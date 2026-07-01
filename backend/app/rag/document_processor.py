from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    Docx2txtLoader, 
    CSVLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

class DocumentProcessor:
    """
    Handles parsing and chunking of uploaded documents (PDF, TXT, DOCX, MD, CSV)
    """
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def load_document(self, file_path: str):
        """
        Dynamically selects the right loader based on file extension.
        """
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext == ".txt":
            loader = TextLoader(file_path)
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif ext == ".csv":
            loader = CSVLoader(file_path)
        elif ext == ".md":
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
            
        return loader.load()

    def process_and_chunk(self, file_path: str):
        """
        Loads the document and splits it into manageable chunks for embedding.
        """
        docs = self.load_document(file_path)
        chunks = self.text_splitter.split_documents(docs)
        return chunks
