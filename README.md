# Java JDK Uplift Simulation Environment

This prototype simulates the process of automatically uplifting Java code from older JDK versions (JDK 8) to newer versions (JDK 17) using Docker Compose for environment isolation, Python for orchestration, and Robot Framework for testing validation.

## Architecture Overview

The simulation environment consists of:

- **Production Environment** (JDK 8): Simulates the existing production environment
- **Uplift Environment** (JDK 17): Target environment for modernized code
- **Static Analysis**: Uses Modernizer Maven plugin to identify outdated APIs
- **Generative AI**: Uses Ericsson's LLM API to automatically modernize code
- **Testing Framework**: Robot Framework validates that uplifted code maintains functionality
- **Web Interface**: Single-page application for monitoring and controlling the process
- **ESSVT Integration**: Optional cloud-based test validation through Ericsson's ESSVT platform

## Directory Structure

```
/jdk_uplift/
├── docker-compose.yml          # Docker Compose configuration
├── orchestrator.py             # Main workflow orchestration with FastAPI backend
├── genai_uplifter.py           # Static analysis and AI-powered code modernization
├── index.html                  # Web interface
├── dockerfiles/
│   ├── production.Dockerfile   # JDK 8 production environment
│   └── uplift.Dockerfile      # JDK 17 uplift environment
└── repositories/
    ├── ESSVT/                 # Test repository
    │   ├── tests.robot        # Robot Framework test suite
    │   └── src/com/example/TestUtil.java
    └── source-code/           # Source code repository
        └── src/com/example/server/Main.java
```

## Prerequisites

1. **Docker and Docker Compose** installed
2. **Ericsson LLM API** access token
3. **Maven** (installed in Docker containers)
4. **Python 3.8+** with dependencies from requirements.txt
5. **ESSVT Account** (optional, for cloud-based validation)

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the project root with your API credentials:

```bash
# LLM API Configuration
LLM_API_TOKEN=your-api-token-here
LLM_MODEL=Mistral-12b  # Optional, defaults to Mistral-12b

# ESSVT Configuration (Optional)
ESSVT_ENABLED=false           # Set to 'true' to enable ESSVT validation
ESSVT_USERNAME=your_username  # Your ESSVT username
ESSVT_PASSWORD=your_password  # Your ESSVT password
ESSVT_PROJECT_ID=your_project_id  # ESSVT project ID for test execution
ESSVT_CLIENT_ID=essvt-public  # OAuth client ID (default: essvt-public)
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Build Docker Images

```bash
docker-compose build
```

### 4. Verify Setup

Test that both environments are working:

```bash
# Test production environment (JDK 8)
docker-compose run --rm production_env java -version

