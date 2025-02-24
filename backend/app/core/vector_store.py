 from typing import List, Optional
from langchain.docstore.document import Document
from langchain.vectorstores import Chroma
from langchain.embeddings.base import Embeddings
import os

class VectorStore:
    """Manages document embeddings storage using Chroma DB.
    
    This class handles the storage and retrieval of document embeddings using Chroma DB,
    which runs in a Docker container with persistent storage. Each document is stored
    with its embedding vector and associated metadata.
    """

    def __init__(self, embedding_function: Embeddings):
        """Initialize the vector store with a persistent Chroma client.
        
        Args:
            embedding_function: The embedding function to use (e.g., OpenAIEmbeddings)
        """
        persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
        
        self.db = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding_function,
        )

    async def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store.
        
        Args:
            documents: List of Document objects with embeddings and metadata
            
        Returns:
            List of document IDs created in the store
            
        Example document metadata structure:
        {
            "doc_name": "contract.pdf",
            "page": 3,
            "chunk_index": 1,
            "embedding": [0.23, -0.45, ..., 0.89]
        }
        """
        try:
            # Extract text content and metadata
            texts = [doc.page_content for doc in documents]
            metadatas = [
                {
                    k: v for k, v in doc.metadata.items()
                    if k != 'embedding'  # Chroma handles embeddings separately
                }
                for doc in documents
            ]
            
            # Get pre-computed embeddings
            embeddings = [doc.metadata.get('embedding') for doc in documents]
            
            # Add to Chroma
            ids = self.db.add_texts(
                texts=texts,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            # Persist to disk
            self.db.persist()
            
            return ids
        except Exception as e:
            raise Exception(f"Error adding documents to vector store: {str(e)}")

    async def search_similar(
        self,
        query: str,
        n_results: int = 5,
        metadata_filter: Optional[dict] = None
    ) -> List[Document]:
        """Search for similar documents using the query text.
        
        Args:
            query: The text to search for
            n_results: Number of similar documents to return
            metadata_filter: Optional filter for metadata fields
            
        Returns:
            List of similar Document objects with their metadata
        """
        try:
            documents = self.db.similarity_search(
                query,
                k=n_results,
                filter=metadata_filter
            )
            return documents
        except Exception as e:
            raise Exception(f"Error searching vector store: {str(e)}")

    def delete_collection(self):
        """Delete the entire collection and its data."""
        self.db.delete_collection()
        self.db = Chroma(
            persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_data"),
            embedding_function=self.db._embedding_function,
        )