# Implementation Plan: Hierarchical Audit Scoping System

**Status**: Ready for Implementation  
**Estimated Effort**: 2-3 hours  
**Dependencies**: Existing `agent.py`, `app.py`, `pipeline.py`, `manifest.json`

---

## 1. Goal

Evolve the "Focus Audit" feature from a simple ticker filter into a **Hierarchical Scoping System** that allows users to progressively narrow or widen their search across four levels:

| Level | Scope Example             | Use Case                                        |
| ----- | ------------------------- | ----------------------------------------------- |
| 1     | `Blue Lagoon 2025 Form D` | "Who signed this specific filing?"              |
| 2     | `All Blue Lagoon docs`    | "Track risk disclosure drift 2022→2025"         |
| 3     | `Blue Lagoon + Mining`    | "Focus only on resource extraction disclosures" |
| 4     | `All Mining Industry`     | "Industry-wide lithium supply chain risks"      |

---

## 2. Current System State

### Files to Modify

- **`app.py`**: Streamlit UI. Has a single "Focus Audit" ticker dropdown.
- **`agent.py`**: Agentic core. Has `ticker_filter` in `AgentState`, used in `retrieve()` with a `.where()` clause.
- **`pipeline.py`**: Ingestion orchestrator. Writes to `manifest.json`.
- **`manifest.json`**: Document registry. Schema: `{ticker, filename, type, ingested_at, path}`.

### Current Filter Logic (`agent.py:retrieve`)

```python
if state.get("ticker_filter"):
    search_query = search_query.where(f"ticker = '{state['ticker_filter']}'")
```

---

## 3. Implementation Summary

### Phase 1: Extend Manifest Schema (Complete)

- **Manifest**: Schema now includes `industry`, `year`, `filing_type`, and `jurisdiction`.
- **Pipeline**: `ingest_and_index` correctly populates these metadata tags.

### Phase 2: Hierarchical Filter UI (Complete)

- **Workbench**: Sidebar features cascading filters for Company, Industry, Year, and Filing Type.
- **Isolation**: Filters prevent cross-document pollution.

### Phase 3: Multi-Filter Retrieval (Complete)

- **Agent**: `retrieve` node in `agent.py` dynamically builds `.where()` clauses based on active filters in `AgentState`.

### Phase 4: Database Schema Update (Complete)

- **LanceDB**: Schema extended to include all forensic metadata fields.

### Phase 5: Institutional Refinement & Workbench Consolidation (Complete)

- **Theme**: "Institutional Light (Paper)" system implemented for professional readability.
- **Iconography**: Standardized SVG icons replace all emojis.
- **Drafting**: Integrated high-precision "Forensic Report Builder" with dedicated LLM instance.
- **Cleanup**: Purged redundant rendering loops and formatted coordinate citations.

---

## 4. Final Architecture

The system now functions as a unified **Forensic Analysis Workbench**, where filtering, retrieval, citation, and reporting are consolidated into a high-precision loop.

---

## 4. Verification Plan

| Test                | Action                            | Expected Result                            |
| ------------------- | --------------------------------- | ------------------------------------------ |
| **Scope L1**        | Select `BLRX` + `2025` + `Form D` | Only that specific doc's chunks returned   |
| **Scope L2**        | Select `BLRX` + `ALL`             | All Blue Lagoon docs searched              |
| **Scope L3**        | Select `BLRX` + `Mining`          | Only mining-tagged Blue Lagoon chunks      |
| **Scope L4**        | Select `ALL` + `Mining`           | All mining-industry docs in library        |
| **Backward Compat** | Query with no filters             | All documents searched (existing behavior) |

---

## 5. UI/UX Considerations

- **Default State**: "ALL DOCUMENTS" to preserve current behavior.
- **Empty State Handling**: If a filter combo returns 0 results, show a clear message suggesting broader scope.
- **Industry List**: Pre-populate with SEC standard sectors (or allow free-text for flexibility).

---

## 6. Files Changed Summary

| File            | Change Type | Description                                         |
| --------------- | ----------- | --------------------------------------------------- |
| `pipeline.py`   | MODIFY      | Add `industry` and `year` to ingestion and manifest |
| `database.py`   | MODIFY      | Extend `ComplianceChunk` schema                     |
| `agent.py`      | MODIFY      | Multi-filter retrieval logic                        |
| `app.py`        | MODIFY      | Cascading filter UI panel                           |
| `manifest.json` | SCHEMA      | Add `industry`, `year` fields                       |

---

## 7. Stretch Goal: Semantic Topic Filter

If time permits, add a **semantic pre-filter** option:

- User types a topic keyword (e.g., "lithium supply chain")
- System runs a quick vector search on that keyword
- Filters candidate documents before the main query

This enables Level 3 scoping without requiring manual tagging.
