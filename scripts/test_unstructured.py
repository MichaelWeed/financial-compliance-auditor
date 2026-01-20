from unstructured.partition.pdf import partition_pdf
import sys

def test_single_page(file_path):
    print(f"Testing partition on {file_path} (first page only)...")
    try:
        elements = partition_pdf(
            filename=file_path,
            strategy="fast", # Use fast for quick test
            # hi_res is slow and might download models
        )
        print(f"Success! Found {len(elements)} elements.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_single_page("data/raw/alphabet_10k_2023.pdf")
