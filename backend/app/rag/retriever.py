from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config.settings import settings
import os

class RAGRetriever:
    """
    Manages the FAISS Vector Database for Document Retrieval.
    """
    def __init__(self, index_name: str = "modelrouter_faiss"):
        self.index_name = index_name
        self.index_path = f"app/database/{self.index_name}"
        
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for embedding documents.")
            
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )
        self.vector_store = None

    def ingest_documents(self, chunks):
        """
        Embeds chunks and adds them to the FAISS index.
        """
        if os.path.exists(self.index_path):
            self.vector_store = FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
            self.vector_store.add_documents(chunks)
        else:
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            
        # Save locally so it persists between restarts
        self.vector_store.save_local(self.index_path)

    def retrieve_context(self, query: str, k: int = 4) -> str:
        """
        Searches the FAISS index for the top k most relevant chunks.
        """
        if not self.vector_store:
            if os.path.exists(self.index_path):
                self.vector_store = FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
            else:
                return "" # No documents ingested yet
                
        results = self.vector_store.similarity_search(query, k=k)
        
        # Combine the chunks into a single context string
        context = "\n\n".join([f"Document Content:\n{doc.page_content}" for doc in results])
        return context
