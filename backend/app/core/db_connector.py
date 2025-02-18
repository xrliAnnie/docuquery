from typing import List
from langchain.docstore.document import Document
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import os
import logging

logger = logging.getLogger(__name__)

class DBConnector:
    def __init__(self):
        """Initialize the database connector with OpenAI embeddings"""
        try:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            
            # Create ChromaDB client
            client = chromadb.HttpClient(
                host="chroma",
                port=8000,
                ssl=False
            )

            self.db = Chroma(
                client=client,
                embedding_function=self.embeddings,
                collection_name="langchain"
            )
            logger.info("Successfully initialized ChromaDB connection")
        except Exception as e:
            logger.error(f"Error initializing DB connector: {str(e)}")
            raise

    async def store_documents(self, documents: List[Document]) -> str:
        """Store documents in Chroma DB and return collection ID"""
        try:
            collection_id = self.db.add_documents(documents)
            logger.info(f"Successfully stored {len(documents)} documents")
            return collection_id
        except Exception as e:
            logger.error(f"Error storing documents: {str(e)}")
            raise Exception(f"Error storing documents: {str(e)}")

    async def get_collection(self, collection_id: str):
        """Retrieve a collection by ID"""
        try:
            results = self.db.get(collection_id)
            logger.info(f"Successfully retrieved collection {collection_id}")
            return results
        except Exception as e:
            logger.error(f"Error retrieving collection: {str(e)}")
            raise Exception(f"Error retrieving collection: {str(e)}")

    async def query_documents(self, query: str, k: int = 4):
        """Query documents using similarity search"""
        try:
            docs = self.db.similarity_search(
                query,
                k=k  # Number of documents to return
            )
            logger.info(f"Successfully queried documents for: {query}")
            return docs
        except Exception as e:
            logger.error(f"Error querying documents: {str(e)}")
            raise Exception(f"Error querying documents: {str(e)}")