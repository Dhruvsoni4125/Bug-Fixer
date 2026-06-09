# ========================
# BugRescue Production Dockerfile
# Multi-stage build with Streamlit + CLI support
# ========================

# --- Stage 1: Builder (install deps in a clean layer) ---
FROM python:3.10-slim AS builder

WORKDIR /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt

# --- Stage 2: Runtime ---
FROM python:3.10-slim

LABEL maintainer="BugRescue Team"
LABEL version="2.0.0"
LABEL description="BugRescue — Autonomous AI Code Repair Engine"

# Install language runtimes for polyglot code execution
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        golang-go \
        nodejs \
        npm \
        default-jdk-headless \
        g++ \
        rustc \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r bugrescue && \
    useradd -r -g bugrescue -m -s /bin/bash bugrescue

WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /install/deps /usr/local

# Copy application code
COPY bug_rescue.py .
COPY app.py .
COPY .streamlit/ .streamlit/
COPY requirements.txt .

# Create directories that the app needs (owned by non-root user)
RUN mkdir -p /app/.bugrescue_backups /app/fixed_code /app/projects && \
    chown -R bugrescue:bugrescue /app

# Switch to non-root user
USER bugrescue

# Expose Streamlit port
EXPOSE 8501

# Health check — Streamlit serves a /healthz endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Environment variables (can be overridden at runtime)
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_THEME_PRIMARY_COLOR="#4ec9b0"
ENV STREAMLIT_THEME_BACKGROUND_COLOR="#1e1e1e"
ENV STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR="#252526"
ENV STREAMLIT_THEME_TEXT_COLOR="#d4d4d4"

# Default entrypoint: Streamlit dashboard
# Override with: docker run ... python3 bug_rescue.py ./code
ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
