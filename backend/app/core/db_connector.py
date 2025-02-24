from typing import List, Optional
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import chromadb
import os
import logging
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
from chromadb import Client
from langchain.vectorstores import Chroma as LangChainChroma
from chromadb.api.types import EmbeddingFunction, Embeddable, DataLoader, Loadable

logger = logging.getLogger(__name__)

class DBConnector:
    def __init__(self, collection_name: str = "docuquery"):
        """Initialize the database connector with a fixed collection name."""
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
                self.collection = self.get_collection(
                    name=self.collection_name,
                    embedding_function=self.embeddings
                )
                logger.info(f"Successfully initialized ChromaDB connection with collection: {self.collection_name}")
            else:
                logger.info("Successfully initialized ChromaDB connection without a default collection")

            # Optional: Sanity check for embedding dimension
            sample_embedding = self.embeddings.embed_query("test")
            if len(sample_embedding) != 1536:
                raise ValueError(f"Embedding dimension mismatch: expected 1536, got {len(sample_embedding)}")
            else:
                logger.info("Embedding dimension verified as 1536.")

            # Update the docuquery collection metadata
            self.docuquery_collection = self.client.get_or_create_collection(
                name="docuquery",
                metadata={"dimension": 1536, "space": "cosine"}
            )
            logger.info(f"Successfully initialized ChromaDB connection with collection: docuquery")
        except Exception as e:
            logger.error(f"Error initializing DB connector: {str(e)}")
            raise
            
    async def store_documents(self, doc_id: str, documents: List[Document]):
        try:
            # Get or create the collection for the given doc_id
            collection = self.get_or_create_collection(doc_id)

            # Use the self.embeddings instance
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

            # Use the self.embeddings instance
            db_for_query = Chroma(
                client=self.client,
                collection_name=collection_id,
                embedding_function=self.embeddings
            )

            # Query using the underlying collection
            results = collection.query(
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

    def get_collection(
        self,
        name: str,
        embedding_function: Optional[EmbeddingFunction[Embeddable]] = None,
        data_loader: Optional[DataLoader[Loadable]] = None,
    ) -> LangChainChroma:
        if embedding_function is None:
            embedding_function = self.embeddings
        return LangChainChroma(
            collection_name=name,
            embedding_function=embedding_function,
            persist_directory=None,  # or your persist directory if needed
        )

    def get_or_create_collection(self, collection_id: str):
        try:
            return self.client.get_collection(collection_id)
        except Exception:
            # Create collection with explicit dimension
            return self.client.create_collection(
                name=collection_id,
                metadata={"dimension": 1536, "space": "cosine"}
            )

    def reset_collection(self):
        try:
            self.client.reset()
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"dimension": 1536, "space": "cosine"}
            )
            logger.info(f"Chroma collection reset successfully for {self.collection_name}")
        except Exception as e:
            logger.error(f"Error resetting Chroma collection: {str(e)}")
            raise
