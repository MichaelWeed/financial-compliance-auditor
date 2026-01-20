"""
PDF Viewer Component with Bounding Box Overlay

This component renders PDFs with optional highlight overlays for citation grounding.
Phase 1: Isolated component with basic PDF rendering.
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
import json
from pathlib import Path


def render_pdf_viewer(pdf_path: str, page_number: int = 1, bbox: str = None, height: int = 800):
    """
    Render a PDF with optional bounding box highlight.
    
    Args:
        pdf_path: Absolute path to PDF file
        page_number: Page to display (1-indexed)
        bbox: JSON string of bounding box coordinates (optional)
        height: Viewer height in pixels
    """
    
    # Validate PDF exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        st.error(f"PDF not found: {pdf_path}")
        return
    
    # Read and encode PDF
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    # Parse bbox if provided
    bbox_rect = None
    if bbox:
        try:
            # bbox is stored as JSON string of 4-point polygon from Unstructured.io
            # Example: "[[x0, y0], [x1, y1], [x2, y2], [x3, y3]]"
            points = json.loads(bbox)
            if points and len(points) >= 2:
                # Convert polygon to rectangle [x0, y0, x1, y1]
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                bbox_rect = [min(xs), min(ys), max(xs), max(ys)]
        except (json.JSONDecodeError, IndexError, KeyError):
            st.warning("Invalid bbox format. Showing page without highlight.")
    
    # Generate HTML with pdf.js
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: #f8f9fa;
            }}
            #pdf-container {{
                position: relative;
                width: 100%;
                height: {height}px;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            #pdf-canvas {{
                border: 1px solid #e5e7eb;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                background: white;
            }}
            #highlight-overlay {{
                position: absolute;
                border: 3px solid #D4AF37;
                background: rgba(212, 175, 55, 0.15);
                pointer-events: none;
                display: none;
            }}
        </style>
    </head>
    <body>
        <div id="pdf-container">
            <canvas id="pdf-canvas"></canvas>
            <div id="highlight-overlay"></div>
        </div>
        
        <script>
            const pdfjsLib = window['pdfjs-dist/build/pdf'];
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            
            const pdfData = atob('{pdf_base64}');
            const pageNum = {page_number};
            const bboxRect = {json.dumps(bbox_rect)};
            
            const loadingTask = pdfjsLib.getDocument({{data: pdfData}});
            loadingTask.promise.then(pdf => {{
                pdf.getPage(pageNum).then(page => {{
                    const canvas = document.getElementById('pdf-canvas');
                    const context = canvas.getContext('2d');
                    
                    // Scale to fit container width (max 800px)
                    const viewport = page.getViewport({{scale: 1.5}});
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    
                    const renderContext = {{
                        canvasContext: context,
                        viewport: viewport
                    }};
                    
                    page.render(renderContext).promise.then(() => {{
                        // Draw bounding box overlay if provided
                        if (bboxRect && bboxRect.length === 4) {{
                            const overlay = document.getElementById('highlight-overlay');
                            const scale = viewport.scale;
                            
                            // PDF coordinates are from bottom-left, canvas from top-left
                            const x0 = bboxRect[0] * scale;
                            const y0 = (viewport.height / scale - bboxRect[3]) * scale;
                            const width = (bboxRect[2] - bboxRect[0]) * scale;
                            const height = (bboxRect[3] - bboxRect[1]) * scale;
                            
                            overlay.style.left = x0 + 'px';
                            overlay.style.top = y0 + 'px';
                            overlay.style.width = width + 'px';
                            overlay.style.height = height + 'px';
                            overlay.style.display = 'block';
                        }}
                    }});
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    # Render in Streamlit
    components.html(html_content, height=height, scrolling=False)


# Test harness (will be removed in production)
if __name__ == "__main__":
    st.set_page_config(page_title="PDF Viewer Test", layout="wide")
    st.title("PDF Viewer Component Test")
    
    # Test with a sample PDF if available
    base_dir = Path(__file__).parent.parent
    test_pdf = base_dir / "data/raw/alphabet_10k_sample.pdf"
    
    if Path(test_pdf).exists():
        st.success(f"Testing with: {test_pdf}")
        render_pdf_viewer(test_pdf, page_number=1)
    else:
        st.warning("No test PDF found. Upload a PDF to test the component.")
        uploaded = st.file_uploader("Upload PDF for testing", type=["pdf"])
        if uploaded:
            temp_path = f"/tmp/{uploaded.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded.getbuffer())
            render_pdf_viewer(temp_path, page_number=1)
