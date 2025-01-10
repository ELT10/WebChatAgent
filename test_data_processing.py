import asyncio
from data_processor import DataProcessingAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_processing():
    processor = DataProcessingAgent()
    try:
        vectorstore = await processor.process_data()
        
        # Test a simple query to verify the vectorstore
        query = "What services are offered?"
        results = vectorstore.similarity_search(query, k=2)
        
        print("\nTest Query Results:")
        print(f"Query: {query}")
        for i, doc in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"Content: {doc.page_content}")
            print(f"Source: {doc.metadata['source']}")
            
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_processing()) 