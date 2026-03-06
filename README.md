sequenceDiagram
    actor Dev as Human Engineer
    participant Git as GitHub (Source of Truth)
    participant Argo as Argo CD Controller
    participant K8s as Kubernetes Cluster
    participant Engine as Python AIOps Engine
    participant AI as Groq LLM (Llama 3)

    Note over Dev, AI: Phase 1: The Incident
    Dev->>Git: 1. Push broken deployment.yml
    Argo->>K8s: 2. Sync broken state to cluster

    Note over Dev, AI: Phase 2: Observability & Context
    K8s-->>K8s: 3. Pod crashes (e.g., ErrImagePull)
    K8s->>Engine: 4. Watcher detects Pod failure
    Engine->>K8s: 5. Fetch live container logs & events
    Engine->>Git: 6. Dynamically fetch original YAML

    Note over Dev, AI: Phase 3: AI Diagnostics
    Engine->>AI: 7. Prompt: Logs + Events + Original YAML
    AI-->>Engine: 8. Return raw, corrected YAML fix

    Note over Dev, AI: Phase 4: GitOps Remediation
    Engine->>Git: 9. Create branch & open Pull Request
    Dev->>Git: 10. Review PR and click MERGE
    Argo->>K8s: 11. Sync healthy state (Self-Healed!)
