# AI Kubernetes Troubleshooting Agent

On-demand Kubernetes troubleshooting: investigate a cluster, reason about failures, and show a diagnosis in the UI.

## Getting Started

Copy environment files, then start the stack:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up --build
```

Access:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health

Local development without Docker:

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

The application now includes kubectl-based evidence collection, OpenRouter-backed reasoning with a local fallback, cluster context selection, and an InsForge-authenticated dashboard. Set `NEXT_PUBLIC_INSFORGE_BASE_URL` and `NEXT_PUBLIC_INSFORGE_ANON_KEY` in `frontend/.env.local`, then run the SQL in `docs/insforge.sql` to enable history storage.

The backend reads the local kubeconfig through `kubectl`. Set `KUBECONFIG_PATH` when the default kubeconfig is not being used. Configure either the InsForge Model Gateway values (`OPENROUTER_API_KEY` and `OPENROUTER_MODEL`) or an OpenAI key (`OPENAI_API_KEY` and `OPENAI_MODEL`). Without either provider, the deterministic Kubernetes diagnosis fallback is used.

Intentional failure manifests for CrashLoopBackOff, ImagePullBackOff, OOMKilled, and Service selector mismatch can be added under `docs/` when testing against a disposable cluster.

---

# High Level Design (HLD)

## Goal

Build an AI-powered Kubernetes troubleshooting platform that can:

- Investigate Kubernetes failures
- Analyze logs, events, and cluster state
- Identify root causes
- Suggest fixes
- Store investigation history
- Be deployed publicly as a real application

---

# High Level Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                     │
│                                                            │
│  Pods | Deployments | Services | Events | Logs            │
│                                                            │
│  This is where failures happen and evidence exists         │
└────────────────────────────────────────────────────────────┘
                              │
                              │ kubectl / Kubernetes API
                              ▼
┌────────────────────────────────────────────────────────────┐
│                  Investigation Layer                      │
│                                                            │
│ Responsibility:                                            │
│ - Connect to Kubernetes cluster                            │
│ - Collect troubleshooting signals                          │
│ - Gather debugging evidence                                │
│                                                            │
│ Components:                                                │
│                                                            │
│  1. Pod Inspector                                          │
│     - Get pod health                                       │
│     - Detect CrashLoopBackOff                              │
│     - Detect Pending/Error states                          │
│                                                            │
│  2. Logs Collector                                         │
│     - Read pod logs                                        │
│     - Capture container errors                             │
│                                                            │
│  3. Events Analyzer                                        │
│     - Read Kubernetes events                               │
│     - Detect scheduling/image failures                     │
│                                                            │
│  4. Deployment Inspector                                   │
│     - Inspect deployment status                            │
│     - Verify rollout health                                │
│                                                            │
│  5. Network Inspector                                      │
│     - Check services                                       │
│     - Validate selectors                                   │
│     - Investigate DNS/networking issues                    │
└────────────────────────────────────────────────────────────┘
                              │
                              │ Structured Investigation Data
                              ▼
┌────────────────────────────────────────────────────────────┐
│                  AI Kubernetes Agent                      │
│                                                            │
│ Responsibility:                                            │
│ - Understand Kubernetes failures                           │
│ - Correlate logs + events + deployment state               │
│ - Identify root cause                                      │
│ - Recommend fixes                                          │
│                                                            │
│ Components:                                                │
│                                                            │
│  1. Prompt Builder                                         │
│     - Convert investigation data into LLM prompt           │
│                                                            │
│  2. LLM Reasoning Layer                                    │
│     - Uses OpenRouter API Key from InsForge                │
│     - Supports models like:                                │
│       - Claude                                              │
│       - GPT                                                 │
│       - DeepSeek                                            │
│                                                            │
│  3. Root Cause Analyzer                                    │
│     - Detect primary issue                                 │
│     - Correlate signals                                    │
│                                                            │
│  4. Fix Recommendation Engine                              │
│     - Suggest kubectl fixes                                │
│     - Recommend YAML updates                               │
│                                                            │
│  5. Confidence Scoring                                     │
│     - Confidence % for diagnosis                           │
└────────────────────────────────────────────────────────────┘
                              │
                              │ Investigation Result
                              ▼
┌────────────────────────────────────────────────────────────┐
│                    InsForge Backend                       │
│                                                            │
│ Responsibility:                                            │
│ - Authentication                                           │
│ - Backend APIs                                             │
│ - Investigation history                                    │
│ - Realtime investigation updates                           │
│                                                            │
│ Components:                                                │
│                                                            │
│  1. Authentication                                         │
│     - User login                                           │
│                                                            │
│  2. API Layer                                              │
│     - Trigger investigations                               │
│     - Return AI analysis                                   │
│                                                            │
│  3. Investigation History                                  │
│     - Store previous incidents                             │
│     - Save root cause reports                              │
│                                                            │
│  4. Realtime Updates                                       │
│     - Live investigation progress                          │
│                                                            │
│ Example:                                                    │
│  ✓ Checking pods                                           │
│  ✓ Reading logs                                            │
│  ✓ Analyzing events                                        │
│  ✓ Finding root cause                                      │
└────────────────────────────────────────────────────────────┘
                              │
                              │ API Response
                              ▼
┌────────────────────────────────────────────────────────────┐
│                     Frontend Dashboard                    │
│                                                            │
│ Responsibility:                                            │
│ - Trigger investigation                                    │
│ - Show realtime progress                                   │
│ - Display root cause                                       │
│ - Show suggested fixes                                     │
│ - Show investigation history                               │
│                                                            │
│ Example UI:                                                 │
│                                                            │
│ Incident: Payment Service Failure                          │
│                                                            │
│ Status: Investigating...                                   │
│                                                            │
│ ✓ Pods Checked                                             │
│ ✓ Events Analyzed                                          │
│ ✓ Logs Processed                                           │
│                                                            │
│ Root Cause: ImagePullBackOff                               │
│                                                            │
│ Suggested Fix:                                             │
│ Update invalid image tag                                   │
└────────────────────────────────────────────────────────────┘
                              │
                              │ Deploy Entire App
                              ▼
┌────────────────────────────────────────────────────────────┐
│                     InsForge Deployment                   │
│                                                            │
│ Responsibility:                                            │
│ - Deploy frontend                                          │
│ - Deploy backend                                           │
│ - Generate public URL                                      │
│                                                            │
│ Output:                                                     │
│                                                            │
│ https://ai-k8s-agent.public-url.app                        │
│                                                            │
│ Enables public access to the troubleshooting platform      │
└────────────────────────────────────────────────────────────┘
```

