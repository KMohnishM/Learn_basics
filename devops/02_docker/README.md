# Module 2: Containerization (Docker)

Before containers, if you wanted to deploy an application, you had to run it directly on a server. If the application needed Python 3.9, but the server had Python 3.6, you had a problem. If you ran two applications on the same server, their dependencies might conflict.

Virtual Machines (VMs) solved this by virtualizing the hardware—running an entire Operating System (Guest OS) on top of the host. But VMs are heavy, slow to start, and waste resources.

**Enter Containers.**

## What is a Container?
A container is a standardized, executable package of software that contains everything needed to run an application: code, runtime, system tools, system libraries, and settings. 

Unlike VMs, containers do not virtualize the hardware. They virtualize the *Operating System*. All containers on a host share the same underlying Linux Kernel, but they are isolated from each other using two Linux features:
1. **Namespaces**: Isolates resources (Networking, Process IDs, Mount points). A process in a container thinks it is the only process running.
2. **cgroups (Control Groups)**: Limits resource usage. You can tell a container "You are only allowed to use 512MB of RAM and 1 CPU core."

## Docker Architecture
Docker is the engine that makes building and running containers easy.
- **Docker Daemon (`dockerd`)**: The background service running on the host that manages containers, images, networks, and volumes.
- **Docker Client (`docker`)**: The CLI tool you use to talk to the Daemon (e.g., `docker run`).
- **Docker Registry**: A remote server where container images are stored (like Docker Hub or AWS ECR).

## Images vs. Containers
- **Image**: A read-only template with instructions for creating a Docker container. It's like a class in Object-Oriented Programming.
- **Container**: A runnable instance of an image. It's like an object instantiated from a class.

### Image Layers
Images are built in layers. Each instruction in a `Dockerfile` (like `RUN apt-get install python`) creates a new layer. Layers are cached. If you change a line at the bottom of your `Dockerfile`, Docker only rebuilds that layer and the ones below it, making builds incredibly fast.

## The Dockerfile
A `Dockerfile` is a text document containing all the commands a user could call on the command line to assemble an image.

```dockerfile
# Start from a base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# What command should run when the container starts?
CMD ["python", "app.py"]
```

## Docker Compose
When your architecture grows, you don't just have one container. You have a frontend container, a backend API container, and a database container.
Managing them individually with `docker run` is painful. 
**Docker Compose** is a tool for defining and running multi-container Docker applications using a single YAML file (`docker-compose.yml`).

## Volumes & Networking
- **Volumes**: Containers are ephemeral. If a container dies, all data inside it is lost. To persist data (like a Database), we use Docker Volumes, which map a folder on the host machine to a folder inside the container.
- **Networking**: By default, containers in the same Docker Compose file are put on the same internal network and can talk to each other using their service names as DNS (e.g., `http://db:5432`).

---

## Next Steps
Head over to the `labs/` directory. We will write a `Dockerfile` for a Python API, and use `docker-compose` to run it alongside an Nginx reverse proxy!
