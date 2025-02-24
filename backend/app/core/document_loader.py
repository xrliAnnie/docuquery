from typing import BinaryIO, Dict, Any, List
from PyPDF2 import PdfReader
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import mimetypes
import logging
from fastapi import UploadFile
import io

logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    Handles document loading and text extraction for different file types.
    Supports PDF, DOCX, and TXT files with proper validation and chunking.
    """

    # Supported file types configuration
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
    SUPPORTED_MIMETYPES = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'text/plain': '.txt'
    }

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize the DocumentLoader with configurable chunking parameters.
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        logger.info(f"Initialized DocumentLoader with chunk_size={chunk_size}, overlap={chunk_overlap}")

    async def process_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Process uploaded file and return chunks with metadata.
        """
        logger.info(f"Starting document processing for {file.filename}")

        try:
            # Validate file and get the determined content type
            determined_content_type = await self.validate_file(file)

            # Read file content
            content = await file.read()

            # Process based on determined content type
            if determined_content_type == 'application/pdf':
                chunks = await self.load_pdf(io.BytesIO(content))
            elif determined_content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                chunks = await self.load_docx(io.BytesIO(content))
            elif determined_content_type == 'text/plain':
                chunks = await self.load_txt(io.BytesIO(content))
            else:
                raise ValueError(f"Unsupported content type: {determined_content_type}")

            result = {
                "chunks": chunks,
                "metadata": {
                    "source": file.filename,
                    "chunk_count": len(chunks),
                    "file_type": determined_content_type,
                }
            }

            logger.info(f"Document processing completed for {file.filename}: {len(chunks)} chunks created")
            return result

        except Exception as e:
            logger.error(f"Error processing document {file.filename}: {str(e)}")
            raise

    async def validate_file(self, file: UploadFile) -> str:
        """
        Validate file type by extension and MIME type.
        Returns the determined content type.
        """
        ext = self._get_file_extension(file.filename)
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension: {ext}. Supported types: {', '.join(self.SUPPORTED_EXTENSIONS)}")

        # Determine the content type in a local variable
        if not file.content_type:
            if ext == '.txt':
                determined_content_type = 'text/plain'
            elif ext == '.pdf':
                determined_content_type = 'application/pdf'
            elif ext == '.docx':
                determined_content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                raise ValueError(f"Could not determine content type for file: {file.filename}")
        else:
            determined_content_type = file.content_type

        if determined_content_type not in self.SUPPORTED_MIMETYPES:
            raise ValueError(f"Invalid content type: {determined_content_type}")

        if self.SUPPORTED_MIMETYPES[determined_content_type] != ext:
            raise ValueError(f"File extension {ext} does not match content type {determined_content_type}")

        logger.debug(f"File validation successful for {file.filename}")
        return determined_content_type

    def _get_file_extension(self, filename: str) -> str:
        """Extract and validate file extension."""
        return '.' + filename.split('.')[-1].lower() if '.' in filename else ''

    async def load_pdf(self, file: BinaryIO) -> List[str]:
        """Extract text from PDF file and split into chunks."""
        try:
            pdf = PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                # Add cleaning
                page_text = page_text.replace('\n', ' ').strip()
                if page_text:
                    text += f"Page {page_num}: {page_text}\n\n"
            return self.text_splitter.split_text(text)
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    async def load_docx(self, file: BinaryIO) -> List[str]:
        """Extract text from DOCX file and split into chunks."""
        try:
            doc = Document(file)
            text = ""
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"

            chunks = self.text_splitter.split_text(text)
            logger.info(f"Successfully extracted {len(chunks)} chunks from DOCX")
            return chunks
        except Exception as e:
            logger.error(f"Error processing DOCX: {str(e)}")
            raise

    async def load_txt(self, file: BinaryIO) -> List[str]:
        """Extract text from TXT file and split into chunks."""
        try:
            text = file.read().decode('utf-8')
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Successfully extracted {len(chunks)} chunks from TXT")
            return chunks
        except UnicodeDecodeError:
            logger.error("Error decoding text file - trying with different encoding")
            file.seek(0)
            text = file.read().decode('latin-1')
            chunks = self.text_splitter.split_text(text)
            return chunks
        except Exception as e:
            logger.error(f"Error processing TXT: {str(e)}")
            raise
