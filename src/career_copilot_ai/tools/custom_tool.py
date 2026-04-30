import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
import json
import os
from pydantic import BaseModel, Field
from typing import Type, List
try:
    import faiss
    import numpy as np
except ImportError:
    faiss = None

class GoogleEmbedder:
    def __init__(self):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from dotenv import load_dotenv
        import os
        load_dotenv()
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        self.model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        
    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.embed_documents(texts)
        return np.array(embeddings).astype('float32')

try:
    embedder = GoogleEmbedder()
except Exception as e:
    print(f"Failed to load Google Embedder: {e}")
    embedder = None

class TopJobsScraperInput(BaseModel):
    """Input schema for TopJobsScraperTool."""
    url: str = Field(..., description="The URL of the website to scrape for jobs.")
    resume_text: str = Field(..., description="The text of the user's resume to match against.")

class TopJobsScraperTool(BaseTool):
    name: str = "top_jobs_scraper_tool"
    description: str = "Scrapes a URL, chunks the text, and uses FAISS semantic search to return the most relevant job chunks matching the resume."
    args_schema: Type[BaseModel] = TopJobsScraperInput

    def _run(self, url: str, resume_text: str) -> str:
        if not embedder or not faiss:
            return "Error: SentenceTransformer or FAISS failed to load. Please install dependencies."
            
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            for element in soup(["script", "style", "nav", "footer", "noscript"]):
                element.extract()
                
            text_content = soup.get_text(separator='\n\n', strip=True)
            
            # Simple heuristic: split by double newlines to create chunks
            raw_chunks = text_content.split('\n\n')
            
            # Filter out very short chunks (e.g. menu items) and very long ones
            valid_chunks = [c.strip() for c in raw_chunks if 50 < len(c.strip()) < 2000]
            
            if not valid_chunks:
                 return f"No valid job text found on {url}"
                 
            # Create FAISS index
            chunk_embeddings = embedder.encode(valid_chunks)
            d = chunk_embeddings.shape[1]
            index = faiss.IndexFlatL2(d)
            index.add(chunk_embeddings)
            
            # Embed resume and search
            resume_embedding = embedder.encode([resume_text])
            k = min(5, len(valid_chunks)) # Top 5 per site
            distances, indices = index.search(resume_embedding, k)
            
            # Save the index and metadata to disk for the chatbot to use
            try:
                # Load existing if any to append, but for simplicity we overwrite or just keep the last one.
                # A better approach is to have a global index, but we'll overwrite for the demo.
                faiss.write_index(index, 'jobs_index.faiss')
                with open('jobs_metadata.json', 'w', encoding='utf-8') as f:
                    json.dump(valid_chunks, f)
            except Exception as e:
                print(f"Warning: Failed to save FAISS index: {e}")

            top_chunks = []
            for i in indices[0]:
                if i != -1:
                    top_chunks.append(valid_chunks[i])
                    
            return f"Top matches from {url}:\n\n" + "\n---\n".join(top_chunks)
            
        except Exception as e:
            return f"Failed to scrape or process {url}. Error: {str(e)}"

class VectorDBQueryInput(BaseModel):
    """Input schema for VectorDBQueryTool."""
    query: str = Field(..., description="The user's question or search query to find relevant jobs.")

class VectorDBQueryTool(BaseTool):
    name: str = "vector_db_query_tool"
    description: str = "Queries the saved FAISS vector database to find job descriptions and details that answer the user's question."
    args_schema: Type[BaseModel] = VectorDBQueryInput

    def _run(self, query: str) -> str:
        if not embedder or not faiss:
            return "Error: Dependencies not loaded."
            
        if not os.path.exists('jobs_index.faiss') or not os.path.exists('jobs_metadata.json'):
            return "Error: No job data found. Please run the job scraper first."
            
        try:
            index = faiss.read_index('jobs_index.faiss')
            with open('jobs_metadata.json', 'r', encoding='utf-8') as f:
                valid_chunks = json.load(f)
                
            query_embedding = embedder.encode([query])
            k = min(3, len(valid_chunks))
            distances, indices = index.search(query_embedding, k)
            
            results = []
            for i in indices[0]:
                if i != -1:
                    results.append(valid_chunks[i])
                    
            return "Relevant Job Information found:\n\n" + "\n---\n".join(results)
        except Exception as e:
            return f"Failed to query database. Error: {str(e)}"
