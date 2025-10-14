# Cost Optimization Guide for Website Chatbot

## 💰 Current Cost Analysis

### Cost Drivers (Most to Least Expensive)
1. **LLM API Calls** - GPT-3.5-turbo: $0.50/$1.50 per 1M tokens (input/output)
2. **Embedding API Calls** - text-embedding-3-small: $0.02 per 1M tokens
3. **Chat Memory** - Grows linearly with conversation length
4. **Retrieval** - More documents = more tokens sent to LLM

### Example Cost Breakdown (per conversation)
```
Initial Scraping (one-time):
- 100 pages × 2000 tokens each = 200,000 tokens
- Embedding cost: 200k × $0.02 / 1M = $0.004 (one-time)

Per Chat Turn:
- System prompt: ~300 tokens
- Retrieved context: 5 docs × 200 tokens = 1000 tokens
- Chat history: 10 turns × 100 tokens = 1000 tokens
- User query: ~50 tokens
- Total input: ~2,350 tokens = $0.001175
- Response: ~200 tokens = $0.0003
- Total per turn: ~$0.0015

After 100 turns: $0.15
After 1000 turns: $1.50
```

## 🎯 Optimization Strategies

### 1. **Conversation Memory Optimization** (Biggest Impact)

#### Problem
Current implementation uses `ConversationBufferMemory` which keeps ALL messages:
```python
# Current: Unlimited memory
self.memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)
```

After 50 turns, you're sending 5000+ tokens of history with EVERY query!

#### Solution A: Sliding Window Memory (Simple & Effective)
```python
from langchain.memory import ConversationBufferWindowMemory

# Keep only last N exchanges
self.memory = ConversationBufferWindowMemory(
    k=5,  # Keep last 5 exchanges (10 messages)
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)
```
**Cost Reduction**: 70-90% for long conversations
**Quality Impact**: Minimal (most queries don't need full history)

#### Solution B: Summary Memory (Better Quality)
```python
from langchain.memory import ConversationSummaryBufferMemory

# Summarize old messages, keep recent ones
self.memory = ConversationSummaryBufferMemory(
    llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo"),
    max_token_limit=1000,  # Summarize when history exceeds this
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)
```
**Cost Reduction**: 50-70%
**Quality Impact**: Better than window (keeps important context)

#### Solution C: Hybrid Approach (Best of Both)
```python
from langchain.memory import ConversationTokenBufferMemory

# Token-aware memory with automatic pruning
self.memory = ConversationTokenBufferMemory(
    llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo"),
    max_token_limit=2000,  # Hard limit on history tokens
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)
```
**Cost Reduction**: 60-80%
**Quality Impact**: Minimal (smart token management)

### 2. **Use Local Embeddings** (Eliminate Embedding Costs)

#### Problem
Current: OpenAI embeddings cost $0.02 per 1M tokens
For large sites (1M tokens), that's $0.02 per scrape

#### Solution: Use Free Local Embeddings
```python
# Option 1: HuggingFace embeddings (FREE)
from langchain_community.embeddings import HuggingFaceEmbeddings

self.embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",  # Fast & good quality
    model_kwargs={'device': 'cpu'}
)
```

**Alternatives:**
- `all-MiniLM-L6-v2`: Fast, good quality (default choice)
- `all-mpnet-base-v2`: Better quality, slower
- `multi-qa-MiniLM-L6-cos-v1`: Optimized for Q&A

**Cost Reduction**: 100% of embedding costs (FREE!)
**Quality Impact**: ~5% worse than OpenAI (usually acceptable)
**One-time setup**: ~100MB model download

### 3. **Cheaper LLM Models** (40-70% Cost Reduction)

#### Current Cost Comparison
```
gpt-4-turbo:        $10.00 / $30.00 per 1M tokens
gpt-3.5-turbo-16k:   $3.00 /  $4.00 per 1M tokens  ← You're here
gpt-3.5-turbo:       $0.50 /  $1.50 per 1M tokens  ← Use this
```

#### Simple Change
```python
# In chatbot.py, change this:
llm=ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo-16k")

# To this:
llm=ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
```

**Cost Reduction**: 83% per token!
**Quality Impact**: Minimal for most queries
**Trade-off**: Smaller context window (16K → 4K)

#### Smart Model Router (Best Approach)
```python
def get_llm_for_query(self, query: str, context_size: int):
    """Choose model based on complexity."""
    # Simple queries → cheap model
    if len(query.split()) < 15 and context_size < 3000:
        return ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
    # Complex queries → better model
    else:
        return ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo-16k")
```

### 4. **Response Caching** (50-90% Cost Reduction for Common Queries)

#### Problem
Same questions asked multiple times = wasted API calls

#### Solution: Semantic Caching
```python
import hashlib
from typing import Dict, Optional

class ResponseCache:
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.max_size = 1000
        
    def get_cache_key(self, query: str, context: str) -> str:
        """Create cache key from query + context."""
        combined = f"{query.lower().strip()}:{context[:500]}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, query: str, context: str) -> Optional[Dict]:
        """Get cached response if exists."""
        key = self.get_cache_key(query, context)
        return self.cache.get(key)
    
    def set(self, query: str, context: str, response: Dict):
        """Cache response."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            self.cache.pop(next(iter(self.cache)))
        
        key = self.get_cache_key(query, context)
        self.cache[key] = response
```

**Cost Reduction**: 50-90% for repeated queries
**Implementation**: Add to chatbot.py

### 5. **Smarter Retrieval** (Reduce Context Size)

#### Current Issue
Retrieving 5 documents × 1000 tokens = 5000 tokens per query

#### Solution A: Contextual Compression
```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# Compress retrieved docs to only relevant parts
compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)
```

**Cost Reduction**: 30-50% of retrieval context
**Quality Impact**: Often BETTER (removes noise)

#### Solution B: MMR + Lower K
```python
# Current: k=5, fetch_k=10
base_retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,  # Reduce from 5 to 3
        "fetch_k": 6,  # Reduce from 10 to 6
        "lambda_mult": 0.7
    }
)
```

**Cost Reduction**: 40% (5 docs → 3 docs)
**Quality Impact**: Minimal if docs are high quality

#### Solution C: Reranking (Best Quality/Cost Ratio)
```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import CohereRerank

# Get more docs, rerank, keep best ones
compressor = CohereRerank(top_n=3)  # Free tier available
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 10})
)
```

**Cost Reduction**: Better quality with fewer docs
**Quality Impact**: IMPROVED

### 6. **Optimize Chunking** (One-Time, Long-Term Impact)

#### Current Settings
```python
chunk_size=1000
chunk_overlap=200
```

#### Optimized Settings
```python
# Smaller chunks = more precise retrieval
chunk_size=500  # Smaller chunks
chunk_overlap=50  # Less overlap
```

**Benefits:**
- Retrieve fewer tokens per document
- More precise matching
- Less noise in context

**Trade-off:**
- More chunks to store
- Slightly more complex retrieval

### 7. **Prompt Optimization** (10-20% Cost Reduction)

#### Current Prompt (Long - ~300 tokens)
```python
qa_template = """You are a knowledgeable assistant for SreeSurya Ayurveda, 
a specialized Ayurvedic clinic for women in Coimbatore. 
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
