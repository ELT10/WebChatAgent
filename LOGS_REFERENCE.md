# Streaming Logs Reference Guide

## Server Terminal Logs

When you run `python app.py` and send a query, you'll see detailed logs showing the streaming flow.

### Expected Log Flow for English Query

```
📨 Received message from client: 'What services do you offer?...'
🎬 Starting to stream response chunks via WebSocket...
🌍 chat_stream() called with query: 'What services do you offer?...'
🌐 Detected language: en
✅ Query is in English, no translation needed
🎬 Using STREAMING response for English query
🔍 Starting streaming response for query: 'What services do you offer?...'
📚 Retrieving relevant documents from vectorstore...
📚 Retrieved 3 documents
🤖 Calling OpenAI Responses API (model: gpt-5-nano)...
📊 Context length: 2500 chars, History length: 0 chars
📤 Chunk #1: 'We' (length: 2)
📦 Yielding chunk #1: type='chunk', content_length=2 chars
📤 Sending chunk #1 to client: type='chunk', preview='We'
📤 Chunk #2: ' offer' (length: 6)
📦 Yielding chunk #2: type='chunk', content_length=6 chars
📤 Sending chunk #2 to client: type='chunk', preview=' offer'
📤 Chunk #3: ' a' (length: 2)
📦 Yielding chunk #3: type='chunk', content_length=2 chars
📤 Sending chunk #3 to client: type='chunk', preview=' a'
... (more chunks)
✅ Streaming completed! Total chunks: 45, Full answer length: 350
📝 First 100 chars: We offer a wide range of services including...
💾 Saving conversation to memory...
🏁 Sending final 'done' message with 2 sources
📦 Yielding chunk #46: type='done', content_length=350 chars
📤 Sending chunk #46 to client: type='done', preview='We offer a wide range of services including...'
✅ Streaming complete! Total chunks yielded: 46
✅ Streaming response completed! Total chunks sent: 46
```

### Expected Log Flow for Malayalam/Manglish Query

```
📨 Received message from client: 'ivide enthokke services undu?...'
🎬 Starting to stream response chunks via WebSocket...
🌍 chat_stream() called with query: 'ivide enthokke services undu?...'
🌐 Detected language: manglish
🔄 Translating manglish to English...
✅ Translated query: What services are available here?
📄 Using NON-STREAMING response for manglish query
✅ Got response, length: 280 chars
🔄 Converting response to Manglish...
✅ Malayalam translation: നമുക്ക് വിവിധ സേവനങ്ങൾ...
✅ Manglish conversion complete: namukku vividha sevanangal...
📦 Yielding single 'done' chunk with 2 sources
📦 Yielding chunk #1: type='done', content_length=280 chars
📤 Sending chunk #1 to client: type='done', preview='namukku vividha sevanangal...'
✅ Streaming complete! Total chunks yielded: 1
✅ Streaming response completed! Total chunks sent: 1
```

## Log Emoji Key

| Emoji | Meaning |
|-------|---------|
| 📨 | Message received from client |
| 🎬 | Starting streaming/processing |
| 🌍 | Language detection/processing |
| 🌐 | Language detected |
| 🔄 | Translation/conversion in progress |
| ✅ | Success/completion |
| 🔍 | Searching/retrieving data |
| 📚 | Vectorstore operations |
| 🤖 | OpenAI API call |
| 📊 | Context/statistics |
| 📤 | Sending/yielding data |
| 📦 | Chunk packaging |
| 💾 | Memory/storage operation |
| 🏁 | Final message |
| ⚠️ | Warning |
| ❌ | Error |
| 🔌 | Connection status |
| 📝 | Preview/sample text |

## Browser Console Logs

Open your browser console (F12 → Console tab) to see frontend logs:

### Expected Console Output (English Query)

