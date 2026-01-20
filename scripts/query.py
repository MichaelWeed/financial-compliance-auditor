import lancedb
from sentence_transformers import SentenceTransformer

def query_db(query_text, db_path="data/vector_db", limit=3):
    print(f"Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print(f"Connecting to DB at {db_path}...")
    db = lancedb.connect(db_path)
    table = db.open_table("compliance_audit")
    
    print(f"Querying for: '{query_text}'")
    query_vector = model.encode(query_text)
    
    results = table.search(query_vector).limit(limit).to_pandas()
    
    print("\nSearch Results:")
    with open("query_results.txt", "w") as f_out:
        for i, row in results.iterrows():
            output = f"\nResult {i+1} (Score: {row['_distance']:.4f}):\n"
            output += f"Ticker: {row['ticker']} | Page: {row['page_number']} | Type: {row['element_type']}\n"
            output += f"Text: {row['text'][:200]}...\n"
            if row['bbox']:
                output += f"BBox: {row['bbox']}\n"
            print(output)
            f_out.write(output)

if __name__ == "__main__":
    query_db("Who is the company and what model of report is this?")
