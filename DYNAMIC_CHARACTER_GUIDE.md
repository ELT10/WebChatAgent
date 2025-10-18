# Dynamic Character Generation Guide 🎭

This guide explains how the automated chatbot personality generation system works and how to customize it for your needs.

## Overview

The Dynamic Character Generation system automatically analyzes website content during initialization and creates a personalized chatbot character that reflects the business identity. This makes the chatbot feel more natural and contextual rather than using a generic "helpful assistant" prompt.

## Architecture

### Components

1. **`prompt_generator.py`**: Core module that analyzes content and generates prompts
2. **`chatbot.py`**: Updated to accept custom system prompts
3. **`chatbot_optimized.py`**: Optimized version with custom prompt support
4. **`orchestrator.py`**: Coordinates prompt generation during initialization

### Flow

```
Website Scraping
      ↓
Scraped Data (JSON)
      ↓
Prompt Generator Analysis:
  - Extract business name
  - Identify business type
  - Find specialization
  - List key services
      ↓
Generate Custom Prompt
      ↓
Initialize Chatbot with Prompt
      ↓
Personalized Conversations
```

## How It Works

### 1. Business Name Extraction

The system extracts the business name from:
- Homepage title
- Removes common suffixes (Home, Homepage, Welcome)
- Cleans location information

**Example:**
```
"SreeSurya Ayurveda Clinic For Women - Ganapathy, Coimbatore"
→ "SreeSurya Ayurveda Clinic For Women"
```

### 2. Business Type Identification

The system uses keyword matching to identify business categories:

| Business Type | Keywords |
|--------------|----------|
| Ayurveda | ayurveda, ayurvedic, wellness, panchakarma, dosha |
| Clinic | clinic, hospital, medical, health, treatment, doctor |
| Restaurant | restaurant, cafe, menu, food, dining, cuisine |
| Hotel | hotel, resort, accommodation, rooms, stay, booking |
| Spa | spa, massage, relaxation, therapy, wellness, beauty |
| Fitness | gym, fitness, workout, training, exercise, yoga |
| Education | school, college, university, course, learning, education |
| Retail | shop, store, buy, purchase, products, sale |

### 3. Specialization Detection

Looks for patterns like:
- "for Women"
- "for Kids"
- "specialized in X"
- "expert in Y"

### 4. Service Extraction

Extracts key services from:
- H2 and H3 headings
- Filters out common navigation items
- Returns up to 10 unique services

### 5. Prompt Generation

Based on business type, generates a contextual prompt:

**Template Structure:**
```
You are a helpful virtual assistant for [BUSINESS_NAME][, a/an BUSINESS_TYPE]
[specializing in SPECIALIZATION]. Your role is to assist visitors by 
answering their questions accurately and professionally.

Your knowledge is strictly limited to the context provided below. If asked 
about something not covered in the context, politely inform the visitor that 
you don't have that information and suggest they contact the business directly.

[TYPE_SPECIFIC_GUIDANCE]. Be professional yet friendly, and always aim to be 
helpful while staying within the boundaries of the provided information.

Context: {context}
History: {chat_history}
Question: {question}
Answer:
```

## Usage Examples

### Basic Usage (Automatic)

The system works automatically when you initialize a chatbot:

```python
from orchestrator import ChatbotOrchestrator

# Initialize with any website
orchestrator = ChatbotOrchestrator("https://example.com")
await orchestrator.initialize()

# The chatbot now has a personalized character!
response = await orchestrator.chat("What services do you offer?")
```

### Manual Usage

You can also generate prompts manually:

```python
from prompt_generator import generate_system_prompt

# Generate prompt from scraped data
prompt = generate_system_prompt('web_scraping_results.json')
print(prompt)
```

### Custom Prompt

If you want to provide your own prompt:

```python
from chatbot import WebsiteChatbot

custom_prompt = """You are Bob, a friendly assistant for Acme Corp...

Context: {context}
History: {chat_history}
Question: {question}
Answer:"""

chatbot = WebsiteChatbot(
    vectorstore,
    system_prompt=custom_prompt
)
```

## Customization

### Adding New Business Types

Edit `prompt_generator.py`:

```python
BUSINESS_TYPE_KEYWORDS = {
    'clinic': [...],
    'restaurant': [...],
    # Add your new type
    'pharmacy': ['pharmacy', 'medicine', 'prescription', 'drugs'],
}
```

Then add the prompt template in `_generate_typed_prompt()`:

```python
elif business_type == 'pharmacy':
    type_context = ", a pharmacy"
    closing = "Provide helpful information about medications and health products."
```

### Adjusting Tone

Modify the prompt templates in `_generate_typed_prompt()` to change tone:

```python
# More formal
intro = f"You are a professional virtual assistant representing {business_name}"

# More casual
intro = f"Hey! I'm your friendly helper for {business_name}"

# Specific character
intro = f"Welcome! I'm Sarah, your guide to {business_name}"
```

### Customizing Analysis

Adjust weights or logic:

```python
# Change how many pages to analyze
for item in scraped_data[:10]:  # Increase from 5 to 10

# Change keyword scoring
score = sum(2 if keyword in combined_text else 0 for keyword in keywords)  # Weight important keywords higher
```

## Testing

### Test Current Prompt

```bash
python test_prompt_generator.py
```

Shows:
- Detected business information
- Generated system prompt
- Comparison with generic prompt

