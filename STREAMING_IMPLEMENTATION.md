# Streaming Response Implementation

## Overview

This document describes the implementation of streaming responses using the OpenAI Responses API for English-language queries. This feature significantly improves the perceived responsiveness of the chatbot by displaying text as it's generated, rather than waiting for the complete response.

## Architecture

### Components Modified

1. **`chatbot.py`** - Added streaming method using OpenAI Responses API
2. **`orchestrator.py`** - Added language detection to determine when to use streaming
3. **`app.py`** - Modified WebSocket handler to stream chunks to the frontend
4. **`static/script.js`** - Updated frontend to handle and display streaming text
5. **`static/styles.css`** - Added visual indicator for streaming state

## How It Works

### 1. Backend Streaming (`chatbot.py`)

A new method `get_response_stream()` was added to the `WebsiteChatbot` class:

```python
async def get_response_stream(self, query: str) -> AsyncGenerator[Dict, None]:
    """
    Get a streaming response using OpenAI Responses API.
    Yields chunks as they arrive from the API.
    """
```

**Key Features:**
- Uses `client.responses.create()` with `stream=True`
- Retrieves relevant context from the vectorstore first
- Processes stream events, specifically `response.output_text.delta`
- Yields chunks as `{"type": "chunk", "content": delta, "sources": sources}`
- Yields final message as `{"type": "done", "content": full_text, "sources": sources}`
- Falls back to standard API if Responses API is not available

### 2. Language-Aware Orchestration (`orchestrator.py`)

A new method `chat_stream()` was added:

```python
async def chat_stream(self, query: str) -> AsyncGenerator[Dict, None]:
    """
    Process chat query and stream response.
    Only streams for English responses; non-English responses are returned as complete.
    """
```

**Streaming Logic:**
- Detects input language using the translation service
- **English queries** → Stream responses using `get_response_stream()`
- **Non-English queries** (Malayalam/Manglish) → Get complete response, translate, then return as single chunk

This approach ensures:
- English responses stream naturally for the best UX
- Translation workflows remain intact (can't stream during translation)
- Single, unified interface for both streaming and non-streaming responses

### 3. WebSocket Handler (`app.py`)

Modified the `/chat` WebSocket endpoint:

```python
# Stream chatbot response
async for chunk in chatbot_instance.chat_stream(message):
    await websocket.send_json(chunk)
```

**Key Changes:**
- Replaced single response send with async iteration over chunks
- Each chunk is sent immediately as JSON
- Error handling maintains chunk format

### 4. Frontend Implementation (`static/script.js`)

Updated WebSocket message handler to process streaming chunks:

**New Functions:**
- `createStreamingMessage()` - Creates a message div for streaming content
- `updateStreamingMessage()` - Updates the content as chunks arrive
- `finalizeStreamingMessage()` - Completes the message and adds sources/timestamp

**Message Flow:**
1. Receive `"type": "chunk"` → Accumulate and display text incrementally
2. Receive `"type": "done"` → Finalize message with sources and timestamp
3. Receive `"type": "error"` → Display error message

### 5. Visual Feedback (`static/styles.css`)

Added a blinking cursor effect for streaming messages:

```css
.bot-message.streaming .message-content::after {
    content: '▋';
    color: var(--accent-strong);
    animation: blink 1s infinite;
}
```

This provides clear visual feedback that the response is still being generated.

## API Usage

### OpenAI Responses API

The implementation uses the new Responses API with async support:

```python
# Initialize async client
self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Create streaming response
response_stream = await self.openai_client.responses.create(
    model=self.llm.model_name,
    instructions=instructions,  # Context + chat history + system prompt
    input=query,                # User's question
    stream=True                 # Enable streaming
)

# Process events asynchronously
async for event in response_stream:
    if event.type == "response.output_text.delta":
        yield {"type": "chunk", "content": event.delta}
```

### Event Types Processed

- `response.output_text.delta` - Text chunks as they're generated
- `response.output_text.done` - Final complete text

### Fallback Behavior

If the Responses API is not available (e.g., using an older OpenAI SDK), the system automatically falls back to the standard `get_response()` method and returns the complete response as a single "done" chunk.

## Message Format

All messages sent via WebSocket follow a consistent format:

### Chunk Message
```json
{
    "type": "chunk",
    "content": "partial text...",
    "sources": ["url1", "url2"]
}
```

### Done Message
```json
{
    "type": "done",
    "content": "complete response text",
    "sources": ["url1", "url2"]
}
```

### Error Message
```json
{
    "type": "error",
    "content": "Error description",
    "sources": []
}
```

## Benefits

1. **Improved Perceived Performance** - Users see responses start appearing immediately
2. **Better UX** - Natural conversation flow with text appearing as it's generated
3. **Language-Aware** - Only streams when it makes sense (English responses)
4. **Backward Compatible** - Falls back gracefully if API is unavailable
5. **Visual Feedback** - Blinking cursor indicates streaming is in progress

## Testing

To test the streaming implementation:

1. Start the server: `python app.py`
2. Initialize with a website URL
3. Ask questions in English - you should see text stream in word by word
4. Ask questions in Malayalam/Manglish - you should see complete translated responses

## Dependencies

The implementation requires:
- `openai` Python package with Responses API support
- `fastapi` with WebSocket support
- Modern browser with WebSocket support

## Future Enhancements

Potential improvements:
1. Stream translations if real-time translation APIs become available
2. Add streaming progress indicators
3. Cache streaming responses for common queries
4. Implement token-by-token streaming for even smoother UX
5. Add configuration to enable/disable streaming per user preference

