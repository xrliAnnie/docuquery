from typing import List
from langchain.docstore.document import Document
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import os

class DBConnector:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.db = Chroma(
            persist_directory="./data",
            embedding_function=self.embeddings,
            client_settings=Settings(
                anonymized_telemetry=False
            )
        )

    async def store_documents(self, documents: List[Document]) -> str:
        """Store documents in Chroma DB and return collection ID"""
        try:
            collection_id = self.db.add_documents(documents)
            self.db.persist()
            return collection_id
        except Exception as e:
            raise Exception(f"Error storing documents: {str(e)}")

    async def get_collection(self, collection_id: str):
        """Retrieve a collection by ID"""
        try:
            return self.db.get(collection_id)
        except Exception as e:
            raise Exception(f"Error retrieving collection: {str(e)}")