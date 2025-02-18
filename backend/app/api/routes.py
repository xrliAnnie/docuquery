from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
import traceback  # Add this import
from app.core.document_loader import DocumentLoader
from app.core.embedding_processor import EmbeddingProcessor
from app.core.db_connector import DBConnector

# Set up logging
logger = logging.getLogger(__name__)

# Define response models
class Source(BaseModel):
    page: int
    text: str

class Response(BaseModel):
    answer: str
    sources: List[Source] = []

class Query(BaseModel):
    text: str
    filters: Optional[Dict[str, str]] = None

router = APIRouter()

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Endpoint to ingest a document, process it, and store in the vector database.
    """
    try:
        logger.info(f"Processing file: {file.filename}")
        
        # Initialize document loader
        doc_loader = DocumentLoader()

        # Process the document
        try:
            # Extract text and get chunks
            result = await doc_loader.process_file(file)
            
            return {
                "status": "success",
                "message": "Document processed successfully",
                "doc_id": f"doc_{hash(file.filename)}",
                "metadata": {
                    "filename": file.filename,
                    "chunk_count": len(result["chunks"]),
                    "content_type": file.content_type
                }
            }

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing document: {str(e)}"
            )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.post("/query", response_model=Response)
async def query_document(query: Query):
    """
    Endpoint to query the stored documents and get relevant answers.
    """
    try:
        logger.info(f"Processing query: {query.text}")
        
        # Initialize processors
        embedding_processor = EmbeddingProcessor()
        db = DBConnector()

        # Process query
        try:
            # Create embedding for query
            query_embedding = await embedding_processor.process_query(query.text)
            
            # Search database
            results = await db.query_documents(query_embedding, query.filters)

            return {
                "answer": results.answer,
                "sources": results.sources
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing query: {str(e)}"
            )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

@router.get("/documents/{doc_id}")
async def get_document_status(doc_id: str):
    """
    Get document status and metadata from Chroma
    """
    try:
        # Initialize Chroma client
        client = chromadb.HttpClient(host="chroma", port=8000)
        collection = client.get_or_create_collection("langchain")
        
        # Query the collection
        results = collection.get(
            where={"doc_id": doc_id},
            include=["metadatas", "documents"]
        )
        
        return {
            "status": "success",
            "chunk_count": len(results['ids']),
            "metadata": results['metadatas'],
            "sample_chunks": results['documents'][:3]  # First 3 chunks as sample
        }
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document status: {str(e)}"
        )