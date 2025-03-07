import openai
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
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.embedding_processor import EmbeddingProcessor
import uuid
from langchain.vectorstores import Chroma

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
    context_id: str = Field(..., description="Document collection ID")
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
        
        # Generate a unique document id using a UUID
        doc_id = f"doc_{uuid.uuid4().hex}"
        
        # Initialize DBConnector with the document-specific collection name
        db = DBConnector(collection_name=doc_id)
        db.reset_collection()  # Reset the collection before ingesting documents

        # Prepare metadata (add a doc_id field so it's also stored with each chunk)
        metadata = [{"doc_id": doc_id, "page": i} for i in range(len(result["chunks"]))]

        # Inside the ingest_document endpoint, after processing the file:
        embedding_processor = EmbeddingProcessor()
        embeddings = await embedding_processor.process_chunks(result["chunks"])

        # Store documents with embeddings
        db.collection.add(
            documents=result["chunks"],
            metadatas=metadata,
            ids=[f"{doc_id}_{i}" for i in range(len(result["chunks"]))],
            embeddings=embeddings  # Include embeddings
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
        logger.info(f"Received query request: {query_data}")

        # Validate query
        if not query_data.text or not query_data.text.strip():
            logger.error("Query text cannot be empty")
            raise HTTPException(status_code=400, detail="Query text cannot be empty")
            
        # Initialize processors
        embedding_processor = EmbeddingProcessor()
        db = DBConnector()

        # Process query
        query_embedding = await embedding_processor.process_query(query_data.text)
        
        # Validate documents
        documents = await db.query_documents(
            query_embedding=query_embedding,
            collection_id=query_data.context_id
        )
        if not documents:
            logger.error(f"No documents found for this context_id: {query_data.context_id}")
            raise HTTPException(status_code=400, detail="No documents found for this context_id")
        if len(documents) < 2:  # Minimum context chunks
            logger.error(f"Insufficient context for answering with {len(documents)} documents")
            raise HTTPException(status_code=400, detail="Insufficient context for answering")
        
        # Create vector store connection
        vector_store = Chroma(
            client=db.client,
            collection_name=query_data.context_id,
            embedding_function=db.embeddings
        )

        # Create RAG chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
        
        result = qa_chain.invoke({"query": query_data.text})
        
        return {
            "answer": result["result"],
            "sources": [
                {
                    "doc": doc.metadata.get("doc_id", ""),
                    "page": doc.metadata.get("page", 0),
                    "text": doc.page_content  # Add the text field from the source document
                }
                for doc in result["source_documents"]
            ]
        }

    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        # Initialize DBConnector with the document-specific collection name
        db = DBConnector(collection_name=doc_id)
        collection = db.get_collection(doc_id)  # Remove 'await'
        logger.info(f"Fetching document with doc_id: {doc_id} using {collection}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
