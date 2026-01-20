from pypdf import PdfReader, PdfWriter
import sys

def slice_pdf(input_path, output_path, end_page=5):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for i in range(min(end_page, len(reader.pages))):
        writer.add_page(reader.pages[i])
        
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"Saved {end_page} pages to {output_path}")

if __name__ == "__main__":
    slice_pdf("data/raw/alphabet_10k_2023.pdf", "data/raw/alphabet_10k_sample.pdf")
