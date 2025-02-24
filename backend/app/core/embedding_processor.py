from typing import List, Optional
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_community.embeddings import OpenAIEmbeddings
from chromadb import Client
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
import os
import logging
import asyncio
import functools

logger = logging.getLogger(__name__)

class EmbeddingProcessor:
    """Processes documents into embeddings using OpenAI's embedding model."""
    
    def __init__(self, collection_name: str = None):
        """Initialize the database connector with a collection name."""
        try:
            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                model="text-embedding-ada-002"
            )
            
            # Initialize Chroma client
            self.client = Client(
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True,
                    chroma_server_api_default_path="/api/v1"
                )
            )

            # Assign the collection_name argument to an instance attribute
            self.collection_name = collection_name

            # Use the self.collection_name attribute only if it's provided
            if self.collection_name:
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"dimension": 1536, "space": "cosine"}
                )
                logger.info(f"Successfully initialized ChromaDB connection with collection: {self.collection_name}")
            else:
                logger.info("Successfully initialized ChromaDB connection without a default collection")
        except Exception as e:
            logger.error(f"Error initializing DB connector: {str(e)}")
            raise

    def load_document(self, file_path: str) -> List[Document]:
        """Load document from file path using appropriate loader."""
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = UnstructuredWordDocumentLoader(file_path)
        else:
            raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")
        
        documents = loader.load()
        
        # Preserve page numbers
        for doc in documents:
            if "page" not in doc.metadata:
                doc.metadata["page"] = 1  # Default to page 1 if not available
            
        return documents

    def create_documents(self, chunks: List[str], metadata: dict) -> List[Document]:
        """Convert text chunks to Document objects with metadata."""
        if not chunks:
            raise ValueError("Chunks list cannot be empty")

        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    **metadata,
                    'chunk_index': i
                }
            )
            documents.append(doc)
        
        return documents

    async def process_document(self, file_path: str, metadata: dict) -> List[Document]:
        """Process a document file into embeddings asynchronously."""
        try:
            # Load the document
            documents = self.load_document(file_path)
            
            # Split the documents into chunks
            split_docs = self.text_splitter.split_documents(documents)
            
            # Generate embeddings for all documents
            embeddings = await self.embeddings.aembed_documents([doc.page_content for doc in split_docs])
            
            # Attach embeddings and additional metadata to documents
            for i, (doc, embedding) in enumerate(zip(split_docs, embeddings)):
                # Get the page number from the document if available
                page = doc.metadata.get('page', None)
                
                doc.metadata.update({
                    **metadata,
                    'embedding': embedding,
                    'chunk_index': i,
                    'page': page,
                    'text_chunk': doc.page_content
                })
                
            return split_docs
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    async def process_chunks(self, chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks."""
        embeddings = self.embeddings.embed_documents(chunks)
        return embeddings

    async def process_query(self, query: str):
        """
        Asynchronously process a query string into an embedding.
        """
        return self.embeddings.embed_query(query)

# Create an instance of EmbeddingProcessor
embedding_processor = EmbeddingProcessor()
