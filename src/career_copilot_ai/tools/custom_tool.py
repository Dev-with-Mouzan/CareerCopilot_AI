import re
import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
import json
import os
from pydantic import BaseModel, Field
from typing import Optional, Type, List
from urllib.parse import quote_plus

# ---------------------------------------------------------------------------
# TF-IDF based semantic matching (no API key, no model download needed)
# ---------------------------------------------------------------------------
# custom_tool.py lives at: src/career_copilot_ai/tools/custom_tool.py
# Going up 3 levels reaches the project root: MatchForge-AI/
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_DB_DIR = os.path.join(_PROJECT_ROOT, "data")
os.makedirs(_DB_DIR, exist_ok=True)
JOBS_CHUNKS_PATH = os.path.join(_DB_DIR, "jobs_chunks.json")

print(f"[TF-IDF] Data directory: {_DB_DIR}")

def _tfidf_top_matches(chunks: list, query: str, top_k: int = 5) -> list:
    """
    Return the top_k chunks most similar to query using TF-IDF cosine similarity.
    Pure Python/sklearn — no API key or model download required.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    if not chunks:
        return []

    corpus = chunks + [query]
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except Exception:
        # Fallback: return first top_k chunks if vectorizer fails
        return chunks[:top_k]

    query_vec   = tfidf_matrix[-1]       # last row = query
    chunk_vecs  = tfidf_matrix[:-1]      # all rows except last = chunks
    scores      = cosine_similarity(query_vec, chunk_vecs)[0]
    top_indices = scores.argsort()[::-1][:top_k]
    return [chunks[i] for i in top_indices if scores[i] > 0]


class TopJobsScraperInput(BaseModel):
    """Input schema for TopJobsScraperTool."""
    url: str = Field(..., description="The URL of the website to scrape for jobs.")
    search_query: str = Field(..., description="The keywords or skills from the resume to match against the scraped content.")

class TopJobsScraperTool(BaseTool):
    name: str = "top_jobs_scraper_tool"
    description: str = "Scrapes a URL, chunks the text, and uses TF-IDF to return the most relevant job chunks matching the resume."
    args_schema: Type[BaseModel] = TopJobsScraperInput

    def _run(self, url: str, search_query: str) -> str:
        import time
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
            max_retries = 3
            response = None
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        raise e

            soup = BeautifulSoup(response.content, 'html.parser')
            for element in soup(["script", "style", "nav", "footer", "noscript"]):
                element.extract()

            text_content = soup.get_text(separator='\n\n', strip=True)
            raw_chunks   = text_content.split('\n\n')
            valid_chunks = [c.strip() for c in raw_chunks if 50 < len(c.strip()) < 2000]

            if not valid_chunks:
                return f"No valid job text found on {url}"

            # Save chunks for VectorDBQueryTool
            try:
                existing = []
                if os.path.exists(JOBS_CHUNKS_PATH):
                    with open(JOBS_CHUNKS_PATH, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                existing.extend(valid_chunks)
                with open(JOBS_CHUNKS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(existing, f)
                print(f"[TF-IDF] Saved {len(valid_chunks)} chunks from {url}")
            except Exception as e:
                print(f"Warning: Failed to save chunks: {e}")

            # TF-IDF matching using search query
            top_chunks = _tfidf_top_matches(valid_chunks, search_query, top_k=5)
            return f"Top matches from {url}:\n\n" + "\n---\n".join(top_chunks)

        except Exception as e:
            return f"Failed to scrape or process {url}. Error: {str(e)}"

class VectorDBQueryInput(BaseModel):
    """Input schema for VectorDBQueryTool."""
    query: str = Field(..., description="The user's question or search query to find relevant jobs.")

class VectorDBQueryTool(BaseTool):
    name: str = "vector_db_query_tool"
    description: str = "Queries the saved job chunks using TF-IDF to find job descriptions relevant to the user's question."
    args_schema: Type[BaseModel] = VectorDBQueryInput

    def _run(self, query: str) -> str:
        if not os.path.exists(JOBS_CHUNKS_PATH):
            return f"Error: No job data found at {JOBS_CHUNKS_PATH}. Please run the job scraper first."

        try:
            with open(JOBS_CHUNKS_PATH, 'r', encoding='utf-8') as f:
                all_chunks = json.load(f)

            if not all_chunks:
                return "Error: Job database is empty. Please run the scraper first."

            top_chunks = _tfidf_top_matches(all_chunks, query, top_k=3)
            if not top_chunks:
                return "No relevant job information found for your query."

            return "Relevant Job Information found:\n\n" + "\n---\n".join(top_chunks)
        except Exception as e:
            return f"Failed to query job database. Error: {str(e)}"


# ---------------------------------------------------------------------------
# Remotive Public API Tool (replaces blocked HTML scrape of remotive.com)
# ---------------------------------------------------------------------------

class RemotiveAPIInput(BaseModel):
    """Input schema for RemotiveAPITool."""
    search_query: str = Field(
        ...,
        description="The job title or keywords to search for (e.g. 'Python Developer')."
    )
    limit: Optional[int] = Field(
        default=10,
        description="Maximum number of jobs to return (default: 10)."
    )

class RemotiveAPITool(BaseTool):
    name: str = "remotive_api_tool"
    description: str = (
        "Fetches remote job listings from Remotive's free public API "
        "(https://remotive.com/api/remote-jobs). "
        "Automatically extracts keywords from the user's resume to filter results."
    )
    args_schema: Type[BaseModel] = RemotiveAPIInput

    def _run(self, search_query: str, limit: int = 10) -> str:
        # Use provided query or fallback
        search_term = search_query if search_query else "remote"

        url = f"https://remotive.com/api/remote-jobs?search={quote_plus(search_term)}&limit={limit}"

        import time
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                data = response.json()
                break
            except requests.RequestException as exc:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return f"Remotive API request failed: {exc}"
            except ValueError:
                return "Remotive API returned non-JSON response."

        jobs = data.get("jobs", [])
        if not jobs:
            return f"No jobs found on Remotive for keywords: '{search_term}'"

        results = []
        for job in jobs[:limit]:
            title       = job.get("title", "N/A")
            company     = job.get("company_name", "N/A")
            category    = job.get("category", "N/A")
            job_type    = job.get("job_type", "N/A")
            location    = job.get("candidate_required_location", "Worldwide")
            url_link    = job.get("url", "N/A")
            results.append(
                f"**{title}** at {company}\n"
                f"Category: {category} | Type: {job_type} | Location: {location}\n"
                f"Link: {url_link}\n"
            )

        header = (
            f"Remotive Jobs — Keywords: '{search_term}'\n"
            f"Found {len(results)} job(s):\n\n"
        )
        return header + "\n---\n".join(results)


# ---------------------------------------------------------------------------
# Jobicy Public API Tool (replaces timed-out HTML scrape of remote.co)
# API docs: https://jobicy.com/jobs-rss-feed
# ---------------------------------------------------------------------------

class JobicyAPIInput(BaseModel):
    """Input schema for JobicyAPITool."""
    search_tag: str = Field(
        ...,
        description="The job category or tag to search for (e.g. 'software', 'dev', 'marketing')."
    )
    count: Optional[int] = Field(
        default=10,
        description="Maximum number of jobs to return (default: 10, max: 50)."
    )

class JobicyAPITool(BaseTool):
    name: str = "jobicy_api_tool"
    description: str = (
        "Fetches remote job listings from Jobicy's free public API "
        "(https://jobicy.com/api/v2/remote-jobs). "
        "Automatically extracts keywords from the resume to filter results."
    )
    args_schema: Type[BaseModel] = JobicyAPIInput

    def _run(self, search_tag: str, count: int = 10) -> str:
        tag = search_tag.split()[0] if search_tag else "software"  # Jobicy uses single tag

        url = f"https://jobicy.com/api/v2/remote-jobs?count={count}&tag={quote_plus(tag)}"

        import time
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                data = response.json()
                break
            except requests.RequestException as exc:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return f"Jobicy API request failed: {exc}"
            except ValueError:
                return "Jobicy API returned non-JSON response."

        jobs = data.get("jobs", [])
        if not jobs:
            # Fallback: fetch without tag filter
            try:
                fallback_url = f"https://jobicy.com/api/v2/remote-jobs?count={count}"
                for attempt in range(max_retries):
                    try:
                        r2 = requests.get(fallback_url, timeout=20)
                        jobs = r2.json().get("jobs", [])
                        break
                    except Exception:
                        if attempt < max_retries - 1:
                            time.sleep(2)
                        else:
                            raise
            except Exception:
                return f"No jobs found on Jobicy for tag: '{tag}'"

        results = []
        for job in jobs[:count]:
            title    = job.get("jobTitle", "N/A")
            company  = job.get("companyName", "N/A")
            industry = job.get("jobIndustry", ["N/A"])
            if isinstance(industry, list):
                industry = ", ".join(industry)
            location = job.get("jobGeo", "Worldwide")
            link     = job.get("url", "N/A")
            results.append(
                f"**{title}** at {company}\n"
                f"Industry: {industry} | Location: {location}\n"
                f"Link: {link}\n"
            )

        header = (
            f"Jobicy Jobs — Tag: '{tag}'\n"
            f"Found {len(results)} job(s):\n\n"
        )
        return header + "\n---\n".join(results)


# ---------------------------------------------------------------------------
# LinkedIn Guest API Job Scraper
# ---------------------------------------------------------------------------

def _extract_keywords_from_resume(resume_text: str, max_keywords: int = 5) -> str:
    """
    Extract the most relevant job-search keywords from resume text.
    Strategy: strip common stop-words and punctuation, then return the
    most frequent meaningful tokens joined by '+' for the LinkedIn API.
    """
    stop_words = {
        'the','and','for','with','from','that','this','have','has','are',
        'was','were','been','will','can','may','which','also','their','our',
        'not','all','any','but','such','more','into','than','over','each',
        'your','your','we','as','at','by','to','of','in','on','or','is',
        'a','an','be','do','if','it','no','so','up','us','my',
    }
    tokens = re.findall(r'[A-Za-z][A-Za-z+#.]{2,}', resume_text)
    freq: dict = {}
    for tok in tokens:
        word = tok.lower()
        if word not in stop_words and len(word) > 3:
            freq[word] = freq.get(word, 0) + 1

    # Sort by frequency descending, take top keywords
    sorted_words = sorted(freq, key=lambda w: freq[w], reverse=True)
    keywords = sorted_words[:max_keywords]
    return ' '.join(keywords)  # LinkedIn API accepts space-separated terms


class LinkedInJobsInput(BaseModel):
    """Input schema for LinkedInJobsScraperTool."""
    search_query: str = Field(
        ...,
        description="The job title or keywords to search for (e.g. 'Senior Python Engineer')."
    )
    location: Optional[str] = Field(
        default="United States",
        description="The location to search jobs in (default: United States)."
    )
    # NOTE: 'start' (pagination) removed — Groq tool schema requires all non-Optional
    # fields to be passed explicitly; we don't need pagination for single-shot calls.


class LinkedInJobsScraperTool(BaseTool):
    name: str = "linkedin_jobs_scraper_tool"
    description: str = (
        "Searches LinkedIn for job postings that match the user's resume. "
        "Automatically extracts keywords from the resume and queries the "
        "LinkedIn Guest Jobs API to return relevant listings."
    )
    args_schema: Type[BaseModel] = LinkedInJobsInput

    def _run(self, search_query: str, location: Optional[str] = "United States") -> str:
        # 1. Use the provided search query
        keywords = search_query
        if not keywords:
            return "No search query provided."

        loc = location or "United States"

        # 2. Build the LinkedIn Guest API URL (start=0, first page only)
        encoded_keywords = quote_plus(keywords)
        encoded_location = quote_plus(loc)
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={encoded_keywords}&location={encoded_location}&start=0"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        import time
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return f"LinkedIn request failed: {exc}"

        # 3. Parse the HTML cards returned by LinkedIn's guest API
        soup = BeautifulSoup(response.text, "html.parser")
        job_cards = soup.find_all("div", class_="base-card")

        if not job_cards:
            # Fallback: return raw text snippet so the agent still has something
            raw = soup.get_text(separator="\n", strip=True)[:3000]
            return (
                f"LinkedIn search URL: {url}\n"
                f"Keywords used: {keywords}\n"
                f"No structured job cards found. Raw page snippet:\n{raw}"
            )

        results = []
        for card in job_cards[:10]:  # Limit to 10 jobs per page
            title_el  = card.find("h3", class_="base-search-card__title")
            company_el = card.find("h4", class_="base-search-card__subtitle")
            location_el = card.find("span", class_="job-search-card__location")
            link_el   = card.find("a", class_="base-card__full-link")

            title    = title_el.get_text(strip=True)   if title_el   else "N/A"
            company  = company_el.get_text(strip=True) if company_el else "N/A"
            loc      = location_el.get_text(strip=True) if location_el else "N/A"
            link     = link_el["href"]                 if link_el    else "N/A"

            results.append(
                f"**{title}** at {company}\n"
                f"Location: {loc}\n"
                f"Link: {link}\n"
            )

        header = (
            f"LinkedIn Jobs — Keywords: '{keywords}' | Location: {location}\n"
            f"URL: {url}\n"
            f"Found {len(results)} job(s):\n\n"
        )
        return header + "\n---\n".join(results)
