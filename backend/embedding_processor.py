from typing import List
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
import os

class EmbeddingProcessor:
    """Processes text chunks into document embeddings using OpenAI's embedding model.
    
    This class handles the creation of embeddings for text chunks using OpenAI's
    embedding model through LangChain's interface. It manages document creation
    and embedding generation for use in vector similarity searches.
    """

    def __init__(self):
        """Initialize the embedding processor with OpenAI credentials."""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def create_documents(self, chunks: List[str], metadata: dict) -> List[Document]:
        """Convert text chunks to Document objects with metadata.
        
        Args:
            chunks: List of text strings to be converted into documents
            metadata: Dictionary of metadata to be attached to each document
            
        Returns:
            List of Document objects with metadata attached
            
        Raises:
            ValueError: If chunks list is empty
        """
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

    async def process_chunks(self, chunks: List[str], metadata: dict) -> List[Document]:
        """Process text chunks into embeddings asynchronously.
        
        Args:
            chunks: List of text strings to be processed
            metadata: Dictionary of metadata to be attached to each document
            
        Returns:
            List of Document objects with embeddings
            
        Raises:
            Exception: If there's an error during embedding creation
            ValueError: If chunks list is empty
        """
        try:
            if not chunks:
                raise ValueError("Chunks list cannot be empty")
                
            # Create documents and generate embeddings
            documents = self.create_documents(chunks, metadata)
            
            # Generate embeddings for all documents
            # Note: This will be done in batches automatically by LangChain
            embeddings = self.embeddings.embed_documents([doc.page_content for doc in documents])
            
            # Attach embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.metadata['embedding'] = embedding
                
            return documents
        except Exception as e:
            raise Exception(f"Error creating embeddings: {str(e)}")