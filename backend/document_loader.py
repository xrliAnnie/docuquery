from typing import BinaryIO, Dict, Any
from PyPDF2 import PdfReader
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import mimetypes

class DocumentLoader:
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
    SUPPORTED_MIMETYPES = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'text/plain': '.txt'
    }

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

    def validate_file(self, file: BinaryIO, filename: str) -> None:
        """Validate file type by extension and MIME type"""
        ext = self._get_file_extension(filename)
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported file type. Please upload a PDF, DOCX, or TXT file.")

        mime_type = mimetypes.guess_type(filename)[0]
        if not mime_type or mime_type not in self.SUPPORTED_MIMETYPES:
            raise ValueError("Invalid file format. Please ensure the file is a valid PDF, DOCX, or TXT file.")

        if self.SUPPORTED_MIMETYPES[mime_type] != ext:
            raise ValueError("File extension does not match its content type.")

    def _get_file_extension(self, filename: str) -> str:
        """Extract and validate file extension"""
        return '.' + filename.split('.')[-1].lower() if '.' in filename else ''

    def load_pdf(self, file: BinaryIO) -> list[str]:
        """Extract text from PDF file and split into chunks"""
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
        return self.text_splitter.split_text(text)

    def load_docx(self, file: BinaryIO) -> list[str]:
        """Extract text from DOCX file and split into chunks"""
        doc = Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return self.text_splitter.split_text(text)

    def load_txt(self, file: BinaryIO) -> list[str]:
        """Extract text from TXT file and split into chunks"""
        text = file.read().decode('utf-8')
        return self.text_splitter.split_text(text)

    def process_document(self, file: BinaryIO, filename: str) -> Dict[str, Any]:
        """Process document based on file type"""
        self.validate_file(file, filename)
        
        ext = self._get_file_extension(filename)
        if ext == '.pdf':
            chunks = self.load_pdf(file)
        elif ext == '.docx':
            chunks = self.load_docx(file)
        elif ext == '.txt':
            chunks = self.load_txt(file)
        else:
            raise ValueError("Unsupported file type. Please upload a PDF, DOCX, or TXT file.")

        return {
            "chunks": chunks,
            "metadata": {
                "source": filename,
                "chunk_count": len(chunks)
            }
        }