```javascript
WebSocket connection established
Received message: {type: "chunk", content: "We"}
Chunk received: We
Created new streaming message box
Received message: {type: "chunk", content: " offer"}
Chunk received:  offer
Received message: {type: "chunk", content: " a"}
Chunk received:  a
... (more chunks)
Received message: {type: "done", content: "We offer a wide range...", sources: Array(2)}
Stream done, content length: 350
Finalizing existing message box with accumulated content length: 350
Finalizing message with content: We offer a wide range of services including...
```

### Expected Console Output (Non-English Query)

```javascript
WebSocket connection established
Received message: {type: "done", content: "namukku vividha sevanangal...", sources: Array(2)}
Stream done, content length: 280
No streaming box, creating new message
```

## Debugging Issues

### Issue: No chunks appearing in logs

**Check for:**
```bash
# Should see this:
🎬 Using STREAMING response for English query

# If you see this instead:
📄 Using NON-STREAMING response
# → Query is not in English
```

### Issue: Chunks generated but not sent

**Look for:**
```bash
# Good:
📤 Chunk #1: 'text...'
📦 Yielding chunk #1
📤 Sending chunk #1 to client

# Bad:
📤 Chunk #1: 'text...'
❌ Error sending chunk #1
```

### Issue: API fallback triggered

**Look for:**
```bash
⚠️ Responses API not available, falling back to standard response
```

**Solution:** Update OpenAI SDK:
```bash
pip install --upgrade openai
```

### Issue: Multiple message boxes

**Browser console should show:**
```javascript
Created new streaming message box  // Should appear ONCE
Chunk received: ...                 // Many times
```

**If you see:**
```javascript
Created new streaming message box  // Multiple times ❌
Created new streaming message box
Created new streaming message box
```

**Solution:** Hard refresh browser (Ctrl+Shift+R)

## Log Levels

The logs use different levels:
- `logger.info()` - Normal operation (shows by default)
- `logger.debug()` - Detailed debugging (add `--log-level debug` to see)
- `logger.warning()` - Warnings (shows by default)
- `logger.error()` - Errors (shows by default)

### Enable Debug Logs

To see even more detailed logs:

```python
# In chatbot.py, orchestrator.py, or app.py, change:
logging.basicConfig(level=logging.INFO)
# To:
logging.basicConfig(level=logging.DEBUG)
```

## Quick Testing

1. **Start server:**
   ```bash
   python app.py
   ```

2. **Watch logs in terminal**

3. **Open browser with console (F12)**

4. **Send English query:**
   ```
   "What services do you offer?"
   ```

5. **Look for:**
   - Terminal: Many "📤 Chunk #X" messages
   - Console: Many "Chunk received" messages
   - UI: Text appearing word-by-word

6. **Send non-English query:**
   ```
   "ivide enthokke services undu?"
   ```

7. **Look for:**
   - Terminal: "📄 Using NON-STREAMING"
   - Console: Single "Stream done" message
   - UI: Complete text appears at once

## Summary Statistics

At the end of each response, you'll see summary stats:

**Server Terminal:**
```
✅ Streaming completed! Total chunks: 45, Full answer length: 350
✅ Streaming complete! Total chunks yielded: 46
✅ Streaming response completed! Total chunks sent: 46
```

These three numbers should all match (or be very close):
- Chunks generated by OpenAI
- Chunks yielded by orchestrator
- Chunks sent via WebSocket

**Note:** The "done" message adds 1 to the count, so total chunks = text chunks + 1

## Filtering Logs

If logs are too verbose, you can filter in terminal:

```bash
# Only show streaming-related logs
python app.py 2>&1 | grep -E "📤|📦|🎬|✅"

# Only show errors
python app.py 2>&1 | grep "❌"

# Only show chunk counts
python app.py 2>&1 | grep "Chunk #"
```

## Log File (Optional)

To save logs to a file:

```bash
python app.py 2>&1 | tee streaming.log
```

Then search the file:
```bash
grep "📤 Chunk" streaming.log | wc -l  # Count chunks
```

## Need Help?

Share these logs when reporting issues:
1. Full server terminal output (from query to completion)
2. Full browser console output
3. Screenshot of the UI issue
4. The exact query you sent

This will help diagnose the problem quickly! 🚀



