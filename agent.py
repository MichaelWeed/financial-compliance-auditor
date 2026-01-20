import os
import sys
from typing import List, Dict, Any, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from sentence_transformers import SentenceTransformer
import lancedb
import pandas as pd
from langgraph.graph import StateGraph, END

# --- LOGGING SETUP ---
LOG_FILE = "logs/agent_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(str(msg) + "\n")
    print(msg, flush=True)

# Clear log
with open(LOG_FILE, "w") as f:
    f.write("--- AGENT LOG START ---\n")

# --- CONFIGURATION ---
DB_PATH = "data/vector_db"
TABLE_NAME = "compliance_audit"
LLM_MODEL = "mlx-community/Qwen2.5-72B-Instruct-4bit"
BASE_URL = "http://localhost:8080/v1"

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    question: str
    generation: str
    documents: List[Dict[str, Any]]
    iterations: int
    ticker_filter: str # Optional filter to scope search
    industry_filter: str # Optional industry filter for hierarchical scoping
    year_filter: int # Optional year filter for temporal scoping
    filing_type_filter: str # New: filter by filing type
    jurisdiction_filter: str # New: filter by jurisdiction
    risk_only_filter: bool # New: filter for risk-flagged entries

# --- NODES ---

class AuditorAgent:
    def __init__(self):
        log("Initializing Auditor Agent...")
        try:
            self.llm = ChatOpenAI(
                model=LLM_MODEL, 
                openai_api_base=BASE_URL, 
                openai_api_key="not-needed",
                temperature=0.1
            )
            log("ChatOpenAI initialized.")
            self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
            log("Embedding model loaded.")
            self.db = lancedb.connect(DB_PATH)
            if TABLE_NAME in self.db.table_names():
                self.table = self.db.open_table(TABLE_NAME)
                log("Database table connected.")
            else:
                self.table = None
                log(f"WARNING: Table '{TABLE_NAME}' not found. Agent will return empty results until documents are indexed.")
        except Exception as e:
            log(f"FAILED TO INITIALIZE AGENT: {e}")
            # We don't raise here, we allow the agent to exist in a deferred state
            self.table = None

    def retrieve(self, state: AgentState):
        t = state.get('ticker_filter', 'NONE')
        ind = state.get('industry_filter', 'NONE')
        y = state.get('year_filter', 'NONE')
        ft = state.get('filing_type_filter', 'NONE')
        j = state.get('jurisdiction_filter', 'NONE')
        r = state.get('risk_only_filter', False)
        log(f"--- RETRIEVING for: {state['question']} (Ticker: {t}, Ind: {ind}, Year: {y}, Type: {ft}, Juris: {j}, Risk: {r}) ---")
        
        if self.table is None:
            # Table might have been created since initialization, attempt one last reconnect
            if TABLE_NAME in self.db.table_names():
                self.table = self.db.open_table(TABLE_NAME)
            else:
                log("RETRIEVAL FAILED: No compliance audit table found in vault.")
                return {"documents": [], "iterations": state.get("iterations", 0) + 1}

        query_vector = self.embed_model.encode(state['question'])
        
        # Build search query with hierarchical filters
        search_query = self.table.search(query_vector).limit(8)
        
        # Get available columns from the database schema to prevent errors on old DBs
        available_columns = self.table.schema.names
        
        # Build filter conditions dynamically based on existing schema
        filters = []
        if state.get("ticker_filter") and "ticker" in available_columns:
            filters.append(f"ticker = '{state['ticker_filter']}'")
        if state.get("industry_filter") and "industry" in available_columns:
            filters.append(f"industry = '{state['industry_filter']}'")
        if state.get("year_filter") and "year" in available_columns:
            filters.append(f"year = {state['year_filter']}")
        if state.get("filing_type_filter") and "filing_type" in available_columns:
            filters.append(f"filing_type = '{state['filing_type_filter']}'")
        if state.get("jurisdiction_filter") and "jurisdiction" in available_columns:
            filters.append(f"jurisdiction = '{state['jurisdiction_filter']}'")
        if state.get("risk_only_filter") and "risk_flag" in available_columns:
            filters.append("risk_flag = true")
        
        # Apply combined filters if any exist
        if filters:
            search_query = search_query.where(" AND ".join(filters))
            
        results = search_query.to_pandas()
        documents = results.to_dict(orient="records")
        return {"documents": documents, "iterations": state.get("iterations", 0) + 1}

    def grade_documents(self, state: AgentState):
        log("--- GRADING DOCUMENTS ---")
        question = state["question"]
        documents = state["documents"]
        
        # Check if this is a table/calculation query (be more lenient)
        table_keywords = ['table', 'tabular', 'calculate', 'difference', 'sum', 'total', 'accrual', 'revenue', 'expense']
        is_table_query = any(kw in question.lower() for kw in table_keywords)
        
        filtered_docs = []
        for i, doc in enumerate(documents):
            log(f"Grading Doc {i+1}...")
            
            # Include table data in grading context if available
            table_context = ""
            if doc.get('table_json'):
                table_context = f"\nTABLE DATA: {doc['table_json'][:500]}..."
            
            prompt = f"""You are a senior compliance grader. 
            Evaluate if the following document chunk is RELEVANT to the auditor's question.
            
            AUDITOR QUESTION: {question}
            DOCUMENT CONTEXT (Page {doc['page_number']}): {doc['text']}{table_context}
            
            RELEVANCE CRITERIA:
            1. Does the text or table contain information that directly or indirectly addresses the question?
            2. If the question asks about tabular data, financial figures, or calculations, consider if this chunk might contain the relevant table.
            3. If the question mentions a specific page, does the context match that page?
            
            Be INCLUSIVE for table-related queries - if there's any chance the document contains relevant data, answer YES.
            
            Answer only with 'YES' or 'NO'.
            """
            res = self.llm.invoke([HumanMessage(content=prompt)])
            log(f" Result: {res.content.strip()}")
            
            # For table queries, be more lenient - include docs with tables even if grader uncertain
            if "YES" in res.content.upper():
                filtered_docs.append(doc)
            elif is_table_query and doc.get('table_json'):
                log(" Including table doc due to table query leniency")
                filtered_docs.append(doc)
        
        return {"documents": filtered_docs}


    def generate(self, state: AgentState):
        log("--- GENERATING ANSWER ---")
        question = state["question"]
        documents = state["documents"]
        
        if not documents:
            return {"generation": "I'm sorry, I couldn't find relevant information in the provided SEC filings to answer your question accurately."}

        context = ""
        available_tables = []
        for i, doc in enumerate(documents):
            context += f"\n[Source {i+1} - Page {doc['page_number']}]:\n{doc['text']}\n"
            if doc.get('table_json'):
                context += f"Table Data (HTML): {doc['table_json']}\n"
                available_tables.append(f"Page {doc['page_number']}")
            if doc.get('bbox'):
                context += f"Coordinates: {doc['bbox']}\n"

        system_msg = """You are a Senior Financial Compliance Auditor with expertise in financial statement analysis.
        Your task is to answer user questions based ONLY on the provided context from SEC 10-K filings.
        
        CRITICAL RULES:
        1. Accuracy is paramount. If the context doesn't contain the answer, say you don't know.
        2. Cite your sources using [Source X - Page Y].
        3. If there is a bounding box (Coordinates) provided, include it in your citation to enable visual highlighting.
        4. Maintain a professional, objective tone.

        RISK FACTOR INTERPRETATION RULES:
        - Distinguish between Hypothetical Risks and Realized Events within Risk Factors (Item 1A).
        - THE "FOR EXAMPLE" OVERRIDE: If text follows phrases like "For example," "We have previously," "Such as the incident in," or "As disclosed in," treat that text as a CONFIRMED HISTORICAL FACT.
        - DATE-BASED VALIDATION: If a description includes a specific past date (e.g., "In November 2023"), it is a FACT. Extract it immediately.
        - GENERICIZED ENTITIES: Corporations often omit specific names (e.g., "Midnight Blizzard") for generic terms ("nation-state actor"). Extract the *description of the actor* even if a proper noun is missing.
        
        TABULAR DATA & CALCULATION RULES:
        - IMPORTANT: Table data may appear as inline text (e.g., "2025 Deferred tax assets 20,777") rather than HTML.
        - Parse numerical values from the text carefully. Look for patterns like "Year Label Amount" or "Category $ Amount".
        - Numbers following year labels (2024, 2025) or preceding text labels often represent financial figures in millions.
        - If asked to calculate differences, sums, or comparisons between years, PERFORM THE MATH explicitly.
        - Show your work: "Value in 2025: $X million, Value in 2024: $Y million, Difference: $X - $Y = $Z million"
        - Identify the correct row labels and extract the corresponding values even if they appear inline.
        - State whether values increased or decreased based on your calculation.
        
        DATA AVAILABILITY GUIDANCE:
        - If the specific data requested is NOT in the context, explicitly state what related data IS available.
        - Example: "I couldn't find accruals for warranties in the provided context. However, the context contains information about [list what's actually present]."
        - Suggest alternative queries the user could try based on what data you can see.
        - If tables are present, mention which pages contain tabular data to help the user refine their search.
        """
        
        prompt = f"Question: {question}\n\nContext:\n{context}"
        
        res = self.llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ])
        
        return {"generation": res.content}

    def decide_to_generate(self, state: AgentState):
        return "generate"

# --- BUILD THE GRAPH ---

def create_agent_graph():
    auditor = AuditorAgent()
    workflow = StateGraph(AgentState)
    workflow.add_node("retrieve", auditor.retrieve)
    workflow.add_node("grade_documents", auditor.grade_documents)
    workflow.add_node("generate", auditor.generate)
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges("grade_documents", auditor.decide_to_generate, {"generate": "generate"})
    workflow.add_edge("generate", END)
    return workflow.compile()

if __name__ == "__main__":
    log("--- DEBUG: Starting Script ---")
    try:
        app = create_agent_graph()
        log("--- DEBUG: Graph Compiled ---")
        
        query = "What is the Agreement and Plan of Merger mentioned in the exhibits and what page is it on?"
        log(f"\n--- Starting Audit for: {query} ---\n")
        
        inputs = {"question": query}
        log("--- DEBUG: Starting Stream ---")
        for output in app.stream(inputs):
            for key, value in output.items():
                log(f"Node '{key}': Complete")
                
        log("\n--- FINAL REPORT ---")
        final_output = app.invoke(inputs)
        log(final_output["generation"])
        
        with open("final_audit_report.txt", "w") as f:
            f.write(final_output["generation"])
            
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
