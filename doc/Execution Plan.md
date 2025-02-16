## **1\. Repositories & Language Choices**

### **Repository Strategy**

**Single Monorepo** (recommended for simplicity in a prototype):

* Contains all code (frontend, backend, infrastructure) in one repository.

**Folder Structure**:  
docuquery/    
├── frontend/        \# Streamlit UI    
├── backend/         \# FastAPI \+ LangChain    
├── infra/           \# Dockerfiles, docker-compose.yml    
└── docs/            \# Design docs, API specs

**Alternative**: Separate repos for frontend/backend/infra (overkill for a prototype).

### **Language & Framework Choices**

| Component | Options | Pros/Cons | Recommended Choice |
| ----- | ----- | ----- | ----- |
| **Frontend (UI)** | **Streamlit (Python)** | ✅ Fast setup, no HTML/JS needed ❌ Limited UI customization | Streamlit |
|  | React \+ TypeScript | ✅ Highly customizable ❌ Requires frontend expertise, slower to build | Not needed for prototype |
| **Backend (API)** | **FastAPI (Python)** | ✅ Async support, integrates with LangChain/OpenAI ❌ Python-only | FastAPI |
|  | Express.js (Node.js) | ✅ JS ecosystem ❌ Harder to integrate with Python-based AI tools | Avoid for this project |
| **Vector DB** | **Chroma (Docker \+ Python)** | ✅ Free, self-hosted ❌ Not scalable beyond 100k docs | Chroma |
| **AI Workflows** | **LangChain (Python)** | ✅ Simplifies RAG pipelines ❌ Steep learning curve | LangChain |

---

## **2\. Execution Sequence & Outcomes**

### **Phase 1: Core Pipeline (Week 1\)**

**Goal**: End-to-end document upload and Q\&A.  
**Steps**:

1. **Setup Repo**:  
   * Initialize Git repo with `frontend/`, `backend/`, `infra/` folders.  
   * Add `requirements.txt` for Python dependencies.  
2. **Backend (FastAPI)**:  
   * Build `/ingest` and `/query` endpoints.  
   * Integrate LangChain’s document loaders and OpenAI embeddings.  
3. **Frontend (Streamlit)**:  
   * Create drag-and-drop UI and chat interface.  
   * Connect to FastAPI endpoints.  
4. **Testing**:  
   * Validate PDF/DOCX ingestion and basic Q\&A.

**Outcome**:

* Functional prototype where users can upload a document and ask questions locally.

---

### **Phase 2: Dockerize Chroma (Week 2\)**

**Goal**: Ensure Chroma runs reliably with data persistence.  
**Steps**:

1. **Docker Setup**:  
   * Write `Dockerfile` for Chroma and define `docker-compose.yml`.  
   * Mount persistent volume for Chroma data.  
2. **Integrate with Backend**:  
   * Update FastAPI to connect to Chroma via Docker network.  
3. **Testing**:  
   * Verify data survives container restarts.

**Outcome**:

* Chroma runs in Docker with persistent storage.

---

### **Phase 3: UI Polish (Week 3\)**

**Goal**: Improve usability and trust.  
**Steps**:

1. **Add Source Citations**:  
   * Display document names and page numbers for answers.  
2. **Progress Indicators**:  
   * Show loading spinners during document processing.  
3. **Error Handling**:  
   * Add user-friendly error messages for invalid files/API failures.

**Outcome**:

* Demo-ready UI with citations and feedback mechanisms.

---

### **Phase 4: Testing & Deployment (Week 4\)**

**Goal**: Deploy a stable prototype.  
**Steps**:

1. **Error Handling**:  
   * Implement retries for OpenAI API calls.  
   * Add rate limiting (10 requests/minute).  
2. **Deployment**:  
   * Deploy to a $5/month VM (DigitalOcean) using Docker Compose.  
3. **Monitoring**:  
   * Set up basic logging with Python’s `logging` module.

**Outcome**:

* Prototype deployed on a cloud VM accessible via URL.

---

## **3\. Tools & Infrastructure**

### **Development Phase**

| Tool | Purpose | Alternatives | Pros/Cons | Recommendation |
| ----- | ----- | ----- | ----- | ----- |
| **Python 3.8+** | Core language for all components | Node.js, Go | ✅ Unifies AI/backend code ❌ None | Python |
| **Docker** | Containerize Chroma | Podman | ✅ Industry standard | Docker |
| **Git** | Version control | SVN, Mercurial | ✅ GitHub/GitLab integration | Git |

### **Deployment Phase**

| Tool | Purpose | Alternatives | Pros/Cons | Recommendation |
| ----- | ----- | ----- | ----- | ----- |
| **Docker Compose** | Orchestrate services | Kubernetes | ✅ Simple, no overkill | Docker Compose |
| **DigitalOcean** | Host prototype | AWS Lightsail, Hetzner | ✅ Cheap, 1-click Docker | DigitalOcean |
| **Prometheus** | Metrics (optional) | Datadog, New Relic | ✅ Free, integrates with Grafana | Prometheus |

---

## **Final Recommendations**

1. **Use a single Python monorepo** to streamline collaboration.  
2. **Prioritize FastAPI \+ Streamlit** for rapid prototyping.  
3. **Deploy early** to a $5/month VM to test real-world performance.

