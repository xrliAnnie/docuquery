# **Design Document: DocuQuery**

**Document Q\&A Prototype with OpenAI \+ Chroma (Docker)**  
*Version 0.1 \- Draft for Team Review*

---

## **1\. Overview**

### **Objective**

Build a lightweight, locally deployable prototype that allows users to upload documents and ask natural-language questions, with answers grounded in the document content.

### **Out of Scope (For Now)**

* User authentication, billing, or multi-tenancy.  
* Scalability beyond 1k documents or 10k queries/day.  
* Advanced features like versioning or collaborative editing.

---

## **2\. Architecture**

### **Flow Diagram**

1. User (Browser)    
2. │    
3. ├─▶ \[Streamlit UI\]    
4. │    │    
5. │    ├─▶ Document Upload → FastAPI \`/ingest\`    
6. │    │     │    
7. │    │     └─▶ LangChain → Split → OpenAI Embed → Chroma    
8. │    │    
9. │    └─▶ User Question → FastAPI \`/query\`    
10. │          │    
11. │          └─▶ OpenAI Embed → Chroma Search → OpenAI LLM → Answer    
12. │    
13. └─▶ \[Chroma DB (Docker)\]    
14.       │    
15.       └─▶ Stores: {id, embedding, metadata: {doc\_name, page, text\_chunk}}  
      
    ---

    ### **Expanded Layer Details**

    #### **1\. User Interface (Streamlit)**

**Components**:

* **File Upload Widget**: Drag-and-drop for PDF/DOCX/TXT files (using `st.file_uploader`).  
* **Chat Interface**: Text input box \+ message history panel (via `st.chat_message`).  
* **Source Citation**: Displays source document/page for each answer (e.g., "Source: Contract.pdf, Page 12").

**Key Libraries**:

* `streamlit` (core UI), `st-annotated-text` (for highlighting citations).  
  ---

  #### **2\. Application Layer (FastAPI)**

**Endpoints**:

1. **POST `/ingest`**:  
   * **Input**: Multipart file upload.  
   * **Workflow**:  
     * Validate file type (block non-PDF/DOCX/TXT).  
     * Offload processing to a background task (to avoid UI blocking).  
     * Return `task_id` for async status tracking.  
   * **Error Handling**: Retry failed embeddings (3 attempts).  
2. **POST `/query`**:  
   * **Input**: `{doc_id: str, question: str, history: []}`.  
   * **Workflow**:  
     * Validate `doc_id` exists in Chroma.  
     * Combine chat history \+ question for context-aware follow-ups.  
     * Return `{answer: str, sources: [{doc: str, page: int}]}`.

**Key Libraries**:

* `fastapi` (server), `celery` (background tasks), `uvicorn` (ASGI server).  
  ---

  #### **3\. Data Processing (LangChain)**

**Steps**:

1. **Document Loading**:  
   * PDF: `PyPDFLoader` (for text) \+ `Unstructured` (for tables).  
   * DOCX: `UnstructuredWordDocumentLoader`.  
2. **Chunking**:  
   * Split text into 500-token chunks with 50-token overlap (using `RecursiveCharacterTextSplitter`).  
   * Preserve page numbers for citations.  
3. **Embedding**:  
   * Call OpenAI’s `text-embedding-ada-002` (1536-dim vectors).  
   * Rate-limited to 100 requests/minute (avoid API throttling).  
4. **Answer Generation**:  
   * Use `RetrievalQA` chain with `gpt-3.5-turbo`, templated prompt:  
     "Answer the question based only on this context: {context}. Question: {question}"

   ---

   #### **4\. Vector Database (Chroma in Docker)**

**Setup**:

**Docker Command**:

* docker run \-p 8000:8000 \-v chroma\_data:/chroma/chroma chromadb/chroma  
* **Persistence**: Data saved to mounted volume `chroma_data`.

**Schema**:

| {    "id": "unique\_id",    "embedding": \[0.12, 0.34, ...\],  \# 1536-dimensional    "metadata": {      "doc\_name": "contract.pdf",      "page": 5,      "text\_chunk": "The payment deadline is 30 days..."    }  } |
| :---- |

**Query**:

* Semantic search via `collection.query(query_embeddings=[...], n_results=3)`.  
  ---

  #### **5\. AI Services (OpenAI)**

**Models**:

1. **Embeddings**:  
   * Model: `text-embedding-ada-002` (cost: $0.0001/1k tokens).  
   * Tokenization: `tiktoken` to count tokens pre-API call.  
2. **Answer Generation**:  
   * Model: `gpt-3.5-turbo` (cost: $0.002/1k tokens).  
   * Fallback: If context exceeds 4k tokens, use `map_reduce` summarization.

**Cost Control**:

* Cache embeddings for re-uploaded documents (MD5 hash check).  
* Limit users to 10 queries/minute.  
  ---

  ### **Critical Interactions Between Layers**

1. **Upload Flow**:  
   `Streamlit → FastAPI → LangChain → OpenAI → Chroma`  
2. **Query Flow**:  
   `Streamlit → FastAPI → OpenAI → Chroma → LangChain → OpenAI → Streamlit`  
   ---

   ### **Failure Points & Mitigations**

| Layer | Failure Risk | Mitigation |
| ----- | ----- | ----- |
| **Streamlit UI** | Large files freeze the browser | Client-side file size limits (e.g., 50MB) |
| **FastAPI** | API timeout during heavy loads | Async tasks \+ Celery job queues |
| **OpenAI** | API rate limits exceeded | Exponential backoff \+ retry logic |
| **Chroma** | Data loss on Docker crash | Daily backups of `chroma_data` volume |

---

## **3\. Key Components**

| Component | Responsibility | Technology Choices |
| ----- | ----- | ----- |
| **Frontend** | Drag-and-drop UI, chat-style Q\&A | Streamlit (Python) |
| **Document Ingest** | Parse PDF/DOCX, split text into chunks | LangChain \+ `PyPDF2`/`Unstructured` |
| **Embedding Service** | Convert text chunks to vectors | OpenAI `text-embedding-ada-002` |
| **Vector DB** | Store/retrieve embeddings | Chroma (Dockerized) |
| **Query Engine** | Retrieve relevant chunks, generate answers | LangChain `RetrievalQA` \+ OpenAI |
| **API Layer** | Coordinate workflows, error handling | FastAPI (Python) |

---

## **4\. Data Flow**

### **I. Document Upload Process**

**Goal**: Convert a user-uploaded document into searchable vectors stored in Chroma.

#### **Step 1: User Uploads a Document**

* **User Action**: Drags-and-drops a file (e.g., `contract.pdf`) into the Streamlit UI.  
* **Technical Details**:  
  * Streamlit’s `st.file_uploader` handles the file input.  
  * File size limit: **50 MB** (to avoid browser crashes).  
  * Supported formats: `PDF`, `DOCX`, `TXT`.

  #### **Step 2: Backend Validates File Type**

* **Checks**:  
  * File extension (e.g., `.pdf`).  
  * MIME type (e.g., `application/pdf`).  
* **Rejection**: Non-supported files trigger an error: *“Unsupported file type. Please upload a PDF, DOCX, or TXT file.”*

  #### **Step 3: LangChain Splits the Document**

* **Workflow**:  
  1. **Text Extraction**:  
     * For PDFs: Use `PyPDFLoader` (text) \+ `Unstructured` (tables).  
     * For DOCX: Use `UnstructuredWordDocumentLoader`.  
  2. **Chunking**:  
     * Split text into **500-token chunks** using `RecursiveCharacterTextSplitter`.  
     * **10% overlap** (50 tokens) to preserve context between chunks.

Example:  
Original Text: "The payment deadline is 30 days after invoice receipt. Late payments incur a 5% fee."  

→ Chunk 1: "The payment deadline is 30 days after invoice receipt."  

→ Chunk 2: "Late payments incur a 5% fee."

#### **Step 4: OpenAI Generates Embeddings**

* **Embedding Model**: `text-embedding-ada-002` (1536-dimensional vectors).  
* **Process**:  
  * Each text chunk is sent to OpenAI’s API.

Example API call:  
embedding \= openai.Embedding.create(input="Chunk text", model="text-embedding-ada-002")\["data"\]\[0\]\["embedding"\]

* **Cost**: \~$0.0001 per 1k tokens.

  #### **Step 5: Chroma Stores Embeddings**

**Data Structure**:

| {    "id": "chunk\_1",    "embedding": \[0.23, \-0.45, ..., 0.89\],  \# 1536 numbers    "metadata": {      "doc\_name": "contract.pdf",      "page": 3,  \# Source page number      "text\_chunk": "The payment deadline is 30 days..."    }  } |
| :---- |

* **Storage**:  
  * Chroma runs in a Docker container with a persistent volume (`chroma_data`).  
  * Data is saved to disk to survive container restarts.


  ### **II. Query Handling Process**

**Goal**: Answer a user’s question using the document’s content.

#### **Step 1: User Submits a Question**

* **Example**: *“What’s the late payment penalty?”*  
* **UI**: Streamlit’s `st.chat_input` captures the question.

  #### **Step 2: OpenAI Embeds the Question**

* **Same Model**: `text-embedding-ada-002` converts the question into a vector.  
  **Example**:  
  question \= "What’s the late payment penalty?"    
  question\_embedding \= openai.Embedding.create(input=question, model="text-embedding-ada-002")

  #### **Step 3: Chroma Retrieves Relevant Chunks**

* **Semantic Search**:  
  * Chroma compares the question’s vector to stored document vectors.  
  * Returns the **top-3 chunks** with the highest cosine similarity.

| Query Code:results \= chroma\_collection.query(    query\_embeddings=\[question\_embedding\],    n\_results=3,    include=\["metadatas", "documents"\]  ) |
| :---- |


  **Output**:

| {    "ids": \[\["chunk\_2"\]\],    "metadatas": \[\[{"doc\_name": "contract.pdf", "page": 3}\]\],    "documents": \[\["Late payments incur a 5% fee."\]\]  } |
| :---- |

  #### **Step 4: OpenAI Generates an Answer**

* **Prompt Engineering**:

| LangChain's RetrievalQA chain combines the question and retrieved chunks into a structured prompt:"Answer this question: 'What's the late payment penalty?'  Use only this context:  Late payments incur a 5% fee. \[Page 3\]  The deadline is 30 days. \[Page 3\]  If unsure, say 'I don't know'." |
| :---- |

  **LLM Call**:

| response \= openai.ChatCompletion.create(    model="gpt-3.5-turbo",    messages=\[{"role": "user", "content": prompt}\]  )  answer \= response.choices\[0\].message.content |
| :---- |

* **Output**: *“The late payment penalty is a 5% fee.”*

  #### **Step 5: Streamlit Displays the Answer**

* **UI Components**:  
  * **Answer Box**: Shows the generated answer.  
  * **Source Citations**: Lists document name and page numbers (e.g., *“Source: contract.pdf, Page 3”*).

  ### **Key Technical Considerations**

1. **Overlap in Chunking**:  
   * 10% overlap ensures critical context isn’t split between chunks (e.g., a definition starting in one chunk and ending in the next).  
2. **Token Limits**:  
   * `gpt-3.5-turbo` has a 4k-token context window. If chunks exceed this, use `map_reduce` to summarize.  
3. **Error Handling**:  
   * Retry failed OpenAI API calls (3 attempts with exponential backoff).  
   * Validate Chroma responses to avoid `KeyError` on missing metadata.

   

   ### **End-to-End Flow Example**

1. **User Uploads** `contract.pdf` → Split into 10 chunks.  
2. **User Asks**: *“What’s the late payment penalty?”*  
3. **System Finds**: Chunk with *“Late payments incur a 5% fee.”* (Page 3).  
4. **Answer Displayed**:

| ANSWER: The late payment penalty is a 5% fee.  SOURCES: contract.pdf (Page 3) |
| :---- |

## ---

**5\. APIs & Interfaces**

### **Key Endpoints**

#### **1\. `/ingest`**

**Method**: `POST`  
**Purpose**: Upload and process a document for future Q\&A.

**Input**:

* file: UploadFile (PDF/DOCX/TXT)


**Workflow**:

1. Validate file type (reject non-PDF/DOCX/TXT).  
2. Generate a unique `doc_id` (e.g., UUID4).  
3. Offload processing to a background task (to avoid blocking the UI).  
4. Return immediately with `doc_id` and status.

**Success Response**:

| {    "doc\_id": "a1b2c3d4",    "status": "processing",    "message": "Document is being processed. Check /status later."  } |
| :---- |

**Error Responses**:  
| Scenario | HTTP Code | Response Example |  
|-------------------------|-----------|-------------------------------------------|  
| Invalid file type | 400 | `{"error": "Unsupported file type: .csv"}` |  
| File too large (\>50MB) | 413 | `{"error": "File exceeds 50MB limit"}` |

#### **2\. `/query`**

**Method**: `POST`  
**Purpose**: Answer a question based on an uploaded document.

**Input**:

| {    "doc\_id": "a1b2c3d4",    "question": "What's the late payment penalty?"  } |
| :---- |

**Workflow**:

1. Validate `doc_id` exists in Chroma.  
2. Embed the question using OpenAI.  
3. Retrieve top-3 relevant chunks from Chroma.  
4. Generate an answer using OpenAI’s LLM.

**Success Response**:

| {    "answer": "The late payment penalty is 5%.",    "sources": \[      {"doc\_name": "contract.pdf", "page": 3},      {"doc\_name": "contract.pdf", "page": 5}    \]  } |
| :---- |

**Error Responses**:  
| Scenario | HTTP Code | Response Example |  
|-------------------------|-----------|-------------------------------------------|  
| Invalid `doc_id` | 404 | `{"error": "Document a1b2c3d4 not found"}` |  
| OpenAI API failure | 503 | `{"error": "LLM service unavailable"}` |

**Rate Limiting**:

10 requests/minute per IP to control OpenAI costs.

### **UI Components**

#### **1\. Document Upload Zone**

**Technical Implementation (Streamlit)**:

| import streamlit as st  uploaded\_file \= st.file\_uploader(    "Drag PDF/DOCX/TXT here",    type=\["pdf", "docx", "txt"\],    accept\_multiple\_files=False  ) |
| :---- |

* **Validation**: Immediate feedback for unsupported files.  
* **Progress Bar**: Shows processing status after upload.

  #### **2\. Chat Interface**

**Technical Implementation**:

| \# Initialize chat history  if "messages" not in st.session\_state:      st.session\_state.messages \= \[\]  \# Display chat history  for message in st.session\_state.messages:      with st.chat\_message(message\["role"\]):          st.markdown(message\["content"\])  \# User input  question \= st.chat\_input("Ask a question about the document...")  if question:      \# Add to history      st.session\_state.messages.append({"role": "user", "content": question})      \# Call /query API      response \= requests.post(API\_URL \+ "/query", json={"doc\_id": doc\_id, "question": question})      \# Display answer      with st.chat\_message("assistant"):          st.markdown(response.json()\["answer"\]) |
| :---- |

#### **3\. Source Citation Panel**

**Technical Implementation**:

| \# After displaying the answer  with st.expander("View Sources"):      for source in response.json()\["sources"\]:          st.write(f"📄 {source\['doc\_name'\]}, Page {source\['page'\]}")          st.code(source\["text\_chunk"\])  \# Optional: Show text snippet |
| :---- |

### **Security & Best Practices**

1. **API Key Management**:  
   * Store OpenAI keys in environment variables (never hardcode).  
   * Use `st.secrets` in Streamlit for deployment.  
2. **Input Sanitization**:  
   * Block SQLi/prompt injection via regex filters (e.g., `[^a-zA-Z0-9?., ]`).  
3. **CORS**: Configure FastAPI to allow requests only from the Streamlit UI domain.

   ### **Example End-to-End Interaction**

**User Action**:

1. Uploads `contract.pdf` → gets `doc_id: "a1b2c3d4"`.  
2. Asks: *“What’s the late payment penalty?”*

**System Flow**:

1. FastAPI validates `doc_id` and embeds the question.  
2. Chroma returns chunks from page 3 and 5\.  
3. OpenAI generates answer: *“5% penalty”*.

**UI Output**:

* USER: What’s the late payment penalty?    
* ASSISTANT: The late payment penalty is 5%.    
* \[View Sources\] → contract.pdf (Page 3), contract.pdf (Page 5\)

---

## **6\. Infrastructure**

### **Local Development Setup**

#### **Components**

1. **Chroma (Docker)**:  
   * **Run Command**:

| docker run \-d \--name chroma \\    \-p 8000:8000 \\    \-v chroma\_data:/chroma/chroma \\    chromadb/chroma |
| :---- |

   * **Persistence**: Data stored in Docker volume `chroma_data` survives container restarts.  
   * **Test Data Reset**:  
     docker volume rm chroma\_data && docker volume create chroma\_data  
2. **Streamlit & FastAPI (Python venv)**:  
   * **Setup**:

| python \-m venv .venv  source .venv/bin/activate  \# Linux/Mac  .\\.venv\\Scripts\\activate   \# Windows  pip install fastapi streamlit langchain openai python-multipart |
| :---- |

   * **Environment Variables**

| export OPENAI\_API\_KEY="sk-..."  \# Required  export CHROMA\_HOST="localhost"  \# Chroma endpoint |
| :---- |

   * **Local Network**:

| Streamlit UI: http://localhost:8501FastAPI: http://localhost:8000Chroma: http://localhost:8000 |
| :---- |

   ---

   ### **Future Deployment**

   #### **Production Architecture**

┌───────────────────┐       ┌──────────────┐       ┌────────────┐  

│    Streamlit      │       │    FastAPI   │       │   Chroma   │  

│    (Frontend)     │ ◄───► │ (Backend)    │ ◄───► │ (VectorDB) │  

└───────────────────┘       └──────────────┘       └────────────┘  

       ▲                           ▲  

       │                           │  

       └───────────User────────────┘

#### **Docker Compose**

| version: "3.9"  services:    chroma:      image: chromadb/chroma      ports:        \- "8000:8000"      volumes:        \- chroma\_data:/chroma/chroma    backend:      build: ./backend  \# FastAPI app      ports:        \- "8001:8000"      environment:        \- OPENAI\_API\_KEY=${OPENAI\_API\_KEY}        \- CHROMA\_HOST=chroma      depends\_on:        \- chroma    frontend:      build: ./frontend  \# Streamlit app      ports:        \- "8501:8501"      environment:        \- API\_URL=http://backend:8000 |
| :---- |

#### **Cloud VM Deployment**

| Provider | Cost | Setup Steps |
| ----- | ----- | ----- |
| **DigitalOcean** | $5/month | 1-click Docker install, 512MB RAM |
| **AWS Lightsail** | $7/month | Preconfigured Docker \+ 1GB RAM |
| **Hetzner** | €4/month | Budget-friendly, 2GB RAM |

**Deployment Steps**:

1. Clone repo to VM: `git clone https://github.com/your/docuquery.git`  
2. Add `.env` file with OpenAI API key.  
3. Run: `docker compose up -d`  
   ---

   ### **Monitoring & Observability**

   #### **Logging**

