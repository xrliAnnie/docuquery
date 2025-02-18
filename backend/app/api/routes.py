from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.core.document_loader import DocumentLoader
from app.core.embedding_processor import EmbeddingProcessor
from app.core.db_connector import DBConnector

router = APIRouter()

# Pydantic models
class Query(BaseModel):
    text: str
    filters: Optional[Dict] = None

class Response(BaseModel):
    answer: str
    sources: List[Dict]

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Endpoint to ingest a document, process it, and store in the vector database.
    """
    try:
        # Initialize processors
        doc_loader = DocumentLoader()
        embedding_processor = EmbeddingProcessor()
        db = DBConnector()

        # Extract text from document
        text_chunks = await doc_loader.process_file(file)

        # Create metadata
        metadata = {
            "filename": file.filename,
            "content_type": file.content_type
        }

        # Process chunks and create embeddings
        documents = await embedding_processor.process_chunks(text_chunks, metadata)

        # Store in database
        await db.store_documents(documents)

        return {"message": "Document processed successfully", "chunks": len(text_chunks)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=Response)
async def query_document(query: Query):
    """
    Endpoint to query the stored documents and get relevant answers.
    """
    try:
        # Initialize processors
        embedding_processor = EmbeddingProcessor()
        db = DBConnector()

        # Process query and get response
        query_embedding = await embedding_processor.process_query(query.text)
        results = await db.query_documents(query_embedding, query.filters)

        # Format response
        return {
            "answer": results.answer,
            "sources": results.sources
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}