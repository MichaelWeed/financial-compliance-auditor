import os
import json
import time
import requests
from ingest import ingest_pdf
from database import create_db, process_and_upsert

MANIFEST_PATH = "data/manifest.json"
DB_PATH = "data/vector_db"
PROCESSED_DIR = "data/processed"

def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r") as f:
                return json.load(f)
        except:
            return {"documents": []}
    return {"documents": []}

def save_manifest(manifest):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

def purge_vault():
    """
    Complete reset of the forensic vault: Deletes the vector database, 
    the manifest, and all processed JSON files.
    """
    import shutil
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
    if os.path.exists(PROCESSED_DIR):
        shutil.rmtree(PROCESSED_DIR)
    if os.path.exists(MANIFEST_PATH):
        os.remove(MANIFEST_PATH)
    # Re-initialize empty manifest
    save_manifest({"documents": []})
    print("--- VAULT PURGED: DB and Manifest reset to baseline ---")

def ingest_and_index(file_path, ticker, filing_type="10-K", industry="", year=0, fiscal_period="", jurisdiction="", risk_flag=False, cik=""):
    """
    Unified pipeline to process a PDF and index it in LanceDB.
    """
    start_time = time.time()
    filename = os.path.basename(file_path)
    
    print(f"--- Pipeline Starting for {ticker} ({filename}) ---")
    
    # 1. Ingest (Partition + Map coordinates)
    # ingest_pdf creates a JSON in data/processed/
    json_path = ingest_pdf(file_path, output_dir=PROCESSED_DIR)
    
    # 2. Index (Embed + Upsert to LanceDB)
    db = create_db(DB_PATH)
    process_and_upsert(
        db, json_path, ticker=ticker, industry=industry, year=year, 
        filing_type=filing_type, fiscal_period=fiscal_period, 
        jurisdiction=jurisdiction, risk_flag=risk_flag, cik=cik,
        source_pdf=filename
    )
    
    # 3. Update Manifest
    manifest = load_manifest()
    
    # Check if already exists to avoid duplicates in manifest (lancedb.add is additive)
    doc_entry = {
        "ticker": ticker,
        "filename": filename,
        "type": filing_type,
        "industry": industry,
        "year": year,
        "fiscal_period": fiscal_period,
        "jurisdiction": jurisdiction,
        "risk_flag": risk_flag,
        "cik": cik,
        "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "path": file_path
    }
    
    # Simple deduplication in manifest view
    manifest["documents"] = [d for d in manifest["documents"] if not (d["ticker"] == ticker and d["filename"] == filename)]
    manifest["documents"].append(doc_entry)
    save_manifest(manifest)
    
    duration = time.time() - start_time
    print(f"--- Pipeline Complete in {duration:.2f}s ---")
    
    return doc_entry

def get_cik_from_ticker(ticker):
    """
    Resolves a ticker symbol to a CIK using the SEC's public mapping.
    """
    headers = {"User-Agent": "Institutional-Compliance-Auditor/1.0 (contact@research.ai)"}
    try:
        res = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
        if res.status_code != 200:
            return None
        data = res.json()
        for k, v in data.items():
            if v['ticker'] == ticker.upper():
                return str(v['cik_str']).zfill(10)
    except Exception as e:
        print(f"Error resolving CIK for {ticker}: {e}")
    return None

def fetch_from_edgar(ticker, year):
    """
    Compliant SEC EDGAR fetcher.
    Downloads the primary document (usually HTM) for a specific ticker and year.
    """
    cik = get_cik_from_ticker(ticker)
    if not cik:
        raise Exception(f"CIK not found for ticker: {ticker}. Please ensure the ticker is correct.")
    
    headers = {
        "User-Agent": "Antigravity Research (admin@antigravity.ai)",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov"
    }
    
    # 1. Fetch submissions history
    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    res = requests.get(submissions_url, headers=headers)
    if res.status_code != 200:
        raise Exception(f"Failed to fetch submissions for CIK {cik} (Status: {res.status_code})")
        
    submissions = res.json()
    recent = submissions.get('filingHistory', {}).get('recent', {})
    
    # 2. Find the 10-K for the target year (or filing year X+1)
    found_idx = -1
    for i, form in enumerate(recent.get('form', [])):
        if "10-K" in form: # Matches 10-K, 10-K/A
            date = recent.get('filingDate', [])[i]
            # 10-K for year X is often filed in year X or year X+1
            if date.startswith(str(year)) or date.startswith(str(year+1)):
                found_idx = i
                break
    
    if found_idx == -1:
        raise Exception(f"No 10-K filing found for {ticker} associated with year {year}.")
        
    accession_no = recent['accessionNumber'][found_idx]
    primary_doc = recent['primaryDocument'][found_idx]
    
    # 3. Construct URL
    # https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_no_dashes}/{primary_doc}
    accession_no_clean = accession_no.replace("-", "")
    download_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_clean}/{primary_doc}"
    
    print(f"Downloading primary document from: {download_url}")
    res = requests.get(download_url, headers=headers)
    if res.status_code != 200:
        raise Exception(f"Failed to download primary document: {download_url}")
    
    # 4. Save to data/raw
    os.makedirs("data/raw", exist_ok=True)
    file_ext = os.path.splitext(primary_doc)[1]
    filename = f"{ticker}_{year}_10K{file_ext}"
    local_path = os.path.join("data/raw", filename)
    
    with open(local_path, "wb") as f:
        f.write(res.content)
        
    print(f"SUCCESS: {filename} downloaded and saved to vault base.")
    return local_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Financial Compliance Auditor Pipeline")
    parser.add_argument("--file", help="Path to a single PDF file")
    parser.add_argument("--dir", help="Path to a directory of PDFs for batch processing")
    parser.add_argument("--ticker", help="Ticker symbol (required if --file is used)")
    parser.add_argument("--industry", default="", help="Industry classification (e.g., Technology)")
    parser.add_argument("--year", type=int, default=0, help="Filing year (e.g., 2023)")
    parser.add_argument("--type", default="10-K", help="Filing type (e.g., 10-K, 10-Q)")
    parser.add_argument("--period", default="", help="Fiscal period (e.g., Q1, Annual)")
    parser.add_argument("--jurisdiction", default="", help="Jurisdiction (e.g., US, UK)")
    parser.add_argument("--risk", action="store_true", help="Mark as high-risk")
    parser.add_argument("--cik", default="", help="CIK (SEC ID)")
    args = parser.parse_args()
    
    if args.file:
        if not args.ticker:
            print("Error: --ticker is required when using --file.")
        elif os.path.exists(args.file):
            ingest_and_index(
                args.file, args.ticker, filing_type=args.type, industry=args.industry, 
                year=args.year, fiscal_period=args.period, jurisdiction=args.jurisdiction,
                risk_flag=args.risk, cik=args.cik
            )
        else:
            print(f"File not found: {args.file}")
            
    elif args.dir:
        if os.path.exists(args.dir):
            pdfs = [f for f in os.listdir(args.dir) if f.endswith(".pdf")]
            print(f"Found {len(pdfs)} PDFs in {args.dir}. High-volume processing starting...")
            for f in pdfs:
                # Naive ticker detection: use first 4 chars of filename if not provided
                ticker = f[:4].upper()
                ingest_and_index(os.path.join(args.dir, f), ticker)
        else:
            print(f"Directory not found: {args.dir}")
    else:
        parser.print_help()
