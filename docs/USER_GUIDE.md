# 💼 Operations Manual: Auditor User Guide

This guide details how to install, configure, and use the Financial Compliance Auditor for daily financial document auditing.

---

## 🚦 Startup & Configuration

The auditor requires two simultaneous services: the **Reasoning Node** (LLM Server) and the **Financial Workbench** (UI).

### 1. The One-Click App (macOS Only)

- Locate the **Financial Compliance Auditor.app** in the project directory.
- Drag it to your `/Applications` folder.
- Double-click to ignite both services at once.

### 2. Manual Terminal Launch (Advanced/Windows)

If you prefer to see the logs or are on Windows:

```bash
# macOS/Linux
./launch.sh

# Windows
launch.bat
```

---

## 🛠️ The Audit Workflow

### Phase 1: Ingestion & Scoping

Before querying, you must ingest the target 10-K filing into the secure vault.

1. Open the sidebar and find the **Ingest New Filing** section.
2. Select your PDF.
3. **Important**: Assign a **Ticker**, **Industry**, and **Year**. These metadata tags allow for hierarchical scoping later.
4. Click **Index Document**.

### Phase 2: The Inquiry

Ask your audit questions in the main workbench.

- **Example**: "What were the significant acquisitions in FY2023 and where are they cited?"
- The system will fetch context, peer-review it for accuracy (Grading node), and generate a report.

### Phase 3: Compliance Verification

When the system provides a conclusion, you must verify the evidence:

1. Locate the **Evidence Repository** in the sidebar.
2. Click **📄 View Source** next to any citation reference (e.g., `REF_001`).
3. The PDF viewer will open to the exact page, with the target text framed in a golden highlight box.

### Phase 4: Reporting

Once you've verified your findings:

1. Click **Author Draft** in the conclusion card.
2. This generates a clean, formatted report in the **Authorized Draft Buffer**.
3. You can edit, format, and copy this report for your final deliverables.

---

## 🔬 Methodology: Why This Tool Is Different

Traditional RAG systems find text that "looks like" the answer. The Financial Compliance Auditor uses **Substantiated Retrieval**:

- We scope by Ticker first to prevent cross-company pollution.
- We preserve table structures so the AI can "read" balance sheets properly.
- We map every claim to a physical location on the document, not just a text string.

---

## 🆘 Troubleshooting

- **Reasoning Node Offline**: Verify the MLX inference server is running on port 8080.
- **Out of Memory**: Ensure you have at least 64GB of unified memory if running the 72B model.
- **No Results Found**: Try broadening your scope (e.g., change "Year" to "ALL").