| \# FastAPI logging setup (main.py)  import logging  logging.basicConfig(      filename="app.log",      level=logging.INFO,      format="%(asctime)s \- %(name)s \- %(levelname)s \- %(message)s",      rotation="100 MB"  \# Rotate large logs  )  \# Example log entry  logger \= logging.getLogger(\_\_name\_\_)  logger.info(f"Ingested document: {doc\_id}") |
| :---- |

   

**Sample Log**:

| 2024-02-20 14:30:45 \- uvicorn \- INFO \- Started server process \[123\]  2024-02-20 14:31:12 \- app \- INFO \- Ingested document: a1b2c3d4 |
| :---- |

#### **Metrics (Optional)**

* **Prometheus** Setup:

| \# docker-compose.yml  prometheus:    image: prom/prometheus    volumes:      \- ./prometheus.yml:/etc/prometheus/prometheus.yml    ports:      \- "9090:9090" |
| :---- |


* **FastAPI Metrics**:  
  * Use `prometheus-fastapi-instrumentator` to expose:  
    * API request count  
    * Error rates  
    * Latency percentiles  
* **Grafana Dashboard**:

| Prebuilt dashboard for LLM costs:sum(rate(openai\_api\_calls\_total\[5m\])) by (model) |
| :---- |

### **Key Infrastructure Decisions**