### Unit Testing

Create your own tests:

```python
from prompt_generator import PromptGenerator

# Test business name extraction
data = [{"title": "Acme Corp - Home", "url": "https://acme.com"}]
name = PromptGenerator._extract_business_name(data)
assert name == "Acme Corp"

# Test business type
business_type = PromptGenerator._identify_business_type(data)
print(f"Detected: {business_type}")
```

## Best Practices

### For Website Owners

1. **Clear Business Name**: Use a clear business name in your homepage title
2. **Structured Headings**: Use H2/H3 tags for services
3. **Descriptive Content**: Include business type keywords naturally
4. **Specialization**: Clearly state your niche ("for Women", "for Kids")

### For Developers

1. **Test Different Sites**: Try various business types
2. **Monitor Logs**: Check detection accuracy in logs
3. **Fallback Gracefully**: Generic prompt is used if analysis fails
4. **Cache Results**: Prompt is generated once during initialization
5. **Validate Prompts**: Ensure generated prompts are appropriate

## Troubleshooting

### Generic Prompt Being Used

**Problem**: System uses generic prompt instead of personalized one

**Solutions:**
- Check if `web_scraping_results.json` exists
- Verify scraped data has homepage content
- Look for errors in logs
- Manually run `test_prompt_generator.py`

### Incorrect Business Type

**Problem**: Wrong business type detected

**Solutions:**
- Add more specific keywords to `BUSINESS_TYPE_KEYWORDS`
- Adjust keyword scoring logic
- Analyze more pages (increase limit in `_identify_business_type`)
- Add manual override option

### Poor Prompt Quality

**Problem**: Generated prompt doesn't sound natural

**Solutions:**
- Refine prompt templates in `_generate_typed_prompt()`
- Add more business-specific guidance
- Test with native speakers/industry experts
- A/B test different phrasings

## Examples

### Ayurveda Clinic

**Input:** SreeSurya Ayurveda Clinic For Women

**Generated Prompt:**
```
You are a helpful virtual assistant for SreeSurya Ayurveda Clinic For Women, 
an Ayurvedic wellness center specializing in care for women. Your role is to 
assist visitors by answering their questions accurately and professionally.

Your knowledge is strictly limited to the context provided below. If asked 
about something not covered in the context, politely inform the visitor that 
you don't have that information and suggest they contact the business directly.

Provide helpful information about Ayurvedic treatments, wellness services, and 
holistic health. Be professional yet friendly, and always aim to be helpful 
while staying within the boundaries of the provided information.
```

### Restaurant

**Input:** The Golden Fork - Fine Dining

**Generated Prompt:**
```
You are a helpful virtual assistant for The Golden Fork, a restaurant. Your 
role is to assist visitors by answering their questions accurately and 
professionally.

Your knowledge is strictly limited to the context provided below. If asked 
about something not covered in the context, politely inform the visitor that 
you don't have that information and suggest they contact the business directly.

Provide helpful information about menu items, dining options, and services. 
Be professional yet friendly, and always aim to be helpful while staying 
within the boundaries of the provided information.
```

## Future Enhancements

Potential improvements:

1. **LLM-Based Analysis**: Use GPT to analyze business type instead of keywords
2. **Multi-Language Prompts**: Generate prompts in user's language
3. **Sentiment Analysis**: Adjust tone based on website sentiment
4. **Brand Voice Detection**: Match existing brand communication style
5. **Dynamic Adjustment**: Update prompt based on conversation patterns
6. **A/B Testing**: Test different prompts and measure effectiveness
7. **User Feedback**: Allow users to rate prompt quality
8. **Template Library**: Pre-built templates for common industries

## API Reference

### `PromptGenerator` Class

#### `generate_system_prompt(scraped_data_path, fallback_name)`
Generates a personalized system prompt.

**Parameters:**
- `scraped_data_path` (str): Path to JSON file with scraped data
- `fallback_name` (str): Business name to use if extraction fails

**Returns:**
- `str`: Generated system prompt template

#### `_extract_business_name(scraped_data)`
Extracts business name from scraped data.

**Parameters:**
- `scraped_data` (List[Dict]): List of scraped page data

**Returns:**
- `Optional[str]`: Extracted business name or None

#### `_identify_business_type(scraped_data)`
Identifies business category from content.

**Parameters:**
- `scraped_data` (List[Dict]): List of scraped page data

**Returns:**
- `str`: Business type (e.g., 'ayurveda', 'clinic', 'restaurant')

#### `_extract_specialization(scraped_data, business_type)`
Extracts business specialization.

**Parameters:**
- `scraped_data` (List[Dict]): List of scraped page data
- `business_type` (str): Identified business type

**Returns:**
- `Optional[str]`: Specialization text or None

#### `_extract_services_or_offerings(scraped_data)`
Extracts key services from headings.

**Parameters:**
- `scraped_data` (List[Dict]): List of scraped page data

**Returns:**
- `List[str]`: List of service names

## Contributing

To contribute improvements:

1. Test with various website types
2. Document edge cases
3. Add new business type patterns
4. Improve prompt templates
5. Submit PR with examples

## License

Same as main project license.

## Support

For issues or questions:
- Check logs: `INFO:prompt_generator:...`
- Run test script: `python test_prompt_generator.py`
- Review scraped data: `web_scraping_results.json`
- Create GitHub issue with details

