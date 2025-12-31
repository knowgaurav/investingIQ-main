# InvestingIQ - Data Pipeline Implementation Plan

## Current State Assessment

### Working ✅
- FastAPI backend with endpoints
- Next.js frontend with UI
- PostgreSQL with pgvector extension
- LLM integration (MegaLLM/DeepSeek)
- Basic sentiment analysis
- Basic news/insights generation

### Partially Working ⚠️
- Stock data: yfinance rate-limited, scraping fallback exists
- News scraping: Finviz working, but limited
- RAG service: Code exists but not fully integrated

### Not Working ❌
- Embeddings: Using old OhMyGPT config
- Vector storage: Documents not being embedded/stored
- RAG retrieval: Not connected to chat
- Historical data: Yahoo blocks history scraping

---

## Implementation Plan

### Phase 1: Reliable Data Scraping

#### 1.1 Stock Data Sources (Priority Order)
```
1. Yahoo Finance (scraping) - Real-time quotes
2. MarketWatch - Backup for quotes
3. Generated history from current price (acceptable for demo)
```

#### 1.2 News Sources (Multiple for reliability)
```
1. Finviz - Stock-specific news (working)
2. Google News - General news search
3. Yahoo Finance News - Stock page news section
4. RSS Feeds - Reuters, Bloomberg (free feeds)
```

#### 1.3 Implementation Tasks
- [ ] Fix Yahoo quote scraping (handle different page structures)
- [ ] Add MarketWatch scraper as backup
- [ ] Add Yahoo Finance news scraper
- [ ] Add RSS feed parser for financial news
- [ ] Implement source rotation on failure

---

### Phase 2: Embedding & Vector Storage

#### 2.1 Embedding Strategy
```
Model: text-embedding-3-small (via MegaLLM or local)
Dimensions: 1536
Chunk Size: 500 tokens with 50 token overlap
```

#### 2.2 Documents to Embed
```
1. News articles (title + description)
2. Company info (sector, description, key metrics)
3. Analysis reports (summary + insights)
4. Price context (recent trends, key levels)
```

#### 2.3 Database Schema (Already exists)
```sql
FinancialDocument:
  - id: UUID
  - ticker: String (indexed)
  - doc_type: String (news/company_info/analysis/price)
  - content: Text
  - embedding: Vector(1536)
  - metadata: JSON
  - created_at: DateTime
```

#### 2.4 Implementation Tasks
- [ ] Update RAG service to use MegaLLM embeddings
- [ ] Create document chunking utility
- [ ] Implement batch embedding for efficiency
- [ ] Add embedding storage after each analysis
- [ ] Create background job for re-embedding stale documents

---

### Phase 3: RAG Integration

#### 3.1 Retrieval Strategy
```
1. Query embedding generation
2. Semantic search with pgvector (cosine similarity)
3. Filter by ticker
4. Return top-k (5) most relevant chunks
5. Include in LLM context
```

#### 3.2 Chat Flow
```
User Query → Embed Query → Vector Search → Get Context → LLM + Context → Response
```

#### 3.3 Context Window Management
```
- Max context: 4000 tokens
- Retrieved docs: ~2000 tokens
- Conversation history: ~1500 tokens
- System prompt: ~500 tokens
```

#### 3.4 Implementation Tasks
- [ ] Update chat endpoint to use RAG retrieval
- [ ] Add source citations to responses
- [ ] Implement conversation memory (last 5 messages)
- [ ] Add relevance scoring threshold (skip low-relevance docs)

---

### Phase 4: Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ANALYSIS REQUEST                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA COLLECTION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Stock Data   │  │ News Data    │  │ Company Info │          │
│  │ (Scraping)   │  │ (Multi-src)  │  │ (Scraping)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Sentiment    │  │ Summarize    │  │ Generate     │          │
│  │ Analysis     │  │ News         │  │ Insights     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Analysis     │  │ Embed Docs   │  │ Store in     │          │
│  │ Report (PG)  │  │ (LLM API)    │  │ pgvector     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CHAT/RAG LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ User Query   │──│ Vector       │──│ LLM Response │          │
│  │              │  │ Search       │  │ + Citations  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 5: Implementation Order

#### Step 1: Fix Scraping (30 min)
1. Improve Yahoo quote scraper reliability
2. Add multiple news sources
3. Test with different tickers

#### Step 2: Fix Embeddings (20 min)
1. Update RAG service config for MegaLLM
2. Test embedding generation
3. Verify vector storage

#### Step 3: Embed on Analysis (20 min)
1. After analysis completes, embed:
   - News articles
   - Company info
   - Analysis summary
2. Store in FinancialDocument table

#### Step 4: RAG in Chat (20 min)
1. Update chat endpoint
2. Retrieve relevant context
3. Include sources in response

#### Step 5: Testing & Polish (15 min)
1. End-to-end test
2. Fix any issues
3. Verify frontend displays correctly

---

## File Changes Required

### Backend Files to Modify:
1. `app/services/scraper_service.py` - Improve scraping
2. `app/services/rag_service.py` - Fix embeddings config
3. `app/api/routes/analysis.py` - Add embedding after analysis
4. `app/api/routes/chat.py` - Add RAG retrieval

### New Files (if needed):
1. `app/services/embedding_service.py` - Dedicated embedding logic

---

## Success Criteria

1. ✅ Stock data loads for any ticker (real or generated)
2. ✅ News articles scraped from multiple sources
3. ✅ Sentiment analysis shows real classifications
4. ✅ Documents embedded and stored in pgvector
5. ✅ Chat retrieves relevant context
6. ✅ Responses include source citations

---

## Ready to Implement?

Confirm to proceed with Phase 1 (Scraping improvements) or specify which phase to start with.
