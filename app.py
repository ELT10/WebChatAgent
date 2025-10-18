from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, validator
import uvicorn
from orchestrator import ChatbotOrchestrator
from utils import validate_url
from config import Config
import json
import logging
import asyncio

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Website Chatbot API",
    description="AI-powered chatbot for website content",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store chatbot instance
chatbot_instance = None

class InitializeRequest(BaseModel):
    website_url: str
    force_scrape: bool = False
    
    @validator('website_url')
    def validate_url_format(cls, v):
        is_valid, error_msg = validate_url(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "chatbot_initialized": chatbot_instance is not None
    }

@app.post("/initialize")
async def initialize_chatbot(request: InitializeRequest):
    """Initialize the chatbot with a website URL."""
    global chatbot_instance
    try:
        logger.info(f"Initializing chatbot for URL: {request.website_url}")
        chatbot_instance = ChatbotOrchestrator(request.website_url)
        await chatbot_instance.initialize(force_scrape=request.force_scrape)
        logger.info("Chatbot initialized successfully")
        return {
            "status": "success", 
            "message": "Hi there! How can I help you?",
            "website_url": request.website_url
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Initialization error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initialize chatbot: {str(e)}")

@app.post("/clear-history")
async def clear_history():
    """Clear the chat history."""
    if not chatbot_instance:
        raise HTTPException(status_code=400, detail="Chatbot not initialized")
    
    try:
        chatbot_instance.clear_chat_history()
        return {"status": "success", "message": "Chat history cleared"}
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat communication."""
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    if not chatbot_instance:
        await websocket.send_json({
            "error": "Chatbot not initialized. Please initialize the chatbot first."
        })
        await websocket.close()
        return

    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            
            if not message or not message.strip():
                logger.warning("⚠️ Empty message received from client")
                await websocket.send_json({
                    "error": "Empty message received"
                })
                continue
            
            logger.info(f"📨 Received message from client: '{message[:100]}...'")
            
            # Stream chatbot response
            chunk_sent_count = 0
            logger.info("🎬 Starting to stream response chunks via WebSocket...")
            async for chunk in chatbot_instance.chat_stream(message):
                try:
                    chunk_sent_count += 1
                    chunk_type = chunk.get('type', 'unknown')
                    content_preview = chunk.get('content', '')[:50] if chunk.get('content') else ''
                    logger.info(f"📤 Sending chunk #{chunk_sent_count} to client: type='{chunk_type}', preview='{content_preview}{'...' if len(chunk.get('content', '')) > 50 else ''}'")
                    await websocket.send_json(chunk)
                    logger.debug(f"✅ Chunk #{chunk_sent_count} sent successfully")
                except Exception as send_error:
                    logger.error(f"❌ Error sending chunk #{chunk_sent_count}: {send_error}")
                    break
            
            logger.info(f"✅ Streaming response completed! Total chunks sent: {chunk_sent_count}")
            
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected by client")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
        try:
            logger.info("📤 Sending error message to client")
            await websocket.send_json({
                "type": "error",
                "content": "An error occurred processing your message",
                "sources": []
            })
        except Exception as close_error:
            logger.error(f"❌ Could not send error message: {close_error}")
        await websocket.close()

if __name__ == "__main__":
    # Validate configuration before starting
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)
    
    logger.info(f"Starting server on {Config.HOST}:{Config.PORT}")
    uvicorn.run(
        "app:app", 
        host=Config.HOST, 
        port=Config.PORT, 
        reload=True,
        log_level="info"
    ) 