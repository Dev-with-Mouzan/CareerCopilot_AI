from langchain_community.document_loaders import PyPDFLoader
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import os

class MatchForgeUtils:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def parse_resume(self, file_path):
        """Extract text from PDF using LangChain + PyPDFLoader."""
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        return " ".join([p.page_content for p in pages])

    def fetch_jobs(self, query):
        """Fetch live jobs from JSearch (RapidAPI)."""
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": os.getenv("X_RAPIDAPI_KEY"),
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        params = {"query": query, "num_pages": "1"}
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('data', [])

    def rank_jobs(self, resume_text, jobs):
        """Calculate cosine similarity between resume and job descriptions."""
        # Semantic matching logic here
        pass
