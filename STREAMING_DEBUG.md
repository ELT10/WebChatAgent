# Streaming Debug Guide

## Fixes Applied

### 1. **Backend Fix** (`chatbot.py`)
- ❌ **Before:** Sending `sources` with every chunk
- ✅ **After:** Only send `sources` with the final `"done"` message

**Chunk format:**
```json
{"type": "chunk", "content": "text delta"}
```

**Done format:**
```json
{"type": "done", "content": "full text", "sources": ["url1", "url2"]}
```

### 2. **Frontend Fix** (`script.js`)
- ✅ Reset streaming state before each new message
- ✅ Only create ONE message box per response
- ✅ Accumulate content from chunks properly
- ✅ Use accumulated content (not response.content) when finalizing
- ✅ Added extensive console logging for debugging
- ✅ Added safety checks to prevent showing sources without content

## How to Test

### Step 1: Clear Browser Cache
```
1. Open DevTools (F12)
2. Right-click refresh button → "Empty Cache and Hard Reload"
   OR
   Press Ctrl+Shift+Delete → Clear cached images and files
```

### Step 2: Start Fresh
```bash
# Kill any existing server
pkill -f "python app.py"

# Start server
python app.py
```

### Step 3: Open Browser Console
```
1. Open DevTools (F12)
2. Go to Console tab
3. Keep it open while testing
```

### Step 4: Test English Query
```
Query: "What services do you offer?"

Expected Console Output:
-----------------------
WebSocket connection established
Received message: {type: "chunk", content: "We"}
Chunk received: We
Created new streaming message box
Received message: {type: "chunk", content: " offer"}
Chunk received:  offer
Received message: {type: "chunk", content: " various"}
Chunk received:  various
...
Received message: {type: "done", content: "We offer various services...", sources: ["url"]}
Stream done, content length: 150
Finalizing existing message box with accumulated content length: 150
Finalizing message with content: We offer various services...
```

### Step 5: Check UI
```
You should see:
1. Typing indicator (...)
2. Empty message box appears
3. Text appears word-by-word with blinking cursor ▋
4. Cursor disappears
5. Sources appear at bottom
6. Timestamp appears
7. ONE message box total (not multiple)
```

## Common Issues & Solutions

### Issue 1: Multiple Message Boxes

**Symptom:** Several boxes appear with same/partial content

**Cause:** 
- Frontend creating new box for each chunk
- Streaming state not being maintained

**Check:**
```javascript
// Should see in console:
"Created new streaming message box"  // Only ONCE per response
```

**Fixed by:** Resetting `currentBotMessageDiv` at start of each message

---

### Issue 2: Only Sources Showing

**Symptom:** Message shows "SOURCES:" but no actual answer

**Cause:** 
- Backend sending sources with chunks (FIXED)
- Content not being accumulated properly
- Using response.content instead of accumulated content

**Check:**
```javascript
// Should see in console:
"Finalizing message with content: [actual text here]"
// NOT:
"Finalizing message with content: EMPTY"
```

**Fixed by:** 
- Removed sources from chunk messages
- Using `currentBotMessageContent` instead of `response.content`

---

### Issue 3: No Streaming (All at Once)

**Symptom:** Response appears complete immediately

**Possible Causes:**

1. **Not English query** (by design)
   ```
   Console: "Using non-streaming response for ml query"
   ```

2. **Cached response**
   ```
   Console: "No streaming box, creating new message"
   ```

3. **API fallback triggered**
   ```
   Server logs: "Responses API not available, falling back"
   ```

4. **Very fast network**
   - Chunks arrive too fast to notice
   - Check server logs for "Streaming completed"

---

### Issue 4: Content Appears Then Disappears

**Symptom:** Text shows during streaming but disappears when done

**Cause:** `finalizeStreamingMessage` overwriting with empty content

**Check:**
```javascript
// Console should show:
"Finalizing message with content: [your accumulated text]"
// NOT:
"Finalizing message with content: "
```

**Fixed by:** Using `currentBotMessageContent || response.content`

---

## Server-Side Debugging

### Check Backend Logs

```bash
python app.py

# You should see:
INFO:orchestrator:Detected language: en
INFO:orchestrator:Using streaming response for English query  
INFO:chatbot:Starting streaming response...
INFO:chatbot:Streaming completed. Full answer length: 150
```

### If you see errors:

#### Error: "AttributeError: 'AsyncOpenAI' object has no attribute 'responses'"

**Solution:** Update OpenAI package
```bash
pip install --upgrade openai
```

#### Error: "Responses API not available"

**Solution:** Fallback is working correctly, but check:
```bash
python -c "from openai import AsyncOpenAI; print(dir(AsyncOpenAI()))" | grep responses
```

## Testing Checklist

- [ ] Browser cache cleared
- [ ] Server restarted
- [ ] Console shows "WebSocket connection established"
- [ ] English query tested
- [ ] Console shows chunks arriving
- [ ] Console shows "Created new streaming message box" ONCE
- [ ] Console shows accumulated content length > 0
- [ ] Only ONE message box appears
- [ ] Text streams word-by-word
- [ ] Blinking cursor (▋) visible during streaming
- [ ] Sources appear AFTER content
- [ ] Timestamp appears at end
- [ ] Input re-enabled after completion

## Quick Fix if Still Broken

If still having issues, you can temporarily disable streaming:

In `/Users/eltonthomas/Developer/WebChatAgent/app.py`, change:

```python
# BEFORE (streaming):
async for chunk in chatbot_instance.chat_stream(message):
    await websocket.send_json(chunk)

# AFTER (non-streaming):
response = await chatbot_instance.chat(message)
await websocket.send_json({
    "type": "done",
    "content": response["answer"],
    "sources": response["sources"]
})
```

This will make everything work as complete responses (no streaming).

## Need More Help?

**Share these logs:**
1. Browser console output (full)
2. Server terminal output (full)
3. Screenshot of the issue
4. The exact query you typed

**Check:**
- Is query in English?
- Is OpenAI API key set?
- Is server running without errors?
- Is WebSocket connected?

## Expected Behavior Summary

### English Query Flow:
```
User types → WebSocket sends → 
Server detects English → 
Retrieves context → 
Streams from OpenAI →
Yields chunks one by one →
Frontend creates ONE box →
Updates box with each chunk →
Finalizes with sources →
Done!
```

### Malayalam Query Flow:
```
User types → WebSocket sends →
Server detects Malayalam →
Gets complete response →
Translates to Malayalam →
Yields ONE "done" message →
Frontend creates message →
Shows complete text →
Done!
```

Both should show ONLY ONE message box per response!



