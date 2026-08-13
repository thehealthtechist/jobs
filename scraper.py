import json
import random
import re
from datetime import datetime, timezone
import requests

# ==========================================
# 1. EXPANDED HEALTHTECH DIRECTORY (35+ COMPANIES)
# ==========================================

# Greenhouse Boards
GREENHOUSE_COMPANIES = [
    "komodohealth",
    "ro",
    "color",
    "virtahealth",
    "springhealth",
    "doximity",
    "zocdoc",
    "headspace",
    "flatironhealth",
    "abridge",
    "tempus",
    "carbonhealth",
    "elationhealth",
    "oscarhealth",
    "vizai",
    "commure",
    "omadahealth",
    "lyrahealth",
    "hingehealth",
    "oakstreethealth",
    "ribbonhealth",
    "cityblockhealth",
    "truveta",
    "benchling",
    "capsule",
    "wheel",
]

# Lever Boards
LEVER_COMPANIES = [
    "hims",
    "modernhealth",
    "osmind",
    "ambiencehealthcare",
    "hippocraticai",
    "strivehealth",
    "charliehealth",
    "subtlemedical",
    "khealth",
    "thirty-madison",
]

# Ashby Boards (Popular with modern Health AI & Remote Startups)
ASHBY_COMPANIES = [
    "suki",
    "athelas",
    "canvas-medical",
    "nabla",
    "corti",
    "unlearn",
]

# Cap per company to ensure site variety
MAX_JOBS_PER_COMPANY = 3

# ==========================================
# 2. DATE FORMATTING HELPER
# ==========================================


def parse_date(date_val):
  """Convert ISO strings or millisecond timestamps into clean relative/formatted dates."""
  if not date_val:
    return "Recently"
  try:
    if isinstance(date_val, (int, float)):
      # Lever uses epoch milliseconds
      dt = datetime.fromtimestamp(date_val / 1000.0, tz=timezone.utc)
    else:
      # ISO 8601 strings (Greenhouse / Ashby)
      clean_str = str(date_val).replace("Z", "+00:00")
      dt = datetime.fromisoformat(clean_str)

    now = datetime.now(timezone.utc)
    diff = (now - dt).days

    if diff == 0:
      return "Today"
    elif diff == 1:
      return "1 day ago"
    elif diff < 30:
      return f"{diff} days ago"
    else:
      return dt.strftime("%b %d, %Y")
  except Exception:
    return "Recently"


# ==========================================
# 3. CATEGORIZATION & TEXT CLEANING
# ==========================================

CATEGORIES = {
    "Health AI": [
        "ai",
        "machine learning",
        "data scientist",
        "llm",
        "nlp",
        "algorithm",
        "deep learning",
    ],
    "Clinical Informatics": [
        "informatics",
        "clinical",
        "ehr",
        "epic",
        "fhir",
        "hl7",
        "medical director",
        "health data",
    ],
    "Product & Engineering": [
        "product manager",
        "engineer",
        "software",
        "frontend",
        "backend",
        "full stack",
        "developer",
    ],
    "Operations": [
        "operations",
        "ops",
        "credentialing",
        "implementation",
        "customer success",
        "care management",
    ],
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
  clean = re.sub("<[^<]+?>", "", text)
  return clean.strip().replace("\n", " ")[:200] + "..."


# ==========================================
# 4. ATS SCRAPERS
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
        posted_date = parse_date(j.get("updated_at") or j.get("created_at"))
        jobs.append({
            "id": j.get("id"),
            "title": title,
            "company": company_token.replace("-", " ").title(),
            "location": j.get("location", {}).get("name", "Remote / Various"),
            "category": categorize_role(title),
            "type": "Full-Time",
            "posted": posted_date,
            "source": "Greenhouse",
            "applyUrl": j.get("absolute_url", ""),
            "description": clean_text(j.get("content", "")),
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
        posted_date = parse_date(j.get("createdAt"))
        jobs.append({
            "id": j.get("id"),
            "title": title,
            "company": company_token.title(),
            "location": j.get("categories", {}).get("location", "Remote"),
            "category": categorize_role(title),
            "type": j.get("categories", {}).get("commitment", "Full-Time"),
            "posted": posted_date,
            "source": "Lever",
            "applyUrl": j.get("hostedUrl", ""),
            "description": clean_text(j.get("descriptionPlain", "")),
        })
  except Exception as e:
    print(f"Error fetching Lever ({company_token}): {e}")
  return jobs


def fetch_ashby_jobs(company_token):
  url = f"https://api.ashbyhq.com/posting-api/job-board/{company_token}"
  jobs = []
  try:
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
      data = res.json()
      postings = data.get("jobs", [])
      for j in postings[:MAX_JOBS_PER_COMPANY]:
        title = j.get("title", "")
        posted_date = parse_date(j.get("publishedAt") or j.get("createdTime"))
        jobs.append({
            "id": j.get("id"),
            "title": title,
            "company": company_token.replace("-", " ").title(),
            "location": j.get("location", "Remote"),
            "category": categorize_role(title),
            "type": "Full-Time",
            "posted": posted_date,
            "source": "Ashby",
            "applyUrl": j.get("jobUrl", ""),
            "description": clean_text(j.get("descriptionHtml", "")),
        })
  except Exception as e:
    print(f"Error fetching Ashby ({company_token}): {e}")
  return jobs


# ==========================================
# 5. MAIN EXECUTION
# ==========================================


def run_scraper():
  all_jobs = []

  # 1. Fetch from Greenhouse
  for company in GREENHOUSE_COMPANIES:
    all_jobs.extend(fetch_greenhouse_jobs(company))

  # 2. Fetch from Lever
  for company in LEVER_COMPANIES:
    all_jobs.extend(fetch_lever_jobs(company))

  # 3. Fetch from Ashby
  for company in ASHBY_COMPANIES:
    all_jobs.extend(fetch_ashby_jobs(company))

  # Shuffle jobs so the board has a diverse, healthy mix of startups
  random.shuffle(all_jobs)

  # Save up to 50 curated jobs
  final_jobs = all_jobs[:50]

  with open("jobs.json", "w", encoding="utf-8") as f:
    json.dump(final_jobs, f, indent=2, ensure_ascii=False)

  print(
      f"Successfully scraped and saved {len(final_jobs)} jobs across"
      " Greenhouse, Lever, and Ashby!"
  )


if __name__ == "__main__":
  run_scraper()
