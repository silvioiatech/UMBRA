# Creator v1 (CRT4) - Multi-stage Docker Build
# Optimized for production deployment with security and performance

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_ENV=production
ARG CREATOR_VERSION=1.0.0

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create build user
RUN useradd --create-home --shell /bin/bash build
USER build
WORKDIR /home/build

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CREATOR_V1_ENABLED=true
ENV CREATOR_LOG_LEVEL=INFO

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

# Create app user with restricted permissions
RUN groupadd -r creator && useradd -r -g creator creator

# Create application directories
RUN mkdir -p /app /app/logs /app/cache /app/data /app/config \
    && chown -R creator:creator /app

# Copy Python dependencies from builder
COPY --from=builder /home/build/.local /home/creator/.local

# Set up PATH
ENV PATH=/home/creator/.local/bin:$PATH

# Copy application code
COPY --chown=creator:creator . /app/

# Switch to app user
USER creator
WORKDIR /app

# Create default configuration
RUN python -c "
from umbra.modules.creator.utils import DevelopmentTools
DevelopmentTools.generate_test_data('/app/data/test', 10)
print('✅ Default test data created')
"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "
import asyncio
import sys
sys.path.append('/app')
from umbra.modules.creator.cli import CreatorCLI

async def health_check():
    try:
        cli = CreatorCLI()
        success = await cli.load_system()
        if success and cli.creator_system:
            health = await cli.creator_system.health_check()
            status = health.get('overall_health', {}).get('status', 'unknown')
            if status in ['healthy', 'warning']:
                print('✅ Health check passed')
                sys.exit(0)
        print('❌ Health check failed')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Health check error: {e}')
        sys.exit(1)

asyncio.run(health_check())
"

# Expose ports
EXPOSE 8000 8080

# Set default command
ENTRYPOINT ["dumb-init", "--"]
CMD ["python", "-m", "umbra.modules.creator.dashboard", "--host", "0.0.0.0", "--port", "8080"]

# Labels for metadata
LABEL org.opencontainers.image.title="Creator v1 (CRT4)"
LABEL org.opencontainers.image.description="Advanced Content Creation System"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="UMBRA"
LABEL org.opencontainers.image.licenses="MIT"

# Build arguments for CI/CD
ARG BUILD_DATE
ARG VCS_REF
LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.revision=$VCS_REF
