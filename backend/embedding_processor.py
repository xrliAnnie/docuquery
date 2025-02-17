from typing import List
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
import os

class EmbeddingProcessor:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def create_embeddings(self, chunks: List[str], metadata: dict) -> List[Document]:
        """Convert text chunks to Document objects with embeddings"""
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
        """Process text chunks into embeddings asynchronously"""
        try:
            documents = self.create_embeddings(chunks, metadata)
            return documents
        except Exception as e:
            raise Exception(f"Error creating embeddings: {str(e)}")