| Component | Choice | Rationale |
| ----- | ----- | ----- |
| **Orchestration** | Docker Compose | Simplest way to run multi-container apps |
| **Persistence** | Docker Volume | No cloud dependency for prototype phase |
| **Monitoring** | Python Logging | Zero-cost solution for basic observability |

### **Failure Recovery**

1. **Chroma Data Loss**:

| Daily backup script:docker run \--rm \-v chroma\_data:/data \-v $(pwd)/backups:/backup \\    alpine tar czf /backup/chroma\_$(date \+%s).tar.gz /data |
| :---- |

2. **API Outages**:  
   * Retry failed OpenAI calls with exponential backoff.  
   * Fallback to cached answers for common queries.

---

## **7\. Security**

* **Data**: Encrypt documents at rest (AES-256) for sensitive use cases.  
* **API Keys**: Store OpenAI keys in environment variables (never hardcoded).  
* **Input Sanitization**: Block SQLi and prompt injection attacks.

---

## **8\. Team Roles**

| Role | Responsibilities | Owner |
| ----- | ----- | ----- |
| **Frontend** | Streamlit UI, error handling | Junior Eng |
| **Backend** | FastAPI, LangChain integration, Chroma setup | Senior Eng |
| **AI/ML** | Optimize chunking/embedding, prompt engineering | Staff Eng |
| **DevOps** | Docker setup, deployment pipeline | Senior Eng |

