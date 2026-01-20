import lancedb
import pandas as pd
from lancedb.pydantic import LanceModel, Vector
from sentence_transformers import SentenceTransformer
import json
import os

# Initialize embedding model (runs on Metal/MPS on Mac)
# 'all-MiniLM-L6-v2' is fast, 'all-mpnet-base-v2' is better but slower.
# We'll use a middle ground for quality.
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

class ComplianceChunk(LanceModel):
    vector: Vector(384) # Dim for all-MiniLM-L6-v2
    text: str
    ticker: str
    section: str
    page_number: int
    element_type: str
    table_json: str = "" # Store HTML or JSON representation of tables
    bbox: str = "" # Store bounding box as string "[x0, y0, x1, y1]"
    industry: str = "" # Industry classification (e.g., "Mining & Resources", "Tech")
    year: int = 0 # Filing year for temporal filtering
    filing_type: str = "" # 10-K, 10-Q, 8-K, etc.
    fiscal_period: str = "" # Q1, Q2, Q3, Q4, FY
    jurisdiction: str = "" # US, EU, UK, APAC
    risk_flag: bool = False # Flag for items requiring high-level audit attention
    cik: str = "" # SEC Central Index Key enabling deeper lookups
    source_pdf: str = "" # Actual PDF filename for View Source button

def create_db(db_path="data/vector_db"):
    db = lancedb.connect(db_path)
    return db

def process_and_upsert(db, json_path, ticker="AAPL", industry="", year=0, filing_type="", fiscal_period="", jurisdiction="", risk_flag=False, cik="", source_pdf=""):
    with open(json_path, "r") as f:
        elements = json.load(f)
    
    data = []
    print(f"Processing {len(elements)} elements for {ticker}...")
    
    for el in elements:
        text = el.get("text", "")
        if not text:
            continue
            
        # Extract metadata
        metadata = el.get("metadata", {})
        page = metadata.get("page_number", 1)
        # Bounding box is often in coordinates -> points
        coords = metadata.get("coordinates", {})
        points = coords.get("points", [])
        bbox_str = json.dumps(points) if points else ""
        
        table_json = ""
        # Capture HTML table data from ANY element type (often inside CompositeElement)
        if "text_as_html" in metadata:
            table_json = metadata.get("text_as_html", "")
        elif el["type"] == "Table":
            # Fallback if text_as_html is missing but it is a Table type
            table_json = metadata.get("text_as_html", "")

            
        # Create embedding
        vector = model.encode(text)
        
        data.append({
            "vector": vector,
            "text": text,
            "ticker": ticker,
            "section": el.get("type", "Text"), # Using type as section for now
            "page_number": page,
            "element_type": el["type"],
            "table_json": table_json,
            "bbox": bbox_str,
            "industry": industry,
            "year": year,
            "filing_type": filing_type,
            "fiscal_period": fiscal_period,
            "jurisdiction": jurisdiction,
            "risk_flag": risk_flag,
            "cik": cik,
            "source_pdf": source_pdf
        })
    
    # Create or Get table
    table_name = "compliance_audit"
    if table_name in db.table_names():
        tbl = db.open_table(table_name)
        tbl.add(data)
    else:
        tbl = db.create_table(table_name, schema=ComplianceChunk, data=data)
    
    print(f"Upserted {len(data)} chunks into {table_name}")
    return tbl

if __name__ == "__main__":
    DB_PATH = "data/vector_db"
    JSON_PATH = "data/processed/alphabet_10k_2023.json"
    
    if os.path.exists(JSON_PATH):
        db = create_db(DB_PATH)
        process_and_upsert(db, JSON_PATH, ticker="GOOGL")
    else:
        print(f"Processed JSON not found at {JSON_PATH}. Run ingest.py first.")
