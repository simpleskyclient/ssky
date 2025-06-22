FROM python:3.12-slim

# Update system and install required packages
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the entire project source
COPY . /app/ssky-source/

# Remove local virtual environment and poetry config that forces in-project venv
RUN rm -rf /app/ssky-source/.venv /app/ssky-source/poetry.toml

# Install Poetry
RUN pip install --no-cache-dir poetry

# Set working directory to the source
WORKDIR /app/ssky-source

# Configure Poetry to not create virtual environment (we're in a container)
RUN poetry config virtualenvs.create false

# Install dependencies and the local ssky package (including the project itself)
RUN poetry install

# Set working directory back to /app and use the installed package
WORKDIR /app

# Set environment variables (optional, can be overridden at runtime)
ENV PYTHONUNBUFFERED=1

# Health check script
RUN echo '#!/bin/bash\npython3 -c "import ssky; print(\"ssky available\")" && python3 -c "import fastmcp; print(\"FastMCP available\")"' > /app/healthcheck.sh \
    && chmod +x /app/healthcheck.sh

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# Start MCP server using the installed package
ENTRYPOINT ["python3", "-m", "ssky_mcp.server"]

# Metadata
LABEL org.opencontainers.image.title="ssky MCP Server"
LABEL org.opencontainers.image.description="MCP server for ssky Bluesky client built from local source"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="SimpleSkyClient Project" 