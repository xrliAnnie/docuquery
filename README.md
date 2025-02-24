# Document Query System

A powerful RAG (Retrieval-Augmented Generation) system that allows users to upload documents and query them using natural language. The system uses ChromaDB for vector storage and OpenAI's GPT model for generating responses.

## Features

- **Document Processing**: Supports multiple file formats (PDF, DOCX, TXT)
- **Smart Text Chunking**: Implements recursive character text splitting for optimal context preservation
- **Vector Storage**: Uses ChromaDB for efficient vector storage and retrieval
- **RAG Implementation**: Combines ChromaDB retrieval with OpenAI's GPT for accurate answers
- **REST API**: FastAPI-based endpoints for document upload and querying

## Technical Stack

- **Backend Framework**: FastAPI
- **Vector Database**: ChromaDB
- **Language Model**: OpenAI GPT-3.5-turbo
- **Embeddings**: OpenAI text-embedding-ada-002
- **Document Processing**: PyPDF2, python-docx
- **Container Platform**: Docker

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API Key
- Node.js (v18 or higher)
- pnpm (v8 or higher)

### Environment Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```

2. Create environment files:

   For backend:
   ```bash
   # In root directory
   cp .env.example .env
   # Add your OpenAI API key to .env
   OPENAI_API_KEY=your_openai_api_key
   ```

   For frontend:
   ```bash
   # In frontend directory
   cp .env.example .env
   # Add your backend API URL
   VITE_API_URL=http://localhost:8000
   ```

### Running the Services

#### Using Docker (Recommended)

1. Start all services:
   ```bash
   cd infra && \
   docker-compose down && \
   docker system prune -a --volumes && \
   docker-compose build --no-cache && \
   docker-compose up -d
   ```

   This will start both the frontend and backend services:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000

#### Development Mode

1. Start the Backend:
   ```bash
   # From the root directory
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

2. Start the Frontend:
   ```bash
   # From the root directory
   cd frontend
   streamlit run app/main.py
   ```

   The services will be available at:
   - Frontend (Dev): http://localhost:8501
   - Backend (Dev): http://localhost:8000

### Viewing Logs

For Docker deployment:
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f frontend
docker-compose logs -f backend
```

For development mode:
- Backend logs will appear in the terminal running uvicorn
- Frontend logs will appear in the terminal running streamlit run app/main.py

### API Endpoints

#### Upload Document
```http
POST /api/documents
Content-Type: multipart/form-data

file: <document_file>
```

#### Query Document
```http
POST /api/query
Content-Type: application/json

{
    "text": "your question here",
    "context_id": "document_id"
}
```

#### Get Document Status
```http
GET /api/documents/{doc_id}
```

## Architecture

### Components

1. **DocumentLoader**: Handles document ingestion and chunking
   - Supports multiple file formats
   - Implements smart text chunking
   - Preserves document metadata

2. **DBConnector**: Manages ChromaDB interactions
   - Handles collection creation and management
   - Manages document embeddings
   - Provides retrieval capabilities

3. **EmbeddingProcessor**: Processes text embeddings
   - Uses OpenAI's embedding model
   - Handles both document and query embeddings

4. **API Layer**: FastAPI-based REST endpoints
   - Document upload and processing
   - Query processing and response generation
   - Document status tracking

## Development

### Code Structure
```
backend/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   ├── db_connector.py
│   │   ├── document_loader.py
│   │   └── embedding_processor.py
│   └── main.py
└── tests/
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the GPT and embedding models
- ChromaDB team for the vector database
- FastAPI team for the web framework