FROM python:3.11-slim
WORKDIR /app

# Node.js — required to run the official Dynatrace MCP server
# (@dynatrace-oss/dynatrace-mcp-server) that the agent connects to as an MCP client.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @dynatrace-oss/dynatrace-mcp-server \
    && apt-get purge -y curl gnupg && apt-get autoremove -y \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
# Bind the platform-provided $PORT (Cloud Run, Render, etc.); default 8080 locally.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
