# PDF Viewer Component Test

This is a simple test harness to validate the PDF viewer in isolation before integrating it into the main app.

## Run:

```bash
cd [project-root]
streamlit run components/pdf_viewer.py --server.port 8501
```

## Expected Behavior:

- If a test PDF exists at `data/raw/alphabet_10k_sample.pdf`, it will render automatically.
- Otherwise, upload a PDF to test the component.
- The PDF should render with a clean border and shadow.

## Phase 1 Validation:

- [ ] PDF renders without errors
- [ ] Component displays in Streamlit without breaking layout
- [ ] No dependency issues with pdf.js CDN
