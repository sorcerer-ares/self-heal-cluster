graph TD
    subgraph Dev_Zone [Developer Workspace]
        Dev[Developer]
        Review[Developer Reviewing PR]
    end

    subgraph GitOps [GitOps Source of Truth - GitHub]
        Repo[(k8s/deployment.yaml<br/>service.yml)]
        PR[AIOps Auto-fix PR]
    end

    subgraph K8s_Cluster [Kubernetes Cluster - Data Plane]
        Argo[Argo CD Controller]
        subgraph Pods [Running Services]
            BE[Backend Pod<br/>ErrImagePull/BackOff]
            FE[Frontend Running]
            DB[Running Mongo]
        end
    end

    subgraph AI_Engine [Remediation & Logic]
        Python[Python Remediation Engine<br/>Watcher/Executor]
        Groq[Groq Brain<br/>Llama 3]
        GH_API[GitHub Executor API]
    end

    %% Flow Steps
    Dev -->|1. Push Broken YAML| Repo
    Repo -->|2. Sync Broken State| Argo
    Argo -->|2| BE
    BE -.->|3. Failure Detection| Python
    Python -->|4. Fetch Logs/Events| BE
    Repo -->|5. Read Original Manifest| Python
    Python -->|6. Send Prompt: Logs + YAML| Groq
    Groq -->|7. Return Fixed YAML| Python
    Python -->|8. Create Branch & PR| GH_API
    GH_API -->|8| PR
    Review -->|9. Human Review| PR
    PR -->|10. Self-Heal: Manual Merge| Repo
    Repo -->|11. Sync Healthy State| Argo
    Argo -->|11| BE

    %% Styling
    style BE fill:#f96,stroke:#333,stroke-width:2px
    style Groq fill:#d4f,stroke:#333,stroke-width:2px
    style Python fill:#4ea,stroke:#333,stroke-width:2px
    style PR fill:#fff,stroke-dasharray: 5 5
