# ⚙️ DevOps Curriculum

A comprehensive, hands-on curriculum that takes you from Linux automation and version control all the way to production-grade Kubernetes deployments and full observability stacks. Every module is built around **real tools, real infrastructure, and real scenarios** — not just slides.

Each module follows a consistent structure:
- `README.md` — In-depth theory covering all concepts for that week
- `labs/` — Fully runnable code with Docker Compose / Kubernetes manifests
- `exercise/` — A challenge for you to solve independently
- `solution/` — The complete, annotated solution

---

## 🗺️ Curriculum Overview

| Week | Module | Key Tools | Topics |
|------|--------|-----------|--------|
| 1 | [Linux & Automation](./01_automation/) | Bash, Python, Git | Shell scripting, cron, Git workflows, SSH |
| 2 | [Docker](./02_docker/) | Docker, Docker Compose | Containers, Images, Networking, Volumes, Multi-stage builds |
| 3 | [CI/CD](./03_cicd/) | GitHub Actions | Pipelines, automated testing, build & deploy workflows |
| 4 | [Kubernetes](./04_kubernetes/) | Kubernetes, kubectl | Pods, Deployments, Services, ConfigMaps, Ingress |
| 5 | [Terraform](./05_terraform/) | Terraform | Infrastructure as Code, state, modules, cloud provisioning |
| 6 | [Monitoring](./06_monitoring/) | Prometheus, Grafana | Metrics, alerting, dashboards, observability |
| 7 | [Capstone Project](./07_capstone/) | All of the above | End-to-end deployment of a real application |
| — | [Prometheus & Grafana Deep Dive](./prometheus_grafana/) | Prometheus, Grafana | Advanced metrics, custom exporters, alert rules |

---

## 📅 Week-by-Week Breakdown

### Week 1 — [Linux & Automation](./01_automation/)
> *Every DevOps workflow starts with a shell. Master it.*

Before you touch Kubernetes or Terraform, you need to be deeply comfortable in a Linux terminal. This week covers the essential tools: Bash scripting for automation, cron for scheduling, Python for more complex scripts, Git for version control, and SSH for remote server access. You'll write real automation scripts that monitor disk usage, rotate logs, and send alerts.

**Key Concepts:** Linux File System, Bash Scripting (conditionals, loops, functions), Cron Jobs, Git Branching & Merging, SSH Key Auth, Python for Automation.

---

### Week 2 — [Docker](./02_docker/)
> *"Works on my machine" is no longer an excuse.*

Docker containers solve the ancient problem of environment inconsistency. This week you'll understand not just how to run containers, but *how they work* under the hood: Linux namespaces and cgroups provide isolation, Union filesystems make images efficient, and the multi-stage build pattern keeps production images lean and secure. You'll Dockerize a real Python application and orchestrate multiple services with Docker Compose.

**Key Concepts:** Containers vs VMs, Docker Architecture (daemon, client, registry), Images & Layers, Dockerfile best practices, Multi-stage Builds, Volumes & Bind Mounts, Docker Networking, Docker Compose.

---

### Week 3 — [CI/CD](./03_cicd/)
> *Ship code faster and safer with automated pipelines.*

Continuous Integration / Continuous Deployment is the practice of automatically building, testing, and deploying code on every push. We go deep into **GitHub Actions**: writing workflows, understanding triggers, using secrets, running matrix builds across multiple Python versions, and wiring the pipeline all the way from a `git push` to a running container. You'll also cover the conceptual difference between CI, CD (Delivery), and CD (Deployment).

**Key Concepts:** CI vs CD vs CD, YAML pipeline syntax, GitHub Actions (jobs, steps, runners), Triggers (push/PR/schedule), Secrets Management, Docker Build & Push automation, Test automation in pipelines.

---

### Week 4 — [Kubernetes](./04_kubernetes/)
> *Orchestrate containers at scale.*

Docker Compose is great for a single machine. Kubernetes is how the rest of the world runs containers across hundreds of machines in production. This week demystifies Kubernetes: you'll understand the **control plane vs data plane**, write real YAML manifests for Deployments and Services, configure health checks, manage secrets, and expose your app to the internet via an Ingress controller.

**Key Concepts:** Kubernetes Architecture (API Server, etcd, Scheduler, Kubelet), Pods, ReplicaSets, Deployments, Services (ClusterIP/NodePort/LoadBalancer), ConfigMaps & Secrets, Persistent Volumes, Ingress, `kubectl` commands.

---

