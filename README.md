# 🤖 Autonomous AIOps & GitOps Kubernetes Remediation Engine

A decoupled, self-healing Kubernetes control plane that leverages Generative AI (LLMs) and GitOps principles to autonomously detect, diagnose, and resolve cluster failures in real time.

## 🚀 Executive Summary

Traditional incident response requires manual log analysis and YAML debugging. This project automates that workflow. By combining a real-time Kubernetes event watcher with a Large Language Model and Argo CD, this system:

* **Automates Root Cause Analysis:** Monitors Kubernetes events and detects pod failures in real time, shifting diagnostic time from manual investigation to instant AI analysis.
* **Resolves Common Configuration Outages:** Diagnoses and writes fixes for standard infrastructure errors (e.g., OOMKilled, ImagePullBackOff, PVC errors).
* **Enforces GitOps Workflows:** Integrates directly with Argo CD by proposing YAML fixes via GitHub Pull Requests, reducing recovery time to a simple human approval.

## 🏗️ Decoupled Two-Repo Architecture

This system enforces Separation of Concerns by isolating the application state from the AI control plane:

### 1. The Control Plane Repository (This Repo)
* **The AI Watcher (`ai_watcher.py`):** A Python daemon monitoring the K8s event stream. Upon pod crash, it extracts the error state, queries the LLM for a diagnosis, and generates the corrected YAML manifest.
* **The Chaos Engine (`menu.sh`):** A custom bash testing harness that intentionally mutates the external repository's Infrastructure-as-Code to trigger cluster failures.
* **Security Model:** Enforces a "Human-in-the-Loop" standard. The AI cannot touch the live cluster directly; it uses the GitHub API to open a Pull Request on the target repository and fires a Discord webhook alert.

### 2. The Target Application Repository (External)
* A 3-tier microservice architecture (React Frontend, Node.js Backend, MongoDB) deployed on a local cluster (minikube/kind).
* Managed entirely by **Argo CD**, which acts as the single source of truth. Once the AI's PR is merged here, Argo CD automatically syncs the cluster back to a healthy state.

## 💥 Validated Remediation Scenarios

The engine successfully handles the following complex failure states:

* **Memory Starvation (`OOMKilled`):** The Chaos Engine restricts container memory limits. The AI calculates a healthy baseline and rewrites the YAML with appropriate `requests` (512Mi) and `limits` (1024Mi).
* **Deployment Typos (`ImagePullBackOff`):** Invalid data is injected into container image tags. The AI cross-references the error and restores the valid registry tag.
* **Storage Catastrophe (Missing PVC):** The engine forces the database to request a non-existent Persistent Volume. The AI detects the missing infrastructure, generates a new `PersistentVolumeClaim` from scratch, and appends it to the deployment.

## ⚙️ Prerequisites & Environment

* Local Kubernetes Cluster (minikube / kind / Docker Desktop)
* Argo CD deployed on the cluster
* Python 3.x
* GitHub Personal Access Token (for cross-repo PR automation)
* Discord Webhook URL (for alerting)

## 🛠️ Usage & Demonstration

**1. Start the AI Watcher**
Launch the Python daemon to monitor the namespace:
```bash
python3 ai_watcher.py
