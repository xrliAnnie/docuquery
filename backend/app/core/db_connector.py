from typing import List, Optional
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import chromadb
import os
import logging

logger = logging.getLogger(__name__)

class DBConnector:
    def __init__(self, collection_name: str = "default"):
        """Initialize the database connector with OpenAI embeddings and a fixed collection name."""
        try:
            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                model="text-embedding-ada-002"
            )
            
            # Initialize chroma client
            self.client = chromadb.HttpClient(
                host="chroma",
                port=8000,
                ssl=False,
                settings=chromadb.Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True,
                    chroma_server_api_default_path="/api/v1"
                )
            )

            # Use the Chroma wrapper from langchain_community.vectorstores.
            # This returns an object that has the "add_texts" method.
            self.db = Chroma(
                client=self.client,
                collection_name=collection_name,
                embedding_function=self.embeddings
            )
            logger.info("Successfully initialized ChromaDB connection with collection: langchain")
        except Exception as e:
            logger.error(f"Error initializing DB connector: {str(e)}")
            raise
            
    async def store_documents(self, documents: List[Document], collection_id: str):
        """Store documents in Chroma DB"""
        try:
            # Create a new collection with the provided ID
            self.db = Chroma(
                client=self.client,
                collection_name=collection_id,
                embedding_function=self.embeddings
            )
            
            # Store documents in the new collection
            self.db.add(documents)
            
        except Exception as e:
            logger.error(f"Error storing documents: {str(e)}")
            raise

    async def query_documents(self, query_embedding: list, filters=None):
        try:
            logger.info("Querying documents in ChromaDB")
            
            # Use raw embeddings for similarity search
            docs = self.db.similarity_search_by_vector(
                embedding=query_embedding,
                k=3,
                filter=filters
            )
            
            return {
                "answer": docs[0].page_content if docs else "No results found",
                "sources": [{"page": i, "text": doc.page_content} for i, doc in enumerate(docs)]
            }
            
        except Exception as e:
            logger.error(f"Error querying documents: {str(e)}")
            raise

    async def get_collection(self, collection_id: str = None):
        """Get all documents in the collection"""
        try:
            if collection_id is None:
                collection = self.db._collection
                results = collection.get()
            else:
                collection = self.db._collection
                results = collection.get(ids=[collection_id])
            
            logger.info("Successfully retrieved collection")
            return results
        except Exception as e:
            logger.error(f"Error retrieving collection: {str(e)}")
            raise
