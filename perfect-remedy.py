import time
import os
from kubernetes import client, config, watch
from groq import Groq
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = 'sorcerer-ares/three-tier-chat-app'

auth = Auth.Token(GITHUB_TOKEN)
ai_client = Groq(api_key=GROQ_API_KEY)
gh_client = Github(auth=auth)
config.load_kube_config()
v1 = client.CoreV1Api()

def get_pod_logs(pod_name, namespace):
    try:
        return v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=50)
    except:
        return "Logs unavailable."

def get_pod_events(pod_name, namespace):
    try:
        events = v1.list_namespaced_event(namespace)
        relevant = [e.message for e in events.items if e.involved_object.name == pod_name]
        return "\n".join(relevant[-5:])
    except:
        return "Events unavailable."

def find_broken_yaml_path(pod_name, repo):
    print(f"🔍 Searching GitHub 'k8s/' folder for '{pod_name}'...")
    base_app_name = pod_name.split('-')[0] 
    try:
        folder_contents = repo.get_contents("k8s") 
        for file in folder_contents:
            if file.type == "file" and file.name.endswith(('.yml', '.yaml')):
                if base_app_name in file.name:
                    print(f"🎯 Target Acquired: '{file.path}'")
                    return file.path
        return None
    except Exception as e:
        print(f"⚠️ API Error: {e}")
        return None

def get_ai_fix(pod_name, namespace, image_name, error_reason, original_yaml):
    print(f"🧠 Diagnosing Pod '{pod_name}'...")
    
    prompt = f"""
    Context: Pod '{pod_name}' is failing in namespace '{namespace}'.
    Error: {error_reason} | Image: {image_name}
    Logs: {get_pod_logs(pod_name, namespace)}
    Events: {get_pod_events(pod_name, namespace)}

    ORIGINAL YAML:
    {original_yaml}

    Task:
    1. Identify the root cause.
    2. Fix the error by modifying the 'ORIGINAL YAML' provided above.
    3. YOU MUST RETURN ONLY THE RAW YAML. NO EXPLANATIONS. NO GREETINGS.
    """

    completion = ai_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,  # Low temperature makes the AI less chatty and more robotic
        messages=[
            # System prompt strictly enforces the persona
            {"role": "system", "content": "You are a raw YAML code generator. You output ONLY valid YAML. You never explain your work or include conversational text."},
            {"role": "user", "content": prompt}
        ]
    )
    
    raw_output = completion.choices[0].message.content.strip()
    
    # --- THE SAFETY NET ---
    # 1. If the AI still uses markdown backticks, extract strictly what is inside them
    if "```yaml" in raw_output.lower():
        raw_output = raw_output.split("```yaml")[1].split("```")[0]
    elif "```yml" in raw_output.lower():
        raw_output = raw_output.split("```yml")[1].split("```")[0]
    elif "```" in raw_output:
        raw_output = raw_output.split("```")[1].split("```")[0]
        
    # 2. If it added conversational text BEFORE the YAML, slice it off entirely
    if "apiVersion:" in raw_output and not raw_output.startswith("apiVersion:"):
        raw_output = "apiVersion:" + raw_output.split("apiVersion:", 1)[1]
        
    return raw_output.strip()
def open_github_pr(corrected_yaml, pod_name, target_yaml_path, repo):
    pr_title = f"[AIOps] Auto-fix for {pod_name}"
    
    for pr in repo.get_pulls(state='open'):
        if pr_title in pr.title:
            print(f"⏭️ Skipping: PR already exists for {pod_name}")
            return

    print(f"🐙 Opening PR to fix {target_yaml_path}...")
    branch_name = f"ai-fix-{int(time.time())}"
    main = repo.get_branch("main")

    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main.commit.sha)
    contents = repo.get_contents(target_yaml_path, ref="main")

    repo.update_file(
        path=target_yaml_path,
        message=f"AIOps: Automated fix for {pod_name}",
        content=corrected_yaml,
        sha=contents.sha,
        branch=branch_name
    )

    pr = repo.create_pull(
        title=pr_title,
        body=f"Automated Platform Fix for {pod_name}. Updated file: `{target_yaml_path}`.",
        head=branch_name,
        base="main"
    )
    print(f"✅ PR Created: {pr.html_url}")

def monitor_cluster():
    print("👀 Watcher: Monitoring 'chat-app' namespace...")
    w = watch.Watch()
    repo = gh_client.get_repo(REPO_NAME)
    
    for event in w.stream(v1.list_pod_for_all_namespaces):
        pod = event['object']
        
        if pod.metadata.namespace != "chat-app":
            continue

        if pod.status.container_statuses:
            for c in pod.status.container_statuses:
                state = c.state.waiting
                if state and hasattr(state, 'reason') and state.reason not in ["Running", "Completed", "ContainerCreating"]:
                    print(f"\n[!] ALERT: '{pod.metadata.name}' is '{state.reason}'")
                    
                    # 1. Find the broken file
                    target_path = find_broken_yaml_path(pod.metadata.name, repo)
                    if not target_path:
                        continue
                        
                    # 2. Fetch the ORIGINAL YAML code
                    original_file = repo.get_contents(target_path, ref="main")
                    original_yaml = original_file.decoded_content.decode("utf-8")
                    
                    # 3. Give the AI the original code to fix
                    fix_yaml = get_ai_fix(pod.metadata.name, pod.metadata.namespace, c.image, state.reason, original_yaml)
                    
                    # 4. Open the PR
                    open_github_pr(fix_yaml, pod.metadata.name, target_path, repo)
                    
                    time.sleep(60)

if __name__ == "__main__":
    monitor_cluster()
