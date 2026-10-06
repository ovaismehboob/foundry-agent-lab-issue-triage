# Container image for the Issue Triage Assistant hosted agent (Modules 6 and 7).
# Based on the structure of the official Microsoft Foundry hosted-agent Python samples.
# No credentials, tokens, or .env files are copied into this image (see .dockerignore).
# Works with local Docker builds and with remote Azure Container Registry builds (used by azd).
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1. Install pinned dependencies first so this layer is cached between code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the application code, prompts, and synthetic data.
COPY triage_desk ./triage_desk
COPY prompts ./prompts
COPY data ./data
COPY main.py .

# 3. Run as a non-root user.
RUN useradd --create-home --uid 10001 agent && chown -R agent /app
USER agent

# Hosted agents serve traffic on port 8088 (the Foundry gateway routes requests to it).
EXPOSE 8088

CMD ["python", "main.py"]
