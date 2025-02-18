from typing import BinaryIO, Dict, Any, List
from PyPDF2 import PdfReader
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import mimetypes
import logging

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

        Args:
            chunk_size (int): The size of text chunks (in characters)
            chunk_overlap (int): The overlap between chunks to maintain context
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""] # Order from most to least preferred split points
        )
        logger.info(f"Initialized DocumentLoader with chunk_size={chunk_size}, overlap={chunk_overlap}")

    def validate_file(self, file: BinaryIO, filename: str) -> None:
        """
        Validate file type by extension and MIME type.

        Args:
            file (BinaryIO): File object to validate
            filename (str): Name of the file with extension

        Raises:
            ValueError: If file type is unsupported or invalid
        """
        ext = self._get_file_extension(filename)
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: {ext}. Supported types: {', '.join(self.SUPPORTED_EXTENSIONS)}")

        mime_type = mimetypes.guess_type(filename)[0]
        if not mime_type or mime_type not in self.SUPPORTED_MIMETYPES:
            raise ValueError(f"Invalid MIME type: {mime_type}")

        if self.SUPPORTED_MIMETYPES[mime_type] != ext:
            raise ValueError(f"File extension {ext} does not match content type {mime_type}")

        logger.debug(f"File validation successful for {filename}")

    def _get_file_extension(self, filename: str) -> str:
        """
        Extract and validate file extension.

        Args:
            filename (str): Name of the file

        Returns:
            str: Lowercase file extension with dot (e.g., '.pdf')
        """
        return '.' + filename.split('.')[-1].lower() if '.' in filename else ''

    def load_pdf(self, file: BinaryIO) -> List[str]:
        """
        Extract text from PDF file and split into chunks.

        Args:
            file (BinaryIO): PDF file object

        Returns:
            List[str]: List of text chunks

        Raises:
            Exception: If PDF parsing fails
        """
        try:
            pdf = PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text.strip():  # Only add non-empty pages
                    text += f"\n\nPage {page_num}:\n{page_text}"
            
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Successfully extracted {len(chunks)} chunks from PDF with {len(pdf.pages)} pages")
            return chunks
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    def load_docx(self, file: BinaryIO) -> List[str]:
        """
        Extract text from DOCX file and split into chunks.

        Args:
            file (BinaryIO): DOCX file object

        Returns:
            List[str]: List of text chunks

        Raises:
            Exception: If DOCX parsing fails
        """
        try:
            doc = Document(file)
            text = ""
            for para in doc.paragraphs:
                if para.text.strip():  # Only add non-empty paragraphs
                    text += para.text + "\n"
            
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Successfully extracted {len(chunks)} chunks from DOCX")
            return chunks
        except Exception as e:
            logger.error(f"Error processing DOCX: {str(e)}")
            raise

    def load_txt(self, file: BinaryIO) -> List[str]:
        """
        Extract text from TXT file and split into chunks.

        Args:
            file (BinaryIO): TXT file object

        Returns:
            List[str]: List of text chunks

        Raises:
            Exception: If text file processing fails
        """
        try:
            text = file.read().decode('utf-8')
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Successfully extracted {len(chunks)} chunks from TXT")
            return chunks
        except UnicodeDecodeError:
            logger.error("Error decoding text file - trying with different encoding")
            file.seek(0)  # Reset file pointer
            text = file.read().decode('latin-1')  # Try alternative encoding
            chunks = self.text_splitter.split_text(text)
            return chunks
        except Exception as e:
            logger.error(f"Error processing TXT: {str(e)}")
            raise

    def process_document(self, file: BinaryIO, filename: str) -> Dict[str, Any]:
        """
        Process document based on file type and return chunks with metadata.

        Args:
            file (BinaryIO): File object to process
            filename (str): Name of the file with extension

        Returns:
            Dict containing:
            - chunks: List of text chunks
            - metadata: Dict with source filename and chunk count

        Raises:
            ValueError: If file validation fails
            Exception: If document processing fails
        """
        logger.info(f"Starting document processing for {filename}")
        self.validate_file(file, filename)
        
        ext = self._get_file_extension(filename)
        try:
            if ext == '.pdf':
                chunks = self.load_pdf(file)
            elif ext == '.docx':
                chunks = self.load_docx(file)
            elif ext == '.txt':
                chunks = self.load_txt(file)
            else:
                raise ValueError(f"Unsupported file type: {ext}")

            result = {
                "chunks": chunks,
                "metadata": {
                    "source": filename,
                    "chunk_count": len(chunks),
                    "file_type": ext[1:],  # Remove the dot from extension
                }
            }
            logger.info(f"Document processing completed for {filename}: {len(chunks)} chunks created")
            return result

        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            raise