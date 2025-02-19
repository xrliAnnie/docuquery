from typing import List
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_community.embeddings import OpenAIEmbeddings
import os
import logging
import asyncio
import functools

logger = logging.getLogger(__name__)

class EmbeddingProcessor:
    """Processes documents into embeddings using OpenAI's embedding model."""
    
    def __init__(self):
        """Initialize the embedding processor with OpenAI credentials and text splitter."""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="text-embedding-ada-002"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )

    def load_document(self, file_path: str) -> List[Document]:
        """Load document from file path using appropriate loader."""
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = UnstructuredWordDocumentLoader(file_path)
        else:
            raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")
        
        return loader.load()

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

    async def process_chunks(self, chunks: List[str], metadata: dict) -> List[Document]:
        """Process text chunks into embeddings asynchronously."""
        try:
            if not chunks:
                raise ValueError("Chunks list cannot be empty")
                
            # Create documents and generate embeddings
            documents = self.create_documents(chunks, metadata)
            
            # Generate embeddings for all documents
            embeddings = await self.embeddings.aembed_documents([doc.page_content for doc in documents])
            
            # Attach embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.metadata['embedding'] = embedding
                doc.metadata['text_chunk'] = doc.page_content
                
            return documents
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise

    async def process_query(self, text: str) -> list:
        """
        Asynchronously process a query string into an embedding.
        """
        loop = asyncio.get_running_loop()
        # Use run_in_executor to run the synchronous embed_query call without blocking the event loop
        query_embedding = await loop.run_in_executor(
            None,
            functools.partial(self.embeddings.embed_query, text)
        )
        return query_embedding