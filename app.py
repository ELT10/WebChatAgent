from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from orchestrator import ChatbotOrchestrator
import json
import logging
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store chatbot instance
chatbot_instance = None

class InitializeRequest(BaseModel):
    website_url: str
    force_scrape: bool = False

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/initialize")
async def initialize_chatbot(request: InitializeRequest):
    global chatbot_instance
    try:
        chatbot_instance = ChatbotOrchestrator(request.website_url)
        await chatbot_instance.initialize(force_scrape=request.force_scrape)
        return {"status": "success", "message": "Chatbot initialized successfully"}
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    if not chatbot_instance:
        await websocket.send_json({
            "error": "Chatbot not initialized"
        })
        await websocket.close()
        return

    try:
        while True:
            message = await websocket.receive_text()
            
            # Get chatbot response
            response = await chatbot_instance.chat(message)
            
            # Send response back to client
            await websocket.send_json(response)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 