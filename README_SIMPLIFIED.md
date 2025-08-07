# Python Modernization Tool

A simplified tool focused on modernizing Python scripts in the adaptation pod repository. This tool removes all Java/JDK functionality and focuses exclusively on Python code modernization.

## Features

- **Python-only modernization**: Focuses on Python scripts in the adaptation pod
- **Conservative modernization**: Preserves exact functionality while updating syntax
- **RAG integration**: Uses Ericsson product libraries for context-aware modernization
- **Web interface**: Modern web UI for easy interaction
- **CLI mode**: Command-line interface for automation
- **Backup creation**: Automatically creates backups before making changes

## Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **LLM API Token** configured in `.env` file:
   ```
   LLM_API_TOKEN=your_token_here
   LLM_MODEL=Mistral-12b
   ```

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your `.env` file with your LLM API token

### Usage

#### Web Interface (Recommended)

1. Start the web server:
   ```bash
   python orchestrator_simplified.py
   ```

2. Open your browser to `http://localhost:8000`

3. Configure modernization settings:
   - Target Python version (e.g., 3.9, 3.10)
   - Select libraries for RAG context (optional)
   - Choose adaptation pod modules to process

4. Click "Start Modernization" to begin the process

#### CLI Mode

Run the modernization process in command-line mode:

```bash
python genai_uplifter_simplified.py --cli
```

This will guide you through:
- Target Python version selection
- Repository path configuration
- Library selection for RAG context
- Processing all Python files in the adaptation pod

## What Gets Modernized

The tool focuses on Python modernization opportunities:

### Python 3.6+ Features
- **F-strings**: Convert `%` formatting to f-strings
- **Type hints**: Add type annotations for better code clarity

### Python 3.8+ Features
- **Walrus operator**: Use `:=` for assignment expressions

### Python 3.9+ Features
- **Dict union operators**: Use `|` instead of `.update()`

### General Python 3 Compatibility
- **Print statements**: Ensure parentheses for Python 3
- **Exception handling**: Use `except Exception as e:` syntax
- **Import statements**: Update to Python 3 import syntax

## Adaptation Pod Structure

The tool processes Python files in the `cec-adaptation-pod-main/` directory:

```
cec-adaptation-pod-main/
├── AF_STAT/
│   ├── main.py
│   └── AF_STAT.py
├── AIR_STAT/
│   ├── main.py
│   └── AIR_STAT.py
├── KAFKA_AF/
│   ├── main.py
│   └── KPI_AF.py
├── POD_FILE_COLLECTOR/
│   ├── main.py
│   └── collector.py
├── POD_FILE_SENDER/
│   ├── main.py
│   └── forwarder.py
└── ... (other modules)
```

## Conservative Approach

The tool follows a **conservative modernization approach**:

✅ **DOES**:
- Update deprecated APIs to modern equivalents
- Fix syntax that won't work in target Python version
- Preserve all existing functionality
- Keep all variable names and logic flow
- Maintain existing bugs and issues

❌ **DOES NOT**:
- Fix logical errors or bugs
- Improve algorithms or performance
- Add missing imports or dependencies
- Change variable names or code structure
- Add error handling

## Backup and Safety

- **Automatic backups**: Creates `.backup` files before making changes
- **Process logging**: Detailed logs of all changes made
- **Summary reports**: Complete summary of modernization process
- **Reset functionality**: Ability to reset to original state

## Configuration

### Environment Variables

Create a `.env` file with:

```env
LLM_API_TOKEN=your_ericsson_llm_token
LLM_MODEL=Mistral-12b
```

### Target Python Versions

Supported target versions:
- **Python 3.6**: Basic modernization features
- **Python 3.8**: Adds walrus operator support
- **Python 3.9**: Adds dict union operators
- **Python 3.10+**: Full feature support

## Troubleshooting

### Common Issues

1. **"LLM API Token not configured"**
   - Ensure `.env` file exists with `LLM_API_TOKEN`
   - Check token validity

2. **"No Python files found"**
   - Verify `cec-adaptation-pod-main/` directory exists
   - Check for `.py` files in the repository

3. **"RAG API not available"**
   - Tool will continue with LLM-only modernization
   - RAG context is optional but recommended

4. **"Process already running"**
   - Wait for current process to complete
   - Use reset function to clear state

### Debug Mode

For detailed debugging, check the console output for:
- 🔍 API response structure
- ✅ Successfully extracted responses
- ❌ Error messages and details

## Files

- `genai_uplifter_simplified.py`: Core modernization logic
- `orchestrator_simplified.py`: Web server and process management
- `index.html`: Web interface
- `rag_utils.py`: RAG context integration
- `requirements.txt`: Python dependencies

## Migration from Full Version

If you're migrating from the full JDK uplift tool:

1. **Backup your data**: Save any important configurations
2. **Use simplified files**: Replace with `*_simplified.py` versions
3. **Update imports**: Ensure all imports point to simplified modules
4. **Test thoroughly**: Verify Python modernization works as expected

## Support

For issues or questions:
1. Check the console output for error messages
2. Review the summary logs for detailed information
3. Ensure all prerequisites are met
4. Verify API token and network connectivity 