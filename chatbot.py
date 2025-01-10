from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from typing import Dict, List, Tuple
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteChatbot:
    def __init__(self, vectorstore):
        # Initialize memory with output_key
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"  # Specify which key to store in memory
        )
        
        # Custom prompt template
        self.qa_template = """You are a helpful AI assistant that answers questions about the website based on the provided context.
        Always be polite and professional. If you're not sure about something, be honest about it.
        
        Context: {context}
        
        Chat History: {chat_history}
        Human: {question}
        Assistant:"""
        
        self.qa_prompt = PromptTemplate(
            template=self.qa_template,
            input_variables=["context", "chat_history", "question"]
        )
        
        # Initialize the chain
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo"),
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt},
            return_source_documents=True,
            verbose=True
        )
        
    async def get_response(self, query: str) -> Dict:
        """
        Get a response from the chatbot for the given query.
        """
        try:
            # Run the chain synchronously since LangChain doesn't support async yet
            response = self.chain({"question": query})
            
            # Extract source URLs
            sources = self._extract_sources(response.get("source_documents", []))
            
            return {
                "answer": response["answer"],
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
                "sources": []
            }
    
    def _extract_sources(self, source_documents: List) -> List[str]:
        """Extract unique source URLs from the source documents."""
        sources = set()
        for doc in source_documents:
            if doc.metadata and "source" in doc.metadata:
                sources.add(doc.metadata["source"])
        return list(sources)
    
    def clear_history(self):
        """Clear the conversation history."""
        self.memory.clear() 