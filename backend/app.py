from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from document_loader import DocumentLoader
from embedding_processor import EmbeddingProcessor
from db_connector import DBConnector
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate required environment variables
if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("OPENAI_API_KEY environment variable is not set")

app = FastAPI(
    title="DocuQuery API",
    description="API for document ingestion and question answering",
    version="0.1.0"
)

class Query(BaseModel):
    """
    Request model for document queries
    """
    question: str
    context_id: Optional[str] = None

class QueryResponse(BaseModel):
    """
    Response model for document queries
    """
    answer: str
    sources: List[Dict[str, str]]

# Initialize components
document_loader = DocumentLoader()
embedding_processor = EmbeddingProcessor()
db_connector = DBConnector()

@app.post("/ingest", response_model=Dict[str, str])
async def ingest_document(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Endpoint to ingest documents and create embeddings
    
    Args:
        file (UploadFile): The document to process (PDF, DOCX, or TXT)
        
    Returns:
        Dict containing:
        - collection_id: Unique identifier for the processed document
        - status: Success message
        
    Raises:
        HTTPException: For invalid files or processing errors
    """
    try:
        # Process document
        logger.info(f"Processing document: {file.filename}")
        doc_data = document_loader.process_document(file.file, file.filename)
        
        # Create embeddings
        logger.info("Creating embeddings")
        documents = await embedding_processor.process_chunks(
            doc_data["chunks"],
            doc_data["metadata"]
        )
        
        # Store in database
        logger.info("Storing documents in database")
        collection_id = await db_connector.store_documents(documents)
        
        return {
            "collection_id": collection_id,
            "status": "Document successfully processed"
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/query", response_model=QueryResponse)
async def query_document(query: Query) -> QueryResponse:
    """
    Endpoint to query the document based on user questions
    
    Args:
        query (Query): Query model containing the question and optional context_id
        
    Returns:
        QueryResponse containing:
        - answer: Generated answer to the question
        - sources: List of source citations
        
    Raises:
        HTTPException: If context not found or processing error occurs
    """
    try:
        if query.context_id:
            # Retrieve collection
            collection = await db_connector.get_collection(query.context_id)
            
            # TODO: Implement question answering logic using retrieved collection
            # This will involve:
            # 1. Creating embedding for the question
            # 2. Finding relevant chunks from the collection
            # 3. Using OpenAI to generate an answer
            
            return QueryResponse(
                answer="Not implemented yet",
                sources=[]
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="context_id is required"
            )
            
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)