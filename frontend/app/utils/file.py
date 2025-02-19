from typing import Union
from streamlit.runtime.uploaded_file_manager import UploadedFile

def validate_file(file: Union[UploadedFile, None]) -> bool:
    """Validate uploaded file"""
    if file is None:
        return False
    
    # Check file size (50MB limit)
    MAX_SIZE_MB = 50
    if file.size > MAX_SIZE_MB * 1024 * 1024:
        st.error(f"File size exceeds {MAX_SIZE_MB}MB limit")
        return False
    
    # Check file type
    allowed_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain"
    }
    
    file_type = file.type
    if file_type not in allowed_types.values():
        st.error(f"Unsupported file type: {file_type}")
        return False
    
    return True