# Website Chatbot

A sophisticated AI-powered chatbot that can scrape any website and answer questions about its content. Features multi-language support including Malayalam and Manglish (Malayalam in English letters).

## Features

- 🌐 **Automatic Website Scraping**: Crawls and indexes website content automatically
- 💬 **Intelligent Q&A**: Uses RAG (Retrieval-Augmented Generation) for accurate answers
- 🌍 **Multi-language Support**: English, Malayalam, and Manglish support
- 🎨 **Visual Scraping**: OCR-based content extraction for image-heavy pages
- 📚 **Context-Aware Responses**: Maintains conversation history
- ⚡ **FastAPI Backend**: Fast, modern web framework with WebSocket support
- 🔄 **Smart Caching**: Reuses scraped data unless forced to re-scrape

## Architecture

```
├── orchestrator.py          # Main orchestrator coordinating all components
├── scraping_agents.py       # Web and visual scraping agents
├── data_processor.py        # Document processing and vector store creation
├── chatbot.py              # RAG-based chatbot logic
├── translation_service.py   # Multi-language translation service
├── app.py                  # FastAPI web server
├── main.py                 # CLI interface
└── static/                 # Frontend files
    ├── index.html
    ├── script.js
    └── styles.css
```

## Prerequisites

- Python 3.9+
- OpenAI API Key
- Tesseract OCR (for visual scraping)

### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd "Website Chatbot"
```

2. **Create virtual environment**
```bash
python -m venv venvmain
source venvmain/bin/activate  # On Windows: venvmain\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers**
```bash
playwright install chromium
```

5. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Create a `.env` file with:
```
OPENAI_API_KEY=your_api_key_here
BASE_URL=https://sreesuryaayurveda.com  # Optional: default website
```

## Usage

### Web Application

1. **Start the web server**
```bash
source venvmain/bin/activate && python app.py
```

2. **Open browser** to `http://localhost:8001`

3. **Initialize chatbot** with any website URL

4. **Start chatting!**

### Command Line Interface

```bash
# Basic usage
python main.py --url "https://example.com"

# Force re-scraping
python main.py --url "https://example.com" --force-scrape
```

### CLI Commands

During chat:
- Type your question normally
- Type `clear` to reset conversation history
- Type `quit` to exit

## Configuration

Edit `config.py` or use environment variables:

```python
OPENAI_API_KEY      # Your OpenAI API key (required)
BASE_URL            # Default website to scrape
```

## Multi-language Support

The chatbot automatically detects:
- **English**: Standard queries
- **Malayalam**: മലയാളം script
- **Manglish**: Malayalam in English letters (e.g., "malayalam engane type cheyyam?")

Responses are automatically translated to match your input language.

## How It Works

1. **Scraping Phase**
   - Web scraping using Playwright for JavaScript-rendered pages
   - Visual scraping with OCR for image-based content
   - Content extraction and cleaning

2. **Processing Phase**
   - Text chunking with overlap for better context
   - Embedding generation using OpenAI
   - Vector store creation with ChromaDB

3. **Chat Phase**
   - Query translation (if needed)
   - Semantic search in vector store
   - LLM-powered answer generation
   - Response translation (if needed)

## File Structure

```
Website Chatbot/
├── app.py                          # FastAPI web server
├── main.py                         # CLI interface
├── orchestrator.py                 # Main coordinator
├── chatbot.py                      # Chatbot logic
├── scraping_agents.py              # Scraping implementations
├── data_processor.py               # Data processing pipeline
├── translation_service.py          # Translation service
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (create this)
├── .gitignore                     # Git ignore rules
├── static/                        # Frontend assets
│   ├── index.html
│   ├── script.js
│   └── styles.css
├── data/                          # Generated data directory
│   └── chroma_db/                # Vector store
├── web_scraping_results.json     # Cached web scraping results
└── visual_scraping_results.json  # Cached visual scraping results
```

## Performance Optimization

- **Caching**: Scraped data is cached to avoid re-scraping
- **Rate Limiting**: Built-in delays between page requests
- **Page Limits**: Maximum 100 pages per website
- **MMR Search**: Maximum Marginal Relevance for diverse results

## Troubleshooting

### Common Issues

**Playwright browser not found:**
```bash
playwright install chromium
```

**Tesseract not found:**
- Install Tesseract OCR (see Prerequisites)
- On macOS with Homebrew: `brew install tesseract`

**OpenAI API errors:**
- Check your API key in `.env`
- Verify your OpenAI account has credits

**Memory issues:**
- Reduce chunk_size in `data_processor.py`
- Limit pages scraped (currently 100)

## Development

### Adding New Features

1. **Custom scraping logic**: Modify `scraping_agents.py`
2. **Different embeddings**: Update `data_processor.py`
3. **Custom prompts**: Edit `chatbot.py`
4. **New languages**: Extend `translation_service.py`

### Testing

```bash
# Run the CLI in test mode
python main.py --url "https://example.com" --force-scrape
```

## Security Notes

- Never commit your `.env` file
- Keep your OpenAI API key secure
- Consider adding rate limiting for production
- Validate user input for URLs

## Future Improvements

- [ ] Add unit tests
- [ ] Implement proper logging system
- [ ] Add authentication for web interface
- [ ] Support for more document types (PDF, DOCX)
- [ ] Streaming responses for better UX
- [ ] Admin dashboard for monitoring
- [ ] Database for conversation history
- [ ] Support for multiple simultaneous users

## License

MIT License - feel free to use this project for your own purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue in the repository.