# Test uplift environment (JDK 17)
docker-compose run --rm uplift_env java -version
```

## Running the Simulation

### Web Interface (Recommended)

```bash
python orchestrator.py
```

Then open your browser to http://localhost:8000

### Command Line

```bash
python orchestrator.py --cli
```

## Workflow Steps

The orchestrator performs the following steps:

1. **🔷 Baseline Testing**: Run Robot Framework tests in production environment (JDK 8)
2. **🔧 ESSVT Uplift**: Modernize test code using static analysis + AI
3. **🧪 ESSVT Validation**: Test uplifted test code against original source code
4. **🌐 ESSVT Cloud Validation** (if enabled): Upload and validate tests on ESSVT platform
5. **📊 Comparison**: Compare test results to ensure functionality is preserved
6. **🔧 Source Code Uplift**: Modernize application source code
7. **🧪 Final Testing**: Run uplifted tests against uplifted source code
8. **🌐 Final ESSVT Validation** (if enabled): Final cloud-based validation with complete solution
9. **📋 Final Report**: Compare all results and report success/failure

## Key Components

### Static Analysis (Modernizer)
- Identifies deprecated APIs and outdated patterns
- Generates Maven-based reports of modernization opportunities
- Focuses on JDK version-specific improvements

### Generative AI (Ericsson LLM API)
- Analyzes static analysis findings
- Generates modernized Java code
- Preserves functionality while updating to modern patterns
- Provides detailed change summaries

### Testing Validation (Robot Framework)
- Compiles and runs Java code in both environments
- Validates that outputs remain consistent after modernization
- Provides detailed test reports and comparisons

### ESSVT Integration
- **Cloud-based Validation**: Upload and execute tests on Ericsson's ESSVT platform
- **Automatic Project Management**: Handle order creation and execution management
- **Real-time Monitoring**: Track cloud execution progress and results
- **Conflict Resolution**: Intelligent handling of concurrent executions
- **Authentication**: OAuth2 token management for secure API access

### Web Interface
- Real-time monitoring of the uplift process
- Visual status indicators for each stage
- Access to logs and test reports
- Control buttons for starting, canceling, and resetting
- ESSVT validation progress tracking (when enabled)

## Backend API Endpoints

The orchestrator.py now includes a FastAPI backend with these endpoints:

- `GET /`: Serves the web interface
- `POST /start`: Starts the uplift process
- `POST /cancel`: Cancels a running process
- `POST /reset`: Resets the environment
- `GET /stream`: Server-Sent Events stream for real-time updates

## Code Examples

The simulation includes placeholder Java files with common legacy patterns:

- **Vector/Hashtable** → **ArrayList/HashMap**
- **StringBuffer** → **StringBuilder**
- **Legacy Date** → **Modern Time APIs**
- **Old iteration patterns** → **Streams (where appropriate)**

## ESSVT Cloud Validation

When enabled (`ESSVT_ENABLED=true`), the tool provides additional validation through Ericsson's ESSVT cloud platform:

### Features
- **Dual Validation**: Local Docker + Cloud ESSVT validation for enhanced confidence
- **Automatic Upload**: Creates and uploads test packages to ESSVT projects
- **Order Management**: Creates test orders and executions automatically
- **Progress Monitoring**: Real-time tracking of cloud execution status
- **Result Integration**: Retrieves and displays ESSVT test results in the web interface

### ESSVT Workflow
1. **Authentication**: Obtain OAuth2 token from ESSVT
2. **Package Creation**: Create ZIP package of test code
3. **Upload**: Upload package to configured ESSVT project
4. **Order Creation**: Create test order in ESSVT
5. **Execution**: Start test execution with auto-start enabled
6. **Monitoring**: Track progress until completion
7. **Results**: Collect and display test results

### Configuration
```bash
# Enable ESSVT validation
ESSVT_ENABLED=true
ESSVT_USERNAME=your_username
ESSVT_PASSWORD=your_password
ESSVT_PROJECT_ID=846ef0b5453648af964e2020b6deaa74
```

## Troubleshooting

### Common Issues

1. **LLM API Authentication Errors**
   - Ensure `LLM_API_TOKEN` is correctly set in your .env file
   - Verify API token has not expired
   - Check network connectivity to the API endpoint

2. **ESSVT Integration Issues**
   - **Upload Conflicts**: Tool automatically waits for running executions to complete
   - **Authentication Failures**: Verify ESSVT credentials in .env file
   - **Project Access**: Ensure you have access to the specified ESSVT project ID

3. **Docker Build Issues**
   - Check Docker daemon is running
   - Ensure sufficient disk space for images

4. **Maven/Compilation Errors**
   - Check Java file syntax in repositories
   - Verify package structure matches directory structure

5. **Web Interface Issues**
   - Check that all required Python packages are installed
   - Ensure output directories exist (they should be created automatically)
   - Check browser console for JavaScript errors

### Logs and Output

- Test results: `baseline_output/`, `essvt_output/`, `final_output/`
- Uplift summaries: `*_uplift_summary.txt` files alongside modified Java files
- Docker logs: `docker-compose logs <service_name>`
- ESSVT logs: Visible in web interface when ESSVT validation is enabled

## Extension Points

This prototype can be extended with:

- Support for additional JDK versions
- Integration with CI/CD pipelines
- Custom static analysis rules
- Different AI models/providers
- Enhanced test validation strategies
- Integration with existing codebases
- Advanced web interface features
- Additional cloud testing platforms

## Educational Concepts

This tool demonstrates several key DevOps and software modernization concepts:

### 1. **Environment Isolation**
- **Concept**: Using containers to replicate different runtime environments
- **Why**: Ensures consistency between development, testing, and production
- **Implementation**: Docker Compose services with different JDK versions

### 2. **Static Analysis Integration**
- **Concept**: Automated code analysis to identify improvement opportunities
- **Why**: Provides systematic, repeatable identification of technical debt
- **Implementation**: Maven Modernizer plugin for Java-specific analysis

### 3. **AI-Assisted Code Transformation**
- **Concept**: Using machine learning to automate code modernization
- **Why**: Scales code updates beyond manual capability while maintaining context
- **Implementation**: Ericsson LLM API integration with structured prompts

### 4. **Validation-Driven Modernization**
- **Concept**: Ensuring functionality preservation through automated testing
- **Why**: Reduces risk of introducing bugs during modernization
- **Implementation**: Robot Framework test comparison between versions

### 5. **Orchestrated Workflows**
- **Concept**: Coordinating multiple tools and environments in sequence
- **Why**: Automates complex multi-step processes with proper error handling
- **Implementation**: Python orchestrator managing Docker containers and external APIs

### 6. **Real-time Process Monitoring**
- **Concept**: Providing visibility into long-running automated processes
- **Why**: Improves user experience and enables intervention when needed
- **Implementation**: FastAPI backend with Server-Sent Events for live updates

### 7. **Hybrid Validation Strategies**
- **Concept**: Combining local and cloud-based testing for comprehensive validation
- **Why**: Increases confidence in modernization results through multiple validation layers
- **Implementation**: Docker-based local testing + ESSVT cloud platform integration