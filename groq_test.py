import os
from groq import Groq
from dotenv import load_dotenv
# 1. Initialize the "Brain"
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 2. Simulate a Kubernetes Error Log
error_log = """
Standard Output: Starting app...
Error: 137 (OOMKilled)
Memory usage: 512Mi / 512Mi (100%)
Status: CrashLoopBackOff
"""

# 3. Ask the AI to reason like a Senior DevOps Engineer
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "system", 
            "content": "You are a Senior DevOps AIOps Agent. Analyze logs and suggest a GitOps fix."
        },
        {
            "role": "user", 
            "content": f"The following pod is crashing: {error_log}. What is the cause and what exact YAML change should I make?"
        }
    ]
)

print("--- AI DIAGNOSIS ---")
print(completion.choices[0].message.content)
