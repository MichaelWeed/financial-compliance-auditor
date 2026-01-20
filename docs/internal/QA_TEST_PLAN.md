# Auditor System: Comprehensive QA & Setup Manual

**Version**: 3.0 (Master)  
**Role**: Senior Architect / Lead QA  
**Objective**: End-to-end validation of the Hierarchical Audit Scoping System.

---

## I. Global System Requirements

_Assume a fresh machine/terminal session._

### 1. Hardware & Environment

- **OS**: macOS (Metal/MPS capable for embeddings).
- **Manager**: Conda (Miniconda/Anaconda).
- **Python**: 3.10+

### 2. Inference Node (Back-end)

The system requires a local LLM server.

- **Model**: `mlx-community/Qwen2.5-72B-Instruct-4bit` (or similar).
- **Endpoint**: `http://localhost:8080/v1`

---

## II. Environment Bootstrap (The "Fresh Eyes" Setup)

**Pre-conditions**: Terminal is open. You are in the project root directory.

| Step   | Trigger / Action                                             | Expected Result                                                    |
| :----- | :----------------------------------------------------------- | :----------------------------------------------------------------- |
| **S1** | `conda create -n compliance-auditor python=3.10 -y`          | Environment is successfully created.                               |
| **S2** | `conda activate compliance-auditor`                          | Prompt changes to `(compliance-auditor)`.                          |
| **S3** | `pip install -r requirements.txt`                            | All dependencies (streamlit, lancedb, etc.) install without error. |
| **S4** | `python -c "import streamlit; print(streamlit.__version__)"` | Output shows a version number (e.g., `1.38.0`).                    |

---

## III. Service Orchestration

Execute these in **separate** terminal tabs.

### tab-1: Reasoning Node

**Action**: `mlx_lm.server --model mlx-community/Qwen2.5-72B-Instruct-4bit`  
**Expected**: Server starts and stays running on port 8080.

### tab-2: Auditor UI

**Action (The Bulletproof Way)**:
Run this one-shot command to bypass shell path issues:

```bash
conda run -n compliance-auditor streamlit run app.py
```

**Expected**: Browser opens automatically to `http://localhost:8501`. Sidebar shows **"REASONING NODE: ONLINE"**.

---

## IV. Stacking Test Scenarios

_Note: These tests are designed to be performed sequentially to build up the manifest._

### TS-01: Evidence Ingestion (Base Setup)

**Start Condition**: UI is open, "Ingest New Filing" expander is visible.
**Action**:

1. Upload a PDF.
2. Ticker: `GOOGL`.
3. Industry: `Technology`.
4. Year: `2023`.
5. Click **Index Document**.
   **Expected Result**: Success message appears. `GOOGL` appears in "AUDITABLE SCOPE" with Technology/2023 tags.

### TS-02: Level 1 Scoping (Specific Document)

**Start Condition**: TS-01 complete.
**Action**:

1. Select **Company**: `GOOGL`.
2. Select **Industry**: `Technology`.
3. Select **Year**: `2023`.
4. Inquiry: `What is the main revenue source?`
   **Expected Result**: Conclusion cites ONLY 2023 Google chunks. Agent logs verify all 3 filters applied correctly.

### TS-03: Level 2 & 3 Scoping (Widening the Net)

**Start Condition**: TS-02 complete.
**Action**:

1. Keep **Company**: `GOOGL`.
2. Change **Industry**: `ALL`.
3. Change **Year**: `ALL`.
4. Inquiry: `Compare risk disclosures.`
   **Expected Result**: System searches across ALL GOOGL documents in the vault, regardless of year/industry metadata.

### TS-04: Level 4 Scoping (Industry Aggregation)

**Start Condition**: Ingest a second company (e.g., `MSFT`, `Technology`, `2023`) using TS-01 steps.
**Action**:

1. Select **Company**: `ALL`.
2. Select **Industry**: `Technology`.
3. Select **Year**: `ALL`.
4. Inquiry: `Common AI risk disclosures in tech?`
   **Expected Result**: Evidence Repository shows chunks from BOTH `GOOGL` and `MSFT`.

---

## VII. Visual & Thematic Verification (Institutional Light)

**Version 3.2 Feature**: The workbench uses a "Paper" aesthetic and professional SVG icons.

| Component       | Visual Requirement                                                                    |
| :-------------- | :------------------------------------------------------------------------------------ |
| **Background**  | Should be off-white paper (`#FAFAFA` approx), NOT pure white or dark.                 |
| **Icons**       | Blue SVG icons only (No emojis in headers like Conclusion or Evidence).               |
| **Citations**   | Citations should follow the `[Source X - Page Y]` format with coordinates.            |
| **Coordinates** | Large bounding boxes should be truncated (e.g., `LOC: [[120, 208...]` with ellipsis). |
| **Buttons**     | Clean labels (e.g., "Author Draft", "Purge Vault") with high-contrast text.           |

---

## VIII. Forensic Report Builder (Drafting Engine)

**Goal**: Verify the drafting engine produces valid content without UI crashes.

1.  **Run Inquiry**: Submit a query and wait for the Conclusion to render.
2.  **Author Draft**: Click **Author Draft**.
    - **Pass Criterion**: A loading spinner appears, followed by a new text area ("Authorized Draft Buffer").
    - **Fail Criterion**: A red `AttributeError` or `NameError` block appears.
3.  **Buffer Persistence**: Edit the text in the buffer. Click **Clear Buffer**.
    - **Expected**: The buffer area disappears and returns to the default state.

---

## IX. Consolidated Workbench Verification (Final)

**Logic Audit**:

- Verify that **Evidence Repository** contains citation references (`REF_001`, etc.).
- Confirm no "Double Render": Scroll through the results – there should be exactly one Conclusion card and one Evidence Repository list.
- Check the **Page Icon**: Should be the institutional building (`🏛️`) in the browser tab.

---

## X. Troubleshooting & Paths (Reference)

... (Slightly updated CLI instructions) ...