# End-to-End Workflow

```text
User clicks "Investigate Cluster"
                │
                ▼
Frontend sends API request
                │
                ▼
FastAPI Backend
      (Orchestration Layer)
                │
                ├── Authenticate User (InsForge)
                │
                ▼
Investigation Layer
                │
                ├── Check Pods
                ├── Read Logs
                ├── Analyze Events
                ├── Inspect Deployments
                └── Check Networking
                │
                ▼
AI Kubernetes Agent
                │
                ▼
LLM Reasoning
      (OpenRouter via InsForge Key)
                │
                ▼
Root Cause Analysis
                │
                ▼
Suggested Fix Generated
                │
                ├── Save Investigation History
                │        (InsForge)
                │
                ├── Realtime Progress Updates
                │        (InsForge)
                │
                ▼
Frontend Receives Result
                │
                ▼
User sees Diagnosis
```

# Example Failure Flow

```text
Issue:
Payment service unavailable

Agent Investigation:

✓ Pod Status Checked
✓ Logs Collected
✓ Events Analyzed

Detected Problem:
CrashLoopBackOff

Root Cause:
DATABASE_URL environment variable missing

Confidence:
94%

Suggested Fix:
Update deployment.yaml and add secret reference

Prevention:
Add startup validation checks
```

## Supported Kubernetes Problems

- CrashLoopBackOff
- ImagePullBackOff
- OOMKilled
- Pending Pods
- Resource Exhaustion
- Deployment Rollout Failures
- Service Selector Mismatch
- DNS Resolution Problems
- Readiness/Liveness Probe Failures
- Networking Issues

```
