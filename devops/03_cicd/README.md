# Module 3: Continuous Integration & Deployment (CI/CD)

In the old days, developers would write code on their machines for months, and then hand a massive zip file to the "Operations" team to deploy on a Friday night. It usually broke everything.

**DevOps changed this with CI/CD.**

Instead of massive, rare deployments, we deploy tiny changes multiple times a day. We achieve this by fully automating the testing and deployment process.

## Continuous Integration (CI)
CI is the practice of automatically building and testing code every time a developer commits changes to version control.
- **The Goal**: Catch bugs immediately.
- **The Process**: 
  1. Developer pushes code to `main`.
  2. The CI Server (like GitHub Actions) wakes up.
  3. It pulls the code into an isolated environment.
  4. It runs Linters (to check code style).
  5. It runs Unit Tests.
  6. It builds the code (e.g., builds a Docker image).
  7. If *any* step fails, the pipeline turns red and blocks the code from being deployed.

## Continuous Delivery / Deployment (CD)
- **Continuous Delivery**: Automatically packaging the built code (the "Artifact") and getting it ready for deployment (e.g., pushing the Docker image to a registry like Docker Hub). A human then clicks a button to deploy it to production.
- **Continuous Deployment**: Taking it one step further—if the tests pass, the code is automatically deployed to production with zero human intervention.

## Artifact Management
An artifact is the final, compiled output of your code. In modern DevOps, this is usually a Docker Image.
Once the CI pipeline builds the Docker image, it pushes it to an **Artifact Registry** (like Docker Hub, AWS ECR, or GitHub Packages). The CD pipeline will later pull this image from the registry to deploy it.

## Semantic Versioning (SemVer)
How do we know what version of the app is running? We use SemVer: `MAJOR.MINOR.PATCH` (e.g., `v1.4.2`).
- **MAJOR**: Breaking changes.
- **MINOR**: New features, backwards compatible.
- **PATCH**: Bug fixes.
In CI/CD, we automatically tag our Docker images with these versions (e.g., `myapp:v1.4.2`).

## GitHub Actions
We will use GitHub Actions for our CI/CD tool. It is built directly into GitHub.
You define workflows using YAML files placed in the `.github/workflows/` directory of your repository.

A Workflow consists of:
- **Events**: What triggers the workflow (e.g., `on: push`).
- **Jobs**: A set of steps that execute on a runner. Jobs run in parallel by default.
- **Runners**: A virtual machine hosted by GitHub that executes your code.
- **Steps**: Individual tasks (run a script, use a pre-built action).

---

## Next Steps
Head over to the `labs/` directory to see a real-world CI pipeline that lints Python code, runs tests, and builds a Docker image!
