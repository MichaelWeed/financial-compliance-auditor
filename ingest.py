import os
import json
import sys

# Fix PATH to include homebrew poppler binaries (required for hi_res PDF processing)
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import convert_to_dict

def get_bbox_from_points(points):
    """
    Returns a bounding box [x0, y0, x1, y1] from a list of points.
    points format: ((x0, y0), (x0, y1), (x1, y1), (x1, y0))
    """
    if not points:
        return None
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    return [min(xs), min(ys), max(xs), max(ys)]

def merge_bboxes(bboxes):
    """
    Merges multiple [x0, y0, x1, y1] bboxes into one.
    """
    valid_bboxes = [b for b in bboxes if b is not None]
    if not valid_bboxes:
        return None
        
    x0 = min(b[0] for b in valid_bboxes)
    y0 = min(b[1] for b in valid_bboxes)
    x1 = max(b[2] for b in valid_bboxes)
    y1 = max(b[3] for b in valid_bboxes)
    
    return [x0, y0, x1, y1]

def ingest_pdf(file_path, output_dir="data/processed"):
    """
    Parses a PDF using unstructured, extracting text, tables, and bounding boxes.
    Handles chunking while preserving/aggregating coordinates.
    """
    print(f"\n--- Starting Ingestion: {os.path.basename(file_path)} ---")
    sys.stdout.flush()
    
    # Selection of strategy: 
    # 'hi_res' is best for tables and coordinates but requires tesseract/poppler and is slower.
    # 'fast' is text-only and much quicker.
    # Given the requirements (Table HTML + Bboxes), we MUST use 'hi_res'.
    print("Partitioning PDF with 'hi_res' strategy (this may take a minute)...")
    sys.stdout.flush()
    
    elements = partition_pdf(
        filename=file_path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_images_in_pdf=False,
        chunking_strategy="by_title",
        max_characters=2000,
        new_after_n_chars=1500,
        combine_text_under_n_chars=500,
        # languages=["eng"]
    )
    
    print(f"Partitioning complete. Found {len(elements)} elements/chunks.")
    sys.stdout.flush()
    
    element_dicts = convert_to_dict(elements)
    
    # Custom logic to ensure every element has bounding box coordinates,
    # especially for CompositeElements (chunks) which don't have them by default.
    processed_count = 0
    for i, el in enumerate(elements):
        target_dict = element_dicts[i]
        
        # 1. Handle coordinates for chunks
        if hasattr(el, "metadata") and hasattr(el.metadata, "orig_elements") and el.metadata.orig_elements:
            # This is a CompositeElement (chunk). Aggregate bboxes from original elements.
            chunk_bboxes = []
            for orig_el in el.metadata.orig_elements:
                if hasattr(orig_el.metadata, "coordinates") and orig_el.metadata.coordinates:
                    bbox = get_bbox_from_points(orig_el.metadata.coordinates.points)
                    if bbox:
                        chunk_bboxes.append(bbox)
            
            merged = merge_bboxes(chunk_bboxes)
            if merged:
                # Inject merged bbox into the dict metadata so database.py can find it
                if "metadata" not in target_dict:
                    target_dict["metadata"] = {}
                
                # We store it in a format database.py expects: metadata.coordinates.points
                # even though it's technically a merged bbox now.
                target_dict["metadata"]["coordinates"] = {
                    "points": [
                        [merged[0], merged[1]],
                        [merged[0], merged[3]],
                        [merged[2], merged[3]],
                        [merged[2], merged[1]]
                    ],
                    "system": "PixelSpace",
                    "layout_width": target_dict["metadata"].get("layout_width"),
                    "layout_height": target_dict["metadata"].get("layout_height")
                }
        
        processed_count += 1

    # Save to JSON
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(file_path).rsplit('.', 1)[0] + ".json"
    output_path = os.path.join(output_dir, base_name)
    
    # Helper for numpy types if any remain (convert_to_dict usually handles them but just in case)
    def default_serializer(obj):
        if hasattr(obj, "tolist"):
            return obj.tolist()
        return str(obj)

    with open(output_path, "w") as f:
        json.dump(element_dicts, f, indent=2, default=default_serializer)
    
    num_tables = len([el for el in element_dicts if el.get("type") == "Table"])
    print(f"Detected {num_tables} tables with HTML structure.")
    
    return output_path

if __name__ == "__main__":
    RAW_DIR = "data/raw"
    PROCESSED_DIR = "data/processed"
    
    # Default to sample if no args, otherwise allow passing file
    if len(sys.argv) > 1:
        files_to_process = [sys.argv[1]]
    else:
        # Process all PDFs in the raw directory excluding small tests
        files_to_process = [
            os.path.join(RAW_DIR, f) 
            for f in os.listdir(RAW_DIR) 
            if f.endswith(".pdf") and os.path.getsize(os.path.join(RAW_DIR, f)) > 10000
        ]
        
    if not files_to_process:
        print(f"No valid PDFs found to process in {RAW_DIR}")
        sys.exit(1)
        
    for file_path in files_to_process:
        if os.path.exists(file_path):
            ingest_pdf(file_path, PROCESSED_DIR)
        else:
            print(f"File not found: {file_path}")