---

## **9\. Milestones & Timeline**

| Milestone | Deliverables | Timeline |
| ----- | ----- | ----- |
| **Core Pipeline** | End-to-end doc upload \+ Q\&A | Week 1 |
| **Dockerized DB** | Chroma running in Docker \+ persistence | Week 2 |
| **UI Polish** | Streamlit interface with citations | Week 3 |
| **V1 Prototype** | Testable demo with error handling | Week 4 |

---

## **10\. Risks & Mitigations**

| Risk | Mitigation | Owner |
| ----- | ----- | ----- |
| Chroma performance issues | Benchmark early; switch to Qdrant if needed | DevOps |
| OpenAI API latency/cost | Cache embeddings, use `gpt-3.5-turbo` | AI/ML |
| Chunking breaks document context | Test overlap strategies, adjust token size | AI/ML |

---

## **11\. Dependencies**

1. OpenAI API access (ensure team has keys).  
2. Chroma’s Docker image stability (monitor GitHub issues).  
3. LangChain compatibility with latest OpenAI SDK.

---

## **12\. Next Steps**

1. Team kickoff: Assign owners for each component (Frontend/Backend/AI/DevOps).  
2. Draft detailed technical specs for `/ingest` and `/query` (2-page max).  
3. Set up Git repo with `docker-compose.yml` and boilerplate code.

