# Website Chatbot

A sophisticated AI-powered chatbot that can scrape any website and answer questions about its content. Features multi-language support including Malayalam and Manglish (Malayalam in English letters).

## Features

- 🌐 **Automatic Website Scraping**: Crawls and indexes website content automatically
- 💬 **Intelligent Q&A**: Uses RAG (Retrieval-Augmented Generation) for accurate answers
- 🎭 **Dynamic Character Generation**: Automatically creates personalized chatbot personalities based on website context
- ✨ **AI Content Enhancement**: NEW! Automatically cleans and structures scraped content for better retrieval (~$0.25-0.50 per website)
- 🌍 **Multi-language Support**: English, Malayalam, and Manglish support
- 🎨 **Visual Scraping**: OCR-based content extraction for image-heavy pages
- 📚 **Context-Aware Responses**: Maintains conversation history
- ⚡ **FastAPI Backend**: Fast, modern web framework with WebSocket support
- 🔄 **Smart Caching**: Reuses scraped data unless forced to re-scrape

## Architecture

```
├── orchestrator.py          # Main orchestrator coordinating all components
├── scraping_agents.py       # Web and visual scraping agents
├── content_enhancer.py      # AI-powered content enhancement (NEW!)
├── data_processor.py        # Document processing and vector store creation
├── chatbot.py              # RAG-based chatbot logic
├── prompt_generator.py      # Dynamic system prompt generation
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

# AI Content Enhancement (NEW!)
ENABLE_AI_ENHANCEMENT=true
ENHANCEMENT_MODEL=gpt-4o-mini
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

2. **Enhancement Phase** ✨ NEW!
   - AI-powered content cleaning (removes navigation noise, fixes typos)
   - Automatic structure addition (sections, context, key information)
   - Business context injection for better retrieval
   - Cost: ~$0.25-0.50 per website (one-time)

3. **Processing Phase**
   - Text chunking with overlap for better context
   - Embedding generation using OpenAI or local models
   - Vector store creation with ChromaDB

4. **Character Generation Phase** 🎭
   - Analyzes website content to identify business type (e.g., clinic, restaurant, hotel)
   - Extracts business name, specialization, and key services
   - Generates personalized system prompt reflecting the business identity
   - Creates context-aware chatbot personality automatically

5. **Chat Phase**
   - Query translation (if needed)
   - Semantic search in vector store
   - LLM-powered answer generation with personalized context
   - Response translation (if needed)

## File Structure

```
Website Chatbot/
├── app.py                          # FastAPI web server
├── main.py                         # CLI interface
├── orchestrator.py                 # Main coordinator
├── chatbot.py                      # Chatbot logic
├── prompt_generator.py             # Dynamic prompt generation 🎭 NEW!
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

## Dynamic Character Generation 🎭

The chatbot now features **automatic personality generation** based on website content! Instead of using a generic "helpful assistant" prompt, the system analyzes the website and creates a personalized chatbot character.

### How It Works

When you initialize a website, the system:
1. **Analyzes** the homepage and initial pages
2. **Identifies** the business type (Ayurveda clinic, restaurant, hotel, etc.)
3. **Extracts** business name, specialization, and key services
4. **Generates** a custom system prompt that reflects the business identity

### Example

For an Ayurvedic center website:

**Before (Generic):**
```
You're a helpful assistant. Answer based on the context below.
```

**After (Personalized):**
```
You are a helpful virtual assistant for SreeSurya Ayurveda Clinic For Women, 
an Ayurvedic wellness center specializing in care for women. Your role is to 
assist visitors by answering their questions accurately and professionally.

Your knowledge is strictly limited to the context provided below. If asked 
about something not covered in the context, politely inform the visitor that 
you don't have that information and suggest they contact the business directly.
```

### Supported Business Types

The system automatically detects:
- 🏥 **Healthcare/Clinics**: Medical services and treatments
- 🌿 **Ayurveda/Wellness**: Holistic health and treatments
- 🍽️ **Restaurants**: Dining and menu services
- 🏨 **Hotels/Resorts**: Accommodation services
- 💪 **Fitness Centers**: Workout and training programs
- 🛍️ **Retail**: Products and shopping
- 🎓 **Education**: Courses and programs
- 💆 **Spas**: Relaxation and beauty services

### Testing

To see the prompt generation in action:
```bash
python test_prompt_generator.py
```

This will show you:
- Detected business information
- Generated system prompt
- Comparison with the generic prompt

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

## AI Content Enhancement ✨ NEW!

The chatbot now includes **AI-powered content enhancement** that automatically cleans and structures scraped content before storing it. This dramatically improves retrieval quality for messy websites.

### How It Works
- Removes navigation noise ("Learn More", "Click Here", etc.)
- Fixes typos and formatting issues
- Adds business context to every page
- Structures content with clear sections
- Extracts key information for better search

### Cost
- **~$0.25-0.50 per website** (50 pages with gpt-4o-mini)
- One-time cost during scraping
- Saves costs by improving retrieval accuracy (fewer retries)

### Configuration
```bash
# Enable/disable in .env
ENABLE_AI_ENHANCEMENT=true
ENHANCEMENT_MODEL=gpt-4o-mini
```

### Testing
```bash
# Run test with sample data
python test_enhancement.py

# Test with real website
python main.py --url "https://example.com" --force-scrape
```

### Documentation
See [AI_ENHANCEMENT_GUIDE.md](AI_ENHANCEMENT_GUIDE.md) for complete documentation.

## Future Improvements

- [ ] Add unit tests
- [ ] Implement proper logging system
- [ ] Add authentication for web interface
- [ ] Support for more document types (PDF, DOCX)
- [x] Streaming responses for better UX ✅
- [x] AI-powered content enhancement ✅
- [ ] Admin dashboard for monitoring
- [ ] Database for conversation history
- [ ] Support for multiple simultaneous users

## License

MIT License - feel free to use this project for your own purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue in the repository.

