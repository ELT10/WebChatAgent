import asyncio
import argparse
from orchestrator import ChatbotOrchestrator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Website Chatbot')
    parser.add_argument('--url', type=str, required=True, help='Website URL to scrape')
    parser.add_argument('--force-scrape', action='store_true', help='Force new scraping')
    args = parser.parse_args()
    
    try:
        # Initialize orchestrator
        orchestrator = ChatbotOrchestrator(args.url)
        await orchestrator.initialize(force_scrape=args.force_scrape)
        
        print("\nChatbot initialized! Type 'quit' to exit, 'clear' to clear chat history.")
        
        # Main chat loop
        while True:
            query = input("\nYou: ").strip()
            
            if query.lower() == 'quit':
                break
            elif query.lower() == 'clear':
                orchestrator.clear_chat_history()
                print("Chat history cleared!")
                continue
            elif not query:
                continue
                
            response = await orchestrator.chat(query)
            print("\nAssistant:", response["answer"])
            if response["sources"]:
                print("\nSources:", response["sources"])
                
    except Exception as e:
        logger.error(f"Error in main: {e}")
        
if __name__ == "__main__":
    asyncio.run(main()) 