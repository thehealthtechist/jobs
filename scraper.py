import json
import os
import random
import re
import requests
from serpapi import GoogleSearch

# ==========================================
# 1. EXPANDED HEALTHTECH COMPANY DIRECTORY
# ==========================================
GREENHOUSE_COMPANIES = [
    "komodohealth", "ro", "color", "virtahealth", "springhealth",
    "doximity", "zocdoc", "headspace", "flatironhealth", "abridge",
    "tempus", "carbonhealth", "elationhealth", "oscarhealth", "vizai",
    "commure", "omadahealth", "lyrahealth", "hingehealth", "oakstreethealth"
]

LEVER_COMPANIES = [
    "hims", "modernhealth", "osmind", "ambiencehealthcare", 
    "hippocraticai", "strivehealth", "charliehealth"
]

# Max jobs to keep per individual company to maintain variety
MAX_JOBS_PER_COMPANY = 3

# ==========================================
# 2. CATEGORIZATION & KEYWORD MATCHING
# ==========================================
CATEGORIES = {
    "Health AI": ["ai", "machine learning", "data scientist", "llm", "nlp", "algorithm", "deep learning"],
    "Clinical Informatics": ["informatics", "clinical", "ehr", "epic", "fhir", "hl7", "medical director", "health data"],
    "Product & Engineering": ["product manager", "engineer", "software", "frontend", "backend", "full stack", "developer"],
    "Operations": ["operations", "ops", "credentialing", "implementation", "customer success", "care management"]
}

def categorize_role(title):
    title_lower = title.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return "Operations"

def clean_text(text):
    if not text:
        return ""
    clean = re.sub('<[^<]+?>', '', text)
    return clean.strip().replace('\n', ' ')[:200] + "..."

# ==========================================
# 3. GOOGLE JOBS SCRAPER
# ==========================================
def fetch_google_jobs(api_key):
    """Fetch live jobs from Google Jobs using SerpApi."""
    if not api_key:
        print("No SERPAPI_KEY found. Skipping Google Jobs fetch.")
        return []

    queries = [
        "Healthtech AI jobs",
        "Digital Health product manager jobs",
        "Healthcare operations jobs"
    ]
    
    google_jobs = []
    
    for query in queries:
        try:
            params = {
                "engine": "google_jobs",
                "q": query,
                "hl": "en",
                "api_key": api_key
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            jobs = results.get("jobs_results", [])
            
            for job in jobs[:5]: # Take top 5 per query
                title = job.get("title", "")
                google_jobs.append({
                    "id": job.get("job_id", str(random.randint(100000, 999999))),
                    "title": title,
                    "company": job.get("company_name", "Healthtech Company"),
                    "location": job.get("location", "Remote / US"),
                    "category": categorize_role(title),
                    "type": "Full-Time",
                    "posted": job.get("detected_extensions", {}).get("posted_at", "Recently"),
                    "source": "Google Jobs",
                    "applyUrl": job.get("related_links", [{}])[0].get("link", "https://google.com"),
                    "description": clean_text(job.get("description", ""))
                })
        except Exception as e:
            print(f"Error fetching Google Jobs for query '{query}': {e}")
            
    return google_jobs

# ==========================================
# 4. ATS BOARD SCRAPERS (GREENHOUSE & LEVER)
# ==========================================
def fetch_greenhouse_jobs(company_token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_token}/jobs?content=true"
    jobs = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            raw_jobs = data.get("jobs", [])
            for j in raw_jobs[:MAX_JOBS_PER_COMPANY]:
                title = j.get("title", "")
                jobs.append({
                    "id": j.get("id"),
                    "title": title,
                    "company": company_token.replace("-", " ").title(),
                    "location": j.get("location", {}).get("name", "Remote / Various"),
                    "category": categorize_role(title),
                    "type": "Full-Time",
                    "posted": "Recently",
                    "source": "Greenhouse",
                    "applyUrl": j.get("absolute_url", ""),
                    "description": clean_text(j.get("content", ""))
                })
    except Exception as e:
        print(f"Error fetching Greenhouse ({company_token}): {e}")
    return jobs

def fetch_lever_jobs(company_token):
    url = f"https://api.lever.co/v0/postings/{company_token}"
    jobs = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            postings = res.json()
            for j in postings[:MAX_JOBS_PER_COMPANY]:
                title = j.get("text", "")
                jobs.append({
                    "id": j.get("id"),
                    "title": title,
                    "company": company_token.title(),
                    "location": j.get("categories", {}).get("location", "Remote"),
                    "category": categorize_role(title),
                    "type": j.get("categories", {}).get("commitment", "Full-Time"),
                    "posted": "Recently",
                    "source": "Lever",
                    "applyUrl": j.get("hostedUrl", ""),
                    "description": clean_text(j.get("descriptionPlain", ""))
                })
    except Exception as e:
        print(f"Error fetching Lever ({company_token}): {e}")
    return jobs

# ==========================================
# 5. MAIN EXECUTION
# ==========================================
def run_scraper():
    all_jobs = []
    
    # 1. Google Jobs (optional API key from environment variables)
    serpapi_key = os.getenv("SERPAPI_KEY", "")
    google_jobs = fetch_google_jobs(serpapi_key)
    all_jobs.extend(google_jobs)

    # 2. Greenhouse Companies
    for company in GREENHOUSE_COMPANIES:
        all_jobs.extend(fetch_greenhouse_jobs(company))

    # 3. Lever Companies
    for company in LEVER_COMPANIES:
        all_jobs.extend(fetch_lever_jobs(company))

    # Shuffle so companies and categories are evenly mixed
    random.shuffle(all_jobs)

    # Cap total jobs shown at 40
    final_jobs = all_jobs[:40]

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(final_jobs, f, indent=2, ensure_ascii=False)

    print(f"Successfully wrote {len(final_jobs)} mixed jobs to jobs.json!")

if __name__ == "__main__":
    run_scraper()
