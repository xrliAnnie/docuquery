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
            
    async def store_documents(self, doc_id: str, documents: List[Document]):
        try:
            # Get or create the collection for the given doc_id
            collection = self.get_or_create_collection(doc_id)

            # Initialize a new Chroma instance for the collection
            db = Chroma(
                client=self.client,
                collection_name=doc_id,
                embedding_function=self.embeddings
            )

            # Add the documents to the collection
            db.add(documents)

        except Exception as e:
            logger.error(f"Error storing documents: {str(e)}")
            raise

    async def query_documents(self, query_embedding: list, collection_id: str):
        """Query a specific document collection"""
        try:
            # Get or create the collection for the given collection_id
            collection = self.get_or_create_collection(collection_id)

            # Initialize a new Chroma instance for the collection
            db_for_query = Chroma(
                client=self.client,
                collection_name=collection_id,
                embedding_function=self.embeddings
            )

            # Query using the underlying collection
            results = db_for_query._collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                include=["metadatas", "documents"]
            )

            return {
                "answer": results["documents"][0][0] if results["documents"] else "No answer",
                "sources": [
                    {"page": meta.get("page", 0), "text": text}
                    for meta, text in zip(results["metadatas"][0], results["documents"][0])
                ]
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

    def get_or_create_collection(self, collection_id: str):
        try:
            return self.client.get_collection(collection_id)
        except Exception as e:
            # Check if the error message indicates that the collection doesn't exist.
            if "does not exist" in str(e):
                return self.client.create_collection(collection_id)
            else:
                raise
