from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import logging
import traceback  # Add this import
import chromadb  # Add this import
from app.core.document_loader import DocumentLoader
from app.core.embedding_processor import EmbeddingProcessor
from app.core.db_connector import DBConnector
from chromadb import Client, Settings

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

class QueryRequest(BaseModel):
    text: str = Field(..., min_length=1)
    filters: Optional[Dict[str, str]] = Field(default_factory=dict)

router = APIRouter()

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Endpoint to ingest a document, process it, store it in the vector database, and return the doc identifier.
    """
    try:
        logger.info(f"Processing file: {file.filename}")
        
        # Initialize Document Loader and process file
        doc_loader = DocumentLoader()
        result = await doc_loader.process_file(file)
        
        # Generate a document id from the file name (or use another unique identifier)
        doc_id = f"doc_{hash(file.filename)}"
        
        # Store document chunks in the Chroma vector store via DBConnector:
        db = DBConnector()
        # We add a "doc_id" field to the metadata of each chunk.
        metadata = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(result["chunks"]))]
        
        db.db.add_texts(
            texts=result["chunks"],
            metadatas=metadata,
            ids=[f"{doc_id}_{i}" for i in range(len(result["chunks"]))]
        )
        
        return {
            "status": "success",
            "message": "Document processed and stored successfully",
            "doc_id": doc_id,
            "metadata": {
                "filename": file.filename,
                "chunk_count": len(result["chunks"]),
                "content_type": file.content_type
            }
        }
    except openai.RateLimitError as e:
        logger.error(f"OpenAI quota exceeded: {str(e)}")
        raise HTTPException(
            status_code=429,
            detail="OpenAI quota exceeded, please check your plan and billing details."
        )
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

@router.post("/query", response_model=Response)
async def query_document(query_data: QueryRequest):
    """
    Endpoint to query the stored documents and get relevant answers.
    """
    try:
        # Add validation for empty query
        if not query_data.text or not query_data.text.strip():
            logger.error("Empty query received")
            raise HTTPException(
                status_code=400,
                detail="Query text cannot be empty"
            )
            
        logger.info(f"Processing query: {query_data.text}")
        
        # Initialize processors
        embedding_processor = EmbeddingProcessor()
        db = DBConnector()

        # Process query
        try:
            # Create embedding for query
            query_embedding = await embedding_processor.process_query(query_data.text)
            
            # Search database
            results = await db.query_documents(query_embedding, query_data.filters)

            return {
                "answer": results["answer"],  # Changed from results.answer
                "sources": results["sources"]  # Changed from results.sources
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing query: {str(e)}"
            )

    except HTTPException:
        raise
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

# backend/app/api/routes.py
@router.get("/documents/{doc_id}")
async def get_document_status(doc_id: str):
    """
    Get document status and metadata from Chroma using the DBConnector.
    """
    try:
        logger.info(f"Fetching document with doc_id: {doc_id} using DBConnector.")

        # Use the DBConnector to ensure you're hitting the same persistent collection.
        db = DBConnector()

        # For debugging, get the underlying collection to log its full content.
        collection = db.db._collection  # Access the raw collection for logging purposes.
        all_items = collection.get()
        logger.debug(f"Complete collection data: {all_items}")

        # Query the collection using the metadata 'doc_id'
        results = collection.get(where={"doc_id": doc_id})
        logger.debug(f"Query results for doc_id {doc_id}: {results}")

        if not results.get("ids"):
            logger.error(
                f"Document {doc_id} not found. Metadata in collection: {all_items.get('metadatas')}"
            )
            return {"status": "error", "message": f"Document {doc_id} not found"}

        logger.info(f"Document {doc_id} found with {len(results['ids'])} chunks.")
        return {
            "status": "success",
            "chunk_count": len(results["ids"]),
            "metadata": results.get("metadatas"),
            "sample_chunks": results["documents"][:3] if results.get("documents") else []
        }
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting document status: {str(e)}")
