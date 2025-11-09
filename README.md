# 🛡️ Aegis - Your AI-Powered Security Guardian

**Aegis** isn't just another security scanner—it's your intelligent code guardian that uses the power of multiple AI models working together to find vulnerabilities that others might miss. Think of it as having a team of expert security researchers reviewing your code, but they work 24/7 and never get tired.

## What Makes Aegis Special?

Most security tools use a single approach. Aegis is different. It runs multiple AI models in parallel—from local Ollama models running on your machine to cloud-powered LLMs—and then uses **consensus algorithms** to merge their findings. This means you get fewer false positives and catch more real issues.

### Key Features

- **🎯 Multi-Model Analysis**: Run scans with Ollama (local), OpenAI, Anthropic, HuggingFace, or classic ML models—all from one interface
- **🤝 Consensus Engine**: Multiple models vote on findings, so you only see vulnerabilities that multiple experts agree on
- **🎨 Beautiful UI**: Clean, modern interface with dark mode support (because we know you code at 2 AM)
- **📊 CWE-Aware**: Automatically focuses on the most relevant vulnerability types for your language
- **📤 Industry-Standard Exports**: Get results in SARIF format for your CI/CD pipelines

## Getting Started

### Prerequisites

You'll need:
- **Python 3.9+** (we recommend 3.10 or newer)
- **uv** package manager (or good old `pip` works too)
- **Ollama** (optional, but recommended for local models)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/canoztas/aegis
   cd aegis
   ```

2. **Install dependencies**
   
   With `uv` (recommended):
   ```bash
   uv sync
   ```
   
   Or with `pip`:
   ```bash
   pip install -e .
   ```

3. **Start the server**
   ```bash
   uv run python app.py
   # or
   python app.py
   ```

4. **Open your browser**
   
   Navigate to `http://localhost:7766` and you're ready to go!

## Your First Scan

1. **Add a Model** (if you haven't already)
   - Click "Models" in the navbar
   - For Ollama: Pull a model like `qwen2.5-coder:7b` or `codellama:7b`
   - For cloud LLMs: Add your API keys for OpenAI, Anthropic, or Azure

2. **Upload Your Code**
   - Create a ZIP file of your source code
   - Drag and drop it on the upload area (or click to browse)
   - Select one or more models from the dropdown
   - Choose a consensus strategy (we recommend "Union" to start)

3. **Review Results**
   - See vulnerable code snippets with context
   - Lines are color-coded by severity
   - Export as SARIF, CSV, or JSON

## Understanding Consensus Strategies

Aegis offers four ways to merge findings from multiple models:

- **Union**: Shows all findings from all models (most comprehensive, might have more false positives)
- **Majority Vote**: Only shows findings that >50% of models agree on (balanced)
- **Weighted Vote**: Same as majority, but you can give more weight to models you trust more
- **Judge Model**: Uses another AI model to intelligently merge findings (most sophisticated)

## Model Management

### Ollama Models (Local)

Ollama lets you run models locally—no API keys needed, and your code never leaves your machine.

**Pulling a model:**
1. Go to Models → Ollama tab
2. Click "Pull Model"
3. Enter a model name like `qwen2.5-coder:7b`
4. Wait for it to download (first time takes a while)
5. The model is automatically registered and ready to use!

**Popular models for security scanning:**
- `qwen2.5-coder:7b` - Great balance of speed and accuracy
- `codellama:7b` - Specialized for code understanding
- `deepseek-coder:6.7b` - Excellent at finding security issues

### Cloud LLMs

If you want the power of GPT-4 or Claude, you can add them:

1. Go to Models → Cloud LLMs tab
2. Click "Add Cloud LLM"
3. Choose your provider (OpenAI, Anthropic, or Azure)
4. Enter your API key and model name
5. That's it!

**Note**: Cloud models require API keys and may incur costs. Check your provider's pricing.

### HuggingFace Models

Want to use open-source models from HuggingFace? Aegis supports that too:

1. Go to Models → HuggingFace tab
2. Enter a model ID (like `bigcode/starcoder2`)
3. Choose the task type
4. Add it to your registry

## Configuration

### Environment Variables

You can customize Aegis with these environment variables:

```bash
# Ollama settings
export OLLAMA_BASE_URL="http://localhost:11434"  # Your Ollama server
export OLLAMA_MODEL="qwen2.5-coder:7b"            # Default model

# Server settings
export HOST="127.0.0.1"                           # Bind address
export PORT="7766"                                # Port number
export FLASK_ENV="development"                    # Enable debug mode
```

### Config File

Edit `config/models.yaml` to set default models, consensus weights, and rate limits.

## How It Works

1. **You upload code** → Aegis extracts source files
2. **Models analyze** → Each selected model scans your code in parallel
3. **Consensus merges** → Findings are combined using your chosen strategy
4. **You review** → See vulnerable code with context, severity, and CWE information

## API Usage

Aegis has a REST API if you want to integrate it into your workflow:

```bash
# List available models
curl http://localhost:7766/api/models

# Create a scan
curl -X POST \
  -F "file=@your-code.zip" \
  -F "models=ollama:qwen2.5-coder:7b,openai:gpt-4o" \
  -F "consensus_strategy=majority_vote" \
  http://localhost:7766/api/scan

# Get results
curl http://localhost:7766/api/scan/{scan_id}

# Export as SARIF
curl http://localhost:7766/api/scan/{scan_id}/sarif -o results.sarif.json
```

## Supported Languages

Aegis can analyze:
- Python, JavaScript, TypeScript
- Java, C, C++, C#
- Go, Rust, Ruby, PHP
- SQL, Shell scripts
- And more (see the full list in the code)

## Tips for Best Results

1. **Use multiple models**: Different models catch different things. Running 2-3 models gives you better coverage.

2. **Start with Union**: When you're new, use "Union" strategy to see everything. As you learn what's noise, switch to "Majority Vote".

3. **Check the code snippets**: The highlighted code shows you exactly what's wrong and why.

4. **Review CWEs**: Each finding includes a CWE (Common Weakness Enumeration) ID. Look it up to understand the vulnerability better.

5. **Use dark mode**: Your eyes will thank you. Click the moon icon in the navbar.

## Troubleshooting

**"No models available"**
- Make sure you've added at least one model in the Models page
- For Ollama, ensure Ollama is running: `ollama serve`

**"Model not responding"**
- Check if Ollama is running: `curl http://localhost:11434/api/tags`
- For cloud models, verify your API keys are correct

**Dark mode not working?**
- Make sure JavaScript is enabled
- Try clearing your browser cache
- Check the browser console for errors

**Scan taking too long?**
- Large codebases take time—this is normal
- Try using fewer models or smaller chunks
- Check your model's performance (local models are often slower than cloud)

## Contributing

Found a bug? Have an idea? We'd love your help!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - use it however you want, just don't blame us if your code still has bugs 😉

## Acknowledgments

Aegis is built with:
- **Flask** - The web framework that makes it all possible
- **Ollama** - For running models locally
- **OpenAI, Anthropic** - For cloud-powered analysis
- **HuggingFace** - For open-source model support
- **Bootstrap** - For making it look good
- **Inter & JetBrains Mono** - For beautiful typography

Inspired by tools like Semgrep, CodeQL, and SonarQube, but with the power of modern AI.

---

**Made with ❤️ for developers who care about security**

Questions? Issues? Open an issue on GitHub or check out the docs.
