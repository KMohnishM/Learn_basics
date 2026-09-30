# Module 2: Dockerfile Best Practices Cheatsheet

## Core Instructions Comparison
| Instruction | Purpose | Key Behavior | Best Practice |
|-------------|---------|--------------|---------------|
| FROM | Base image | Starts build stage | Use specific tags, prefer alpine/distroless |
| RUN | Execute | Creates new layer | Chain commands with `&&` to reduce layers |
| COPY | Add files | Preserves metadata | Prefer over ADD. Order by least frequently changed |
| ADD | Add files | Auto-extracts tar, URLs | Avoid unless tar extraction is specifically needed |
| CMD | Default run | Overridable at runtime | Use for default arguments or the main executable |
| ENTRYPOINT| Main run | Harder to override | Use for the main executable of the container |
| WORKDIR | Setup dir | Creates if missing | Always use absolute paths. Avoid `cd` in RUN |
| USER | Privilege | Drops root | Always run as non-root user for security |
| EXPOSE | Document | No publishing done | Use for documenting ports the container listens on |
| ARG | Build var | Not in final image | Use for build-time configuration |
| ENV | Run var | Persists in image | Use for runtime configuration |
| HEALTHCHECK| Probing | Verifies app health| Use simple commands like curl or wget to test app |
| VOLUME | Storage | Defines mount point| Use for directories that require write access in read-only containers |

## Multi-Stage Build Templates

### Go Application
```dockerfile
FROM golang:1.20-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /bin/app ./cmd/server

FROM scratch
COPY --from=builder /bin/app /app
ENTRYPOINT ["/app"]
```

### Node.js Application
```dockerfile
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS runtime
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
USER node
CMD ["node", "src/index.js"]
```

### Python Application
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
USER 1000
CMD ["python", "main.py"]
```

## BuildKit Mounts Syntax

```dockerfile
# Cache Mounts (Persists downloaded packages across builds)
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y gcc

# Secret Mounts (Provides secure access to secrets without layer leaking)
RUN --mount=type=secret,id=aws,target=/root/.aws/credentials \
    aws s3 cp s3://bucket/config.json .

# SSH Mounts (Allows cloning private repositories using host SSH keys)
RUN --mount=type=ssh \
    git clone git@github.com:private/repo.git
```

## Security Hardening Checklist

- [ ] Use minimal base images (Alpine, Distroless, Scratch)
- [ ] Pin base image versions with SHA256 digests
- [ ] Run containers as non-root user (USER instruction)
- [ ] Make root filesystem read-only where possible
- [ ] Do not store secrets in environment variables or hardcoded in Dockerfile
- [ ] Use BuildKit secret mounts for build-time secrets
- [ ] Scan images using Trivy or Hadolint before deployment
- [ ] Remove unnecessary package managers and shells (curl, wget, bash)
- [ ] Add HEALTHCHECK instruction
- [ ] Use COPY instead of ADD to avoid unexpected remote fetches

## BuildKit CLI Commands
```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build with secret
docker build --secret id=mysecret,src=secret.txt -t app .

# Build with SSH agent forwarding
docker build --ssh default -t app .

# Analyze layers
docker history app:latest
```
