from typing import List
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
import os

class EmbeddingProcessor:
    """Processes documents into embeddings using OpenAI's embedding model.
    
    This class handles document loading, text splitting, and embedding generation
    using OpenAI's embedding model through LangChain's interface. It supports
    PDF and DOCX files, with appropriate chunking and overlap for context preservation.
    """

    def __init__(self):
        """Initialize the embedding processor with OpenAI credentials and text splitter."""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="text-embedding-ada-002",  # Make the model explicit
            chunk_size=1000  # Process 1000 texts at a time for efficiency
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,  # 10% overlap
            length_function=len,
            is_separator_regex=False,
        )

    def load_document(self, file_path: str) -> List[Document]:
        """Load document from file path using appropriate loader.
        
        Args:
            file_path: Path to the document file (PDF or DOCX)
            
        Returns:
            List of Document objects from the file
            
        Raises:
            ValueError: If file type is not supported
        """
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = UnstructuredWordDocumentLoader(file_path)
        else:
            raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")
        
        return loader.load()

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

    async def process_document(self, file_path: str, metadata: dict) -> List[Document]:
        """Process a document file into embeddings asynchronously.
        
        Args:
            file_path: Path to the document file
            metadata: Dictionary of metadata to be attached to each document
                     Should include at minimum: {'doc_name': filename}
            
        Returns:
            List of Document objects with embeddings
            
        Raises:
            Exception: If there's an error during processing
        """
        try:
            # Load the document
            documents = self.load_document(file_path)
            
            # Split the documents into chunks
            split_docs = self.text_splitter.split_documents(documents)
            
            # Generate embeddings for all documents
            embeddings = self.embeddings.embed_documents([doc.page_content for doc in split_docs])
            
            # Attach embeddings and additional metadata to documents
            for i, (doc, embedding) in enumerate(zip(split_docs, embeddings)):
                # Get the page number from the document if available
                page = doc.metadata.get('page', None)
                
                doc.metadata.update({
                    **metadata,
                    'embedding': embedding,
                    'chunk_index': i,
                    'page': page,
                    'text_chunk': doc.page_content  # Add the text chunk to metadata for easy access
                })
                
            return split_docs
        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")

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
            embeddings = self.embeddings.embed_documents([doc.page_content for doc in documents])
            
            # Attach embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.metadata['embedding'] = embedding
                doc.metadata['text_chunk'] = doc.page_content
                
            return documents
        except Exception as e:
            raise Exception(f"Error creating embeddings: {str(e)}")