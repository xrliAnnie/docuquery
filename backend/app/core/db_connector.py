from typing import List, Optional
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import chromadb
import os
import logging

logger = logging.getLogger(__name__)

class DBConnector:
    def __init__(self):
        """Initialize the database connector with OpenAI embeddings and a fixed collection name."""
        try:
            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            
            # Initialize chroma client
            client = chromadb.HttpClient(
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
                client=client,
                collection_name="langchain",
                embedding_function=self.embeddings
            )
            logger.info("Successfully initialized ChromaDB connection with collection: langchain")
        except Exception as e:
            logger.error(f"Error initializing DB connector: {str(e)}")
            raise
            
    async def store_documents(self, documents: List[Document]) -> bool:
        """Store documents in Chroma DB"""
        try:
            self.db.add_texts(
                texts=[doc.page_content for doc in documents],
                metadatas=[doc.metadata for doc in documents],
                ids=[doc.metadata.get("id", f"doc_{i}") for i, doc in enumerate(documents)]
            )
            logger.info(f"Successfully stored {len(documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Error storing documents: {str(e)}")
            raise

    async def query_documents(self, query_embedding, filters=None):
        try:
            logger.info("Querying documents in ChromaDB")
            
            # Ensure the query_embedding is a string
            if not isinstance(query_embedding, str):
                query_embedding = str(query_embedding)
                
            # Convert filters to dict if they're not already
            if filters is None:
                filters = {}
                
            logger.debug(f"Query embedding: {query_embedding}")
            logger.debug(f"Filters: {filters}")
            
            # Perform the similarity search
            docs = self.db.similarity_search(
                query=query_embedding,
                filter=filters
            )
            
            # Process and return results
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
