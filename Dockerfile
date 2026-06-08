# ── Base image ───────────────────────────────────────────
FROM python:3.11-slim

# slim = minimal Debian with just Python. Much smaller than
# python:3.11 (full) — avoids pulling in unnecessary tools.

# ── Set working directory ────────────────────────────────
WORKDIR /app

# All subsequent commands run relative to /app inside the container.

# ── Copy and install dependencies FIRST ─────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Why copy requirements before the rest of the code?
# Docker caches each layer. If requirements.txt hasn't changed,
# Docker reuses the cached pip install layer — making rebuilds
# after code changes much faster.

# ── Copy the rest of the project ────────────────────────
COPY pipeline/ ./pipeline/
COPY run.py .

# ── Create folders the pipeline writes to ───────────────
RUN mkdir -p data logs analysis

# ── Default command ──────────────────────────────────────
CMD ["python", "run.py"]

# This runs when you do `docker run` with no extra arguments.
# You can override it: docker run myimage python -m pytest
