from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
from langchain.docstore.document import Document
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, embedding_processor, db_connector):
        """
        Initialize the document processor with required components.
        
        Args:
            embedding_processor: Instance of EmbeddingProcessor
            db_connector: Instance of DBConnector
        """
        self.embedding_processor = embedding_processor
        self.db_connector = db_connector

    async def process_document(self, file_path: str) -> bool:
        """
        Process a document by loading, splitting, and storing it in the vector database.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            bool: True if processing was successful
        """
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Load document
            loader = TextLoader(file_path)
            documents = loader.load()
            
            # Add debug logging
            logger.debug(f"Loaded {len(documents)} document chunks")
            for i, doc in enumerate(documents):
                logger.debug(f"Document chunk {i}: {doc.page_content[:100]}...")
            
            # Split document
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)
            
            # Add debug logging
            logger.debug(f"Split into {len(splits)} chunks")
            for i, split in enumerate(splits):
                logger.debug(f"Split {i}: {split.page_content[:100]}...")
            
            # Create embeddings and store in vector store
            embeddings = self.embedding_processor.create_embeddings(splits)
            self.db.store_documents(embeddings)
            
            logger.info("Document processing completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise