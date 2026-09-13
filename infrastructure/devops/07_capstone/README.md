# Module 7: DevOps Capstone Project

You have made it to the end. You now understand the core lifecycle of modern software engineering:
1. Writing Automation Scripts (Bash/Linux)
2. Packaging Applications (Docker)
3. Automating Tests and Builds (CI/CD)
4. Deploying at Scale (Kubernetes)
5. Provisioning Infrastructure (Terraform)
6. Monitoring the System (Prometheus/Grafana)

Now, it is time to put it all together without any hand-holding.

## The Scenario
You are the sole DevOps Engineer for a new startup. The development team has just handed you a brand new Python API. It is located in the `app/` folder.

They need you to take this raw code and build the entire deployment pipeline for it.

## The Requirements

You must create the following files in this directory to successfully deploy the application:

1. **`Dockerfile`**: Containerize the Python application located in `app/main.py`. It uses Flask, so make sure you install the dependencies in `app/requirements.txt`.
2. **`ci.yml`**: Write a GitHub Actions workflow that runs on push to `main`. It should checkout the code and build the Docker image (you don't need to push it to a registry for this exercise, just build it to prove it compiles).
3. **`deployment.yaml`**: Write a Kubernetes Deployment manifest that requests 2 replicas of your Docker image.
4. **`service.yaml`**: Write a Kubernetes Service manifest that exposes your deployment via a LoadBalancer on port 80.

*Bonus*: If you want to test this locally, you can use Minikube, build the Docker image directly into the Minikube registry, and run `kubectl apply -f .`!

## Completion
There is no new theory here. This is pure execution. 
When you have written all your files, compare them against the reference architectures in the `solution/` folder.

Good luck!
