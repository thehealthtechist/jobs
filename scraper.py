import json
import re
from datetime import datetime
import requests

# 1. Target Healthtech Companies (Greenhouse & Lever Board Names)
GREENHOUSE_COMPANIES = [
    {"name": "Ro", "board": "ro"},
    {"name": "Komodo Health", "board": "komodohealth"},
    {"name": "Color", "board": "color"},
    {"name": "Virta Health", "board": "virtahealth"},
    {"name": "Spring Health", "board": "springhealth"},
]

LEVER_COMPANIES = [
    {"name": "Hims & Hers", "board": "hims"},
    {"name": "Modern Health", "board": "modernhealth"},
]

# Keywords to auto-assign categories
CATEGORIES = {
    "Health AI": ["ai", "machine learning", "data scientist", "llm", "nlp", "algorithm"],
    "Clinical Informatics": ["informatics", "clinical", "ehr", "epic", "fhir", "hl7", "medical"],
    "Product & Engineering": ["product manager", "engineer", "software", "frontend", "backend", "full stack", "developer"],
    "Operations": ["operations", "ops", "credentialing", "implementation", "customer success", "manager"]
}

def categorize_role(title):
    """Categorize job based on title keywords."""
    title_lower = title.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return "Operations"  # Default fallback

def fetch_greenhouse_jobs(company_name, board_token):
    """Fetch listings from Greenhouse public API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    jobs = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for job in data.get("jobs", []):
                title = job.get("title", "")
                category = categorize_role(title)
                
                # Format job entry
                jobs.append({
                    "id": job.get("id"),
                    "title": title,
                    "company": company_name,
                    "location": job.get("location", {}).get("name", "Remote / Various"),
                    "category": category,
                    "type": "Full-Time",
                    "posted": "Recently",
                    "source": "Greenhouse",
                    "applyUrl": job.get("absolute_url", ""),
                    "description": clean_html(job.get("content", ""))[:200] + "..."
                })
    except Exception as e:
        print(f"Error fetching Greenhouse for {company_name}: {e}")
    return jobs

def fetch_lever_jobs(company_name, board_token):
    """Fetch listings from Lever public API."""
    url = f"https://api.lever.co/v0/postings/{board_token}"
    jobs = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            postings = response.json()
            for job in postings:
                title = job.get("text", "")
                category = categorize_role(title)
                
                categories_data = job.get("categories", {})
                location = categories_data.get("location", "Remote")
                commitment = categories_data.get("commitment", "Full-Time")

                jobs.append({
                    "id": job.get("id"),
                    "title": title,
                    "company": company_name,
                    "location": location,
                    "category": category,
                    "type": commitment,
                    "posted": "Recently",
                    "source": "Lever",
                    "applyUrl": job.get("hostedUrl", ""),
                    "description": job.get("descriptionPlain", "")[:200] + "..."
                })
    except Exception as e:
        print(f"Error fetching Lever for {company_name}: {e}")
    return jobs

def clean_html(raw_html):
    """Strip HTML tags for cleaner descriptions."""
    clean_text = re.sub('<[^<]+?>', '', raw_html)
    return clean_text.strip().replace('\n', ' ')

def run_scraper():
    all_jobs = []
    
    # 1. Scraping Greenhouse Boards
    for company in GREENHOUSE_COMPANIES:
        print(f"Fetching {company['name']} (Greenhouse)...")
        all_jobs.extend(fetch_greenhouse_jobs(company["name"], company["board"]))

    # 2. Scraping Lever Boards
    for company in LEVER_COMPANIES:
        print(f"Fetching {company['name']} (Lever)...")
        all_jobs.extend(fetch_lever_jobs(company["name"], company["board"]))

    # 3. Limit list to top 30 most recent roles & write to jobs.json
    all_jobs = all_jobs[:30]
    
    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully updated jobs.json with {len(all_jobs)} roles!")

if __name__ == "__main__":
    run_scraper()