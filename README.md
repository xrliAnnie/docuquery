# docuquery# Document Query System

A powerful RAG (Retrieval-Augmented Generation) system that allows users to upload documents and query them using natural language. The system uses ChromaDB for vector storage and OpenAI's GPT model for generating responses.

## Features

- **Document Processing**: Supports multiple file formats (PDF, DOCX, TXT)
- **Smart Text Chunking**: Implements recursive character text splitting for optimal context preservation
- **Vector Storage**: Uses ChromaDB for efficient vector storage and retrieval
- **RAG Implementation**: Combines ChromaDB retrieval with OpenAI's GPT for accurate answers
- **REST API**: FastAPI-based endpoints for document upload and querying

## Technical Stack

- **Backend Framework**: FastAPI
- **Vector Database**: ChromaDB
- **Language Model**: OpenAI GPT-3.5-turbo
- **Embeddings**: OpenAI text-embedding-ada-002
- **Document Processing**: PyPDF2, python-docx
- **Container Platform**: Docker

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API Key

### Environment Setup

1. Clone the repository: