import asyncio
from data_processor import DataProcessingAgent
from chatbot import WebsiteChatbot
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chatbot():
    try:
        # Initialize data processor and process data
        processor = DataProcessingAgent()
        vectorstore = await processor.process_data()
        
        # Initialize chatbot
        chatbot = WebsiteChatbot(vectorstore)
        
        # Test questions
        test_questions = [
            "What services do you offer?",
            "What are your treatment options?",
            "Where are you located?",
        ]
        
        # Test conversation
        for question in test_questions:
            print(f"\nHuman: {question}")
            response = await chatbot.get_response(question)
            print(f"Assistant: {response['answer']}")
            print(f"Sources: {response['sources']}")
            
    except Exception as e:
        logger.error(f"Error during chatbot test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_chatbot()) 