### Week 5 — [Terraform](./05_terraform/)
> *Manage your entire cloud infrastructure with code.*

Manual click-ops in the AWS console doesn't scale and can't be reviewed or version controlled. Terraform lets you define your entire cloud infrastructure (VPCs, servers, databases, DNS) as code in `.tf` files. We cover the full Terraform workflow: `init → plan → apply → destroy`, understand **state management** (why `terraform.tfstate` is sacred), and learn to write reusable **modules**.

**Key Concepts:** Infrastructure as Code (IaC), HCL Syntax, Terraform Providers, State Files & Remote State, `plan` vs `apply`, Variables & Outputs, Modules, Terraform Workspaces.

---

### Week 6 — [Monitoring & Observability](./06_monitoring/)
> *You can't fix what you can't see.*

Deploying an application is just the beginning. Running it reliably in production requires knowing what it's doing at all times. This week builds a complete **observability stack**: Prometheus scrapes metrics from your applications, Grafana turns those metrics into beautiful dashboards, and Alertmanager fires PagerDuty/Slack notifications when something goes wrong. You'll also learn the conceptual framework of the **Three Pillars of Observability**: Metrics, Logs, and Traces.

**Key Concepts:** Three Pillars of Observability, Prometheus Architecture (Pull model, scrape configs), PromQL queries, Alertmanager, Grafana Dashboards, Log aggregation (EFK Stack), Distributed Tracing concepts.

---

### Week 7 — [Capstone Project](./07_capstone/)
> *Ship a real application from code to production.*

Everything comes together. You'll take a real multi-service application and deploy it end-to-end: Dockerize the services, write Kubernetes manifests, deploy to a local cluster (minikube/kind), wire up a CI/CD pipeline that automatically deploys on merge to `main`, and set up a Prometheus + Grafana monitoring stack for it. This is your portfolio piece.

**Combines:** Docker, Kubernetes, GitHub Actions CI/CD, Terraform, Prometheus, Grafana.

---

### Bonus — [Prometheus & Grafana Deep Dive](./prometheus_grafana/)
> *Go beyond the defaults and build production-grade monitoring.*

An extended module that goes deeper on the monitoring stack. Covers writing custom Prometheus exporters, defining complex alert rules in YAML, building multi-panel Grafana dashboards from scratch, and understanding the difference between **Blackbox monitoring** (does the service respond?) vs **Whitebox monitoring** (what is happening inside the service?).

**Key Concepts:** Custom Exporters, Recording Rules, Alerting Rules, Grafana Templating Variables, SLO-based Alerting.

---

## 🚀 Getting Started

### Prerequisites
- **Docker Desktop** — All lab environments run via Docker Compose or local Kubernetes (minikube)
- **kubectl** — For Kubernetes labs (Week 4+)
- **Terraform** — For IaC labs (Week 5)
- **Python 3.9+** — For automation scripts
- **A GitHub account** — For CI/CD labs (Week 3+)

### Running a Lab
```bash
# Navigate to any module's labs directory
cd devops/02_docker/labs

# Start the Docker environment
docker-compose up -d

# Follow along with the README instructions
```

### Recommended Learning Path
Work through the modules **in order** — each one builds on the previous. The weekly cadence gives you time to:
1. Read the theory thoroughly
2. Run every command in the labs yourself
3. Attempt the exercise before looking at the solution
4. Break things intentionally — that's how real debugging skills are built

---

## 🛠️ Tech Stack

| Category | Tools |
|----------|-------|
| OS & Shell | Linux, Bash |
| Version Control | Git, GitHub |
| Containers | Docker, Docker Compose |
| Orchestration | Kubernetes (minikube/kind), kubectl |
| CI/CD | GitHub Actions |
| Infrastructure as Code | Terraform |
| Monitoring | Prometheus, Grafana, Alertmanager |
| Languages | Bash, Python, YAML, HCL |

---

## 📁 Repository Structure

```
devops/
├── 01_automation/
│   ├── README.md          ← Deep-dive theory
│   ├── labs/              ← Runnable scripts & configs
│   ├── exercise/          ← Your challenge
│   └── solution/          ← Complete solution
├── 02_docker/
│   └── ...
├── 03_cicd/
│   └── ...
├── 04_kubernetes/
│   └── ...
├── 05_terraform/
│   └── ...
├── 06_monitoring/
│   └── ...
├── 07_capstone/
│   └── ...
└── prometheus_grafana/    ← Bonus deep-dive module
    └── ...
```

---

*Build things. Break things. Fix things. That's DevOps. 🚀*
