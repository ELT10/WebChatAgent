# --------------------------
# 1. Scraping Agent System
# --------------------------
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pytesseract
from PIL import Image
import io

class ScrapingAgents:
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited_urls = set()
        self.documents = []
        
    def static_scraper(self, url):
        """Handle HTML-based scraping"""
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            self.documents.extend(docs)
            print(f"Scraped {url} (static)")
            return True
        except Exception as e:
            print(f"Static scraping failed for {url}: {str(e)}")
            return False
            
    def dynamic_scraper(self, url):
        """Handle JavaScript-rendered pages"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")
                
                # Capture text content
                content = page.content()
                soup = BeautifulSoup(content, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                
                # Capture screenshot for OCR fallback
                screenshot = page.screenshot(full_page=True)
                img = Image.open(io.BytesIO(screenshot))
                ocr_text = pytesseract.image_to_string(img)
                
                combined_content = f"{text}\n[OCR Fallback]:\n{ocr_text}"
                self.documents.append({"page_content": combined_content, "metadata": {"source": url}})
                browser.close()
                print(f"Scraped {url} (dynamic)")
                return True
        except Exception as e:
            print(f"Dynamic scraping failed for {url}: {str(e)}")
            return False

    def crawl_site(self):
        """Agentic crawling system"""
        from urllib.parse import urljoin
        queue = [self.base_url]
        
        while queue:
            current_url = queue.pop(0)
            if current_url in self.visited_urls:
                continue
                
            self.visited_urls.add(current_url)
            
            # Agent decision: Try static first, then dynamic
            if not self.static_scraper(current_url):
                self.dynamic_scraper(current_url)
                
            try:
                response = requests.get(current_url)
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    absolute_url = urljoin(current_url, link["href"])
                    if self.base_url in absolute_url and absolute_url not in self.visited_urls:
                        queue.append(absolute_url)
            except:
                continue

# --------------------------
# 2. RAG Pipeline
# --------------------------
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import tool, AgentExecutor
from langchain.agents import create_tool_calling_agent

class RAGSystem:
    def __init__(self, documents):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        self.vectorstore = Chroma.from_documents(
            self.text_splitter.split_documents(documents),
            embedding=OpenAIEmbeddings(model="text-embedding-3-small")
        )
        self.retriever = self.vectorstore.as_retriever(k=5)
        self.llm = ChatOpenAI(model="gpt-4-turbo")
        
        # Define agentic tools
        self.tools = [
            self.retrieve_information,
            self.handle_fallback
        ]
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, self._get_prompt())
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools)
    
    @tool
    def retrieve_information(query: str) -> str:
        """Retrieve relevant information from knowledge base"""
        docs = self.retriever.get_relevant_documents(query)
        return "\n\n".join([d.page_content for d in docs])
    
    @tool
    def handle_fallback(query: str) -> str:
        """Handle cases when information is not found in knowledge base"""
        return "I couldn't find that information. Would you like me to escalate this to a human?"
    
    def _get_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant for {client}. 
             Use these rules:
             1. Always base answers on retrieved context
             2. Cite sources with URL metadata
             3. If unsure, use fallback mechanism"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
    
    def query(self, question: str) -> str:
        response = self.agent_executor.invoke({
            "input": question,
            "client": "Client Website"
        })
        return response["output"]

# --------------------------
# 3. Chat Interface (FastAPI)
# --------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Initialize systems (would normally be cached)
    scraper = ScrapingAgents("https://client-website.com")
    scraper.crawl_site()
    rag = RAGSystem(scraper.documents)
    
    return {"response": rag.query(request.message)}

# --------------------------
# 4. Run the System
# --------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)