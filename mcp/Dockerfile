FROM python:3.12-slim

# Update system and install required packages
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install ssky and FastMCP
RUN pip install --no-cache-dir ssky fastmcp

# Copy MCP server file
COPY ssky_server.py /app/

# Set environment variables (optional, can be overridden at runtime)
ENV PYTHONUNBUFFERED=1

# Health check script
RUN echo '#!/bin/bash\npython3 -c "import ssky; print(\"ssky available\")" && python3 -c "import fastmcp; print(\"FastMCP available\")"' > /app/healthcheck.sh \
    && chmod +x /app/healthcheck.sh

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# Start MCP server
ENTRYPOINT ["python3", "/app/ssky_server.py"]

# Metadata
LABEL org.opencontainers.image.title="ssky MCP Server"
LABEL org.opencontainers.image.description="MCP server for ssky Bluesky client"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="SimpleSkyClient Project" 