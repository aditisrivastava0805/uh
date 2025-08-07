# Uplift environment with JDK 17
FROM eclipse-temurin:17-jdk

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

# Install Python packages in the virtual environment
# Pin specific versions to ensure compatibility
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    robotframework==6.0.0 \
    google-generativeai \
    google-cloud-aiplatform \
    python-dotenv

# Set working directory
WORKDIR /app

# Set Java environment
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=$JAVA_HOME/bin:$PATH

# Default command
CMD ["/bin/bash"] 