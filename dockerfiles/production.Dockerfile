# Production environment with JDK 8
FROM openjdk:8-jdk-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    maven \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Robot Framework in the virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir robotframework==6.0.0

# Set working directory
WORKDIR /app

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Default command
CMD ["/bin/bash"] 