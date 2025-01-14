from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteChatbot:
    def __init__(self, vectorstore):
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Create base retriever with better search parameters
        base_retriever = vectorstore.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance
            search_kwargs={
                "k": 5,  # Retrieve more documents
                "fetch_k": 10,  # Fetch more documents for MMR
                "lambda_mult": 0.7  # Diversity factor
            }
        )
        
        # Improved prompt template
        self.qa_template = """You are a knowledgeable assistant for SreeSurya Ayurveda, a specialized Ayurvedic clinic for women in Coimbatore. 
        Use the following context to answer questions accurately and professionally.
        If you don't find enough information in the context, say so politely.

        Context:
        {context}

        Chat History:
        {chat_history}

        Question: {question}

        Instructions:
        1. Focus on information present in the context
        2. If discussing treatments, mention they are Ayurvedic approaches
        3. Be professional and accurate
        4. If details are missing, acknowledge it
        5. For medical conditions, stick to describing what's in the context

        Assistant:"""
        
        self.qa_prompt = PromptTemplate(
            template=self.qa_template,
            input_variables=["context", "chat_history", "question"]
        )
        
        # Initialize the chain with improved settings
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo-16k"),
            retriever=base_retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt},
            return_source_documents=True,
            verbose=True
        )

    async def get_response(self, query: str) -> Dict:
        """Get a response from the chatbot for the given query."""
        try:
            # Get response
            response = self.chain({"question": query})
            
            # Extract sources and format them - simplified format for frontend
            sources = []
            for doc in response.get("source_documents", []):
                if doc.metadata.get("source"):
                    # Only include the URL string instead of a complex object
                    source = doc.metadata["source"]
                    if source not in sources:
                        sources.append(source)
            
            return {
                "answer": response["answer"],
                "sources": sources  # Now just a list of URLs
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
                "sources": []
            } 