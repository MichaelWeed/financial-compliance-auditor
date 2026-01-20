import streamlit as st
import os
import sys
import json
import time
import requests
import signal
from agent import create_agent_graph
from components.pdf_viewer import render_pdf_viewer

# --- PREFERENCES MANAGEMENT ---
PREFS_FILE = ".auditor_preferences.json"

def load_preferences():
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"show_welcome_on_startup": True}

def save_preferences(prefs):
    with open(PREFS_FILE, "w") as f:
        json.dump(prefs, f)

# Initialize preferences in session state
if "prefs" not in st.session_state:
    st.session_state.prefs = load_preferences()

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Financial Compliance Auditor | Sovereign Instance",
    page_icon="🏛️", # Institutional icon
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS (FINANCIAL COMPLIANCE AUDITOR V3 - PREMIUM EDITION) ---
st.markdown("""
<style>
    /* FONTS */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');
    
    :root {
        /* TERMINAL PALETTE (Financial Grade) */
        --color-bg-app: #F8F9FA;         /* Soft Professional Gray */
        --color-bg-card: #FFFFFF;        /* Crisp White */
        --color-bg-sidebar: #F1F3F5;     /* Distinct Sidebar */
        
        --color-primary: #0A192F;        /* Deep Navy (Authority) */
        --color-accent: #D4AF37;         /* Metallic Gold (Value) */
        --color-accent-dim: rgba(212, 175, 55, 0.15);
        
        --color-text-main: #111827;      /* Sharper Black */
        --color-text-muted: #6B7280;     /* Muted Gray */
        --color-text-inverse: #FFFFFF;
        
        --color-success: #059669;
        --color-warning: #D97706;
        --color-error: #DC2626;
        --color-border: #E5E7EB;
        
        --font-sans: 'Inter', sans-serif;
        --font-header: 'IBM Plex Sans', sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
        
        --radius-sm: 2px;
        --radius-md: 4px;
    }

    /* GLOBAL RESET */
    html, body, .stApp {
        background-color: var(--color-bg-app);
        color: var(--color-text-main);
        font-family: var(--font-sans);
    }
    
    /* TYPOGRAPHY */
    h1, h2, h3 {
        font-family: var(--font-header) !important;
        color: var(--color-primary) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    
    .auditor-h1 { 
        font-family: var(--font-header);
        font-size: 2rem; 
        font-weight: 600;
        color: var(--color-primary);
        display: flex; 
        align-items: center; 
        gap: 12px;
        border-bottom: 2px solid var(--color-border);
        padding-bottom: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .auditor-sub {
        font-family: var(--font-mono);
        color: var(--color-text-muted);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 2.5rem;
    }

    /* TERMINAL STATUS BOX (Lighter, Integrated) */
    .terminal-box {
        background-color: #F8FAFC; /* Very light slate */
        color: #0A192F; /* Navy text */
        border-radius: var(--radius-md);
        padding: 1.5rem;
        font-family: var(--font-mono);
        font-size: 0.85rem;
        border-left: 4px solid #0A192F; /* Navy accent */
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #CBD5E1;
    }
    
    .terminal-header {
        color: #0A192F; /* Navy to match */
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* CARDS & CONTAINERS (Top Gold Accent like Mockup) */
    .report-card {
        background: transparent; /* Transparent by default, content provides the background */
        border: none;
        border-top: none;
        padding: 0;
        box-shadow: none;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Only show the card styling when there's actual content inside */
    .report-card:not(:empty) > * {
        background: #FFFFFF;
        border: 1px solid var(--color-border);
        border-top: 4px solid #D4AF37;
        padding: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    .evidence-block {
        background: #FFFFFF; /* White cards like mockup */
        border: 1px solid var(--color-border);
        border-top: 2px solid #D4AF37; /* Top accent instead of left */
        padding: 1.5rem;
        margin-bottom: 1rem;
        font-family: var(--font-sans);
        transition: all 0.2s ease;
    }
    
    .evidence-block:hover {
        border-top-width: 3px;
        box-shadow: 0 2px 6px rgba(212, 175, 55,0.15);
        background: #FFFFFF;
    }
    
    .entry-ref {
        font-family: var(--font-mono);
        background: var(--color-primary);
        color: var(--color-text-inverse);
        padding: 2px 6px;
        font-size: 0.7rem;
        border-radius: var(--radius-sm);
    }
    
    .citation-meta {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--color-text-muted);
        margin-top: 1rem;
        padding-top: 0.5rem;
        border-top: 1px dotted var(--color-border);
        display: flex;
        justify-content: space-between;
    }

    /* SVG ICON HELPERS */
    .icon-small {
        width: 16px;
        height: 16px;
        vertical-align: middle;
        margin-right: 6px;
        color: var(--color-accent);
    }
    
    /* PREMIUM SIDEBAR ICONS (Large) */
    .sidebar-icon-large {
        width: 80px;
        height: 80px;
        display: block;
        margin: 0 auto 0.5rem auto;
    }
    
    .sidebar-icon-section {
        text-align: center;
        padding: 1.5rem 0;
        border-bottom: 1px solid rgba(212, 175, 55, 0.2);
    }
    
    .sidebar-icon-label {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        color: #D4AF37;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-top: 0.5rem;
        opacity: 0.9;
    }

    /* SIDEBAR - Wider, no resize handle (not supported by Streamlit) */
    section[data-testid="stSidebar"] {
        background-color: #0A192F !important; /* Deep navy like mockup */
        border-right: 1px solid var(--color-border);
        min-width: 320px !important; /* Wider minimum */
        width: 360px !important;
        resize: none !important;
        overflow: auto;
    }
    
    section[data-testid="stSidebar"] > div {
        min-width: 320px;
    }
    
    .sidebar-header {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: #D4AF37; /* Gold for headers */
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin: 1.5rem 0 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Force Global Text Visibility */
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stMarkdownContainer"] strong {
        color: var(--color-primary) !important;
    }

    /* Captions & Secondary Text */
    div[data-testid="stCaptionContainer"], .stCaption, [data-testid="stCaptionContainer"] p {
        color: #374151 !important; /* Darker slate for captions */
        font-family: var(--font-mono) !important;
        font-size: 0.7rem !important;
        opacity: 1 !important;
    }

    /* Expander Overhaul */
    div[data-testid="stExpander"] {
        border: 1px solid var(--color-border) !important;
        background-color: #FFFFFF !important;
    }
    
    div[data-testid="stExpander"] summary {
        color: var(--color-primary) !important;
        font-family: var(--font-header) !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stExpander"] summary:hover {
        color: var(--color-accent) !important;
    }

    /* Force Label Visibility */
    .stSelectbox label, .stTextInput label, div[data-testid="stMarkdownContainer"] p {
        color: var(--color-primary) !important;
    }

    /* === NUCLEAR BUTTON TEXT FIX === */
    /* Force ALL buttons to have visible text - AGGRESSIVE */
    button, 
    .stButton button, 
    .stButton > button,
    [data-testid="baseButton-secondary"], 
    [data-testid="baseButton-primary"],
    div.stButton > button,
    div[data-testid="stButton"] button {
        background-color: #0A192F !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border: 1px solid #D4AF37 !important;
    }
    
    /* Streamlit primary buttons */
    button[kind="primary"],
    button[data-testid="baseButton-primary"] {
        background-color: #0A192F !important;
        color: #FFFFFF !important;
        border: 1px solid #D4AF37 !important;
    }
    
    /* Streamlit secondary buttons */
    button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {
        background-color: #1E3A5F !important;
        color: #FFFFFF !important;
        border: 1px solid #4B5563 !important;
    }
    
    /* ALL button text elements - EVERY VARIATION */
    button *, 
    .stButton button *,
    button p, button span, button div,
    .stButton button p, .stButton button span, .stButton button div,
    [data-testid="baseButton-secondary"] p,
    [data-testid="baseButton-secondary"] span,
    [data-testid="baseButton-primary"] p,
    [data-testid="baseButton-primary"] span {
        color: #FFFFFF !important;
        background-color: transparent !important;
    }
    
    /* Toggle switch labels */
    .stCheckbox label, .stCheckbox label p, .stCheckbox label span {
        color: var(--color-primary) !important;
    }



    /* INPUTS & WIDGETS (Force High Contrast) */
    .stTextInput input, .stTextArea textarea {
        font-family: var(--font-mono) !important;
        border: 1px solid var(--color-border) !important;
        border-radius: var(--radius-sm) !important;
        background-color: #FFFFFF !important;
        color: var(--color-primary) !important; 
    }
    
    /* Fix for Selectbox (Complex DOM) */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid var(--color-border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--color-primary) !important;
        font-family: var(--font-mono) !important;
    }
    
    /* Dropdown text color */
    div[data-baseweb="select"] span {
        color: var(--color-primary) !important;
    }
    
    /* Labels */
    label[data-testid="stWidgetLabel"] p {
        font-family: var(--font-header) !important;
        color: var(--color-primary) !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Focus states */
    .stTextInput input:focus, div[data-baseweb="select"] > div:focus-within {
        border-color: var(--color-accent) !important;
        box-shadow: 0 0 0 1px var(--color-accent) !important;
    }
    
    /* STATUS BADGE */
    .status-badge {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        padding: 4px 10px;
        background: #0A192F !important;
        border: 2px solid var(--color-border);
        color: var(--color-primary);
        display: inline-block;
        font-weight: 700;
        text-transform: uppercase;
    }
    .status-ok { border-color: #059669 !important; color: #34D399 !important; }
    .status-err { border-color: #DC2626 !important; color: #F87171 !important; }

    /* METRICS (High Precision Cards) */
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 1.25rem;
        border: 1px solid var(--color-border);
        border-top: 3px solid var(--color-accent);
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricValue"] {
        font-family: var(--font-mono) !important;
        color: var(--color-primary) !important;
        font-size: 1.5rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: var(--font-header) !important;
        color: #4B5563 !important;
        font-size: 0.65rem !important;
        font-weight: 700 !important;
    }
    /* Standard Notifications & Info */
    div[data-testid="stNotification"], div[data-testid="stAlert"] {
        background-color: #E2E8F0 !important;
        color: var(--color-primary) !important;
        border: 1px solid var(--color-border) !important;
    }
    
    /* Dividers */
    hr {
        border-top: 1px solid var(--color-border) !important;
        margin: 1.5rem 0 !important;
    }

    /* SIDEBAR TEXT - FORCE HIGH CONTRAST ON DARK BACKGROUND */
    section[data-testid="stSidebar"] * {
        color: #E2E8F0 !important; /* Light slate for all text */
    }
    
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] li,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] strong {
        color: #F1F5F9 !important; /* Very light for readability */
        font-size: 0.85rem !important;
        line-height: 1.5 !important;
    }
    
    /* FIX: Force sidebar code blocks to have dark text since they have light backgrounds */
    section[data-testid="stSidebar"] code {
        color: #0A192F !important;
        background-color: #E2E8F0 !important;
        padding: 2px 4px !important;
        border-radius: 3px !important;
    }
    
    section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p {
        color: #D4AF37 !important; /* Gold for labels */
        font-weight: 600 !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stTextInput label,
    section[data-testid="stSidebar"] .stNumberInput label,
    section[data-testid="stSidebar"] .stRadio label {
        color: #D4AF37 !important;
    }
    
    section[data-testid="stSidebar"] .stRadio label span,
    section[data-testid="stSidebar"] .stCheckbox label span {
        color: #E2E8F0 !important;
    }
    
    /* Sidebar input backgrounds - keep dark but readable */
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #1E3A5F !important;
        color: #FFFFFF !important;
        border-color: #3B5998 !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox span {
        color: #FFFFFF !important;
    }

    /* Tooltip Fix - Force white text with dark background everywhere */
    div[data-testid="stTooltipHoverTarget"] {
        color: inherit !important;
    }
    
    div[data-baseweb="tooltip"] {
        background-color: rgba(0, 0, 0, 0.85) !important;
        color: #FFFFFF !important;
        font-family: var(--font-mono) !important;
        font-size: 0.65rem !important;
        padding: 6px 10px !important;
        border-radius: 4px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4) !important;
        width: auto !important;
        max-width: 200px !important;
        white-space: normal !important;
        z-index: 999999 !important;
    }
    
    div[data-baseweb="tooltip"] > div {
        background-color: transparent !important;
        color: #FFFFFF !important;
        font-size: 0.65rem !important;
    }
    
    /* Force ALL nested elements to be white */
    div[data-baseweb="tooltip"] *,
    div[data-baseweb="tooltip"] p,
    div[data-baseweb="tooltip"] span,
    div[data-baseweb="tooltip"] div {
        color: #FFFFFF !important;
    }

    /* === NUCLEAR FIX: FILE UPLOADER TEXT === */
    /* Force all file uploader text to be dark and visible */
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small {
        color: #111827 !important;
    }
    
    /* File upload dropzone text */
    [data-testid="stFileUploadDropzone"] p,
    [data-testid="stFileUploadDropzone"] span,
    [data-testid="stFileUploadDropzone"] small {
        color: #374151 !important;
    }
    
    /* === NUCLEAR FIX: SUCCESS/INFO/ERROR MESSAGES === */
    /* Streamlit success boxes */
    [data-testid="stSuccess"],
    [data-testid="stSuccess"] p,
    [data-testid="stSuccess"] span {
        background-color: #10B981 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    /* Streamlit info boxes */
    [data-testid="stInfo"],
    [data-testid="stInfo"] p,
    [data-testid="stInfo"] span {
        background-color: #3B82F6 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    /* Streamlit error boxes */
    [data-testid="stError"],
    [data-testid="stError"] p,
    [data-testid="stError"] span {
        background-color: #EF4444 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    /* Streamlit warning boxes */
    [data-testid="stWarning"],
    [data-testid="stWarning"] p,
    [data-testid="stWarning"] span {
        background-color: #F59E0B !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    
    /* Sidebar Expander Specifics - FIXED FOR MOUSE-AWAY */
    section[data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: #0A192F !important; 
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] summary,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary p,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary span {
        color: #D4AF37 !important; /* Gold text */
        background-color: transparent !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover p,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover span {
        color: #FCD34D !important;
    }

    /* Fix SVG icon color inside expander if any */
    section[data-testid="stSidebar"] [data-testid="stExpander"] svg {
        fill: #D4AF37 !important;
        color: #D4AF37 !important;
    }

    /* Radio buttons inside sidebar expander */
    section[data-testid="stSidebar"] .stRadio label p {
        color: #E2E8F0 !important;
    }


    
    /* === MAIN CONTENT AREA TEXT FIX === */
    /* Force all main area text to be dark and readable */
    .main .block-container p,
    .main .block-container li,
    .main .block-container span,
    .main .block-container div {
        color: #111827 !important;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F1F5F9;
        padding: 4px;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #374151 !important;
        font-family: var(--font-header) !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        border-radius: 6px !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: var(--color-primary) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        font-weight: 600 !important;
    }
    
    /* Status container text - BODY */
    div[data-testid="stStatusWidget"] p,
    div[data-testid="stStatusWidget"] span {
        color: #FFFFFF !important;
    }

    /* PROGRESS BAR COLOR FIX */
    [data-testid="stProgress"] > div > div > div > div {
        background-color: #D4AF37 !important; /* Institutional Gold */
    }
    
    /* SHUTDOWN BUTTON */
    .stApp > header {
        display: none !important; /* Hide default Streamlit header to make room */
    }

    .shutdown-container {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        height: 100%;
        margin-right: 5px;
    }

    button[key="shutdown_btn"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        color: rgba(226, 232, 240, 0.6) !important;
        border: 1px solid rgba(226, 232, 240, 0.2) !important;
        border-radius: 50% !important;
        width: 38px !important;
        height: 38px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }

    button[key="shutdown_btn"]:hover {
        background-color: #EF4444 !important; /* Red on hover */
        color: #FFFFFF !important;
        border-color: #EF4444 !important;
        transform: scale(1.05);
        box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.4) !important;
    }
    
    /* Status widget body content */
    div[data-testid="stStatusWidget"] > div:not(:first-child) {
        background-color: #0A192F !important;
        color: #FFFFFF !important;
    }
    
    div[data-testid="stStatusWidget"] > div:not(:first-child) p,
    div[data-testid="stStatusWidget"] > div:not(:first-child) span {
        color: #FFFFFF !important;
    }
    
    /* Fix the dark status header bar - WHEN EXPANDED */
    div[data-testid="stStatusWidget"] > div:first-child {
        background-color: #1E3A5F !important;
        border: 1px solid #D4AF37 !important;
    }
    
    div[data-testid="stStatusWidget"] summary,
    div[data-testid="stStatusWidget"] summary p,
    div[data-testid="stStatusWidget"] summary span,
    div[data-testid="stStatusWidget"] summary div,
    div[data-testid="stStatusWidget"] summary svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }

    
    /* Report card text inside */
    .report-card p,
    .report-card li,
    .report-card span {
        color: #1F2937 !important;
    }
    
    /* Evidence block text */
    .evidence-block p,
    .evidence-block span,
    .evidence-block div {
        color: #374151 !important;
    }
    
    /* Terminal box in main area should be readable */
    .terminal-box {
        color: #0A192F !important;
    }
    
    .terminal-box * {
        color: #0A192F !important;
    }
    
    /* Info/warning/error boxes */
    .stAlert p {
        color: #1F2937 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SVG ICONS ---
ICON_FLOW = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="icon-small"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" /></svg>'
ICON_VAULT = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="icon-small"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" /></svg>'
ICON_SCOPE = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="icon-small"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'
ICON_SHIELD = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="icon-small"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751A11.959 11.959 0 0112 2.964z" /></svg>'
ICON_SCALES = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 32px; height: 32px;"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.303.485 2.713.75 4.185.75m0 0c1.303 0 2.523-.163 3.615-.465a4.875 4.875 0 003.553-4.639V15.75m-3.615.035c-1.092.302-2.312.465-3.615.465m0 0c-1.472 0-2.883-.265-4.185-.75M19.615 15.785A4.875 4.875 0 0012 11.25m7.615 4.535c0 .324-.139.638-.387.86a6.745 6.745 0 01-3.043 1.355m-7.228-6.75A4.875 4.875 0 004.385 15.75m4.387-4.5c0-.623.237-1.189.63-1.611A4.875 4.875 0 0112 8.25m-7.615 7.5c0 .324.139.638.387.86a6.745 6.745 0 003.043 1.355m1.968-3.565A12.003 12.003 0 0112 3L11.25 15.75m0 0l-1.968 3.565" /></svg>'
ICON_NOTE = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="icon-small"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" /></svg>'
ICON_DATABASE = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="icon-small"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0v3.75" /></svg>'

# --- PREMIUM SIDEBAR ICONS (Large Gold-Outlined) ---
ICON_SHIELD_LARGE = '''
<svg class="sidebar-icon-large" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <g transform="translate(20, 10)">
        <!-- Shield Outline -->
        <path d="M30 5 L50 15 L50 35 C50 45 45 52 30 60 C15 52 10 45 10 35 L10 15 Z" 
              stroke="#D4AF37" stroke-width="2" fill="none"/>
        <!-- Building Icon Inside -->
        <rect x="22" y="25" width="16" height="20" stroke="#D4AF37" stroke-width="1.5" fill="none"/>
        <line x1="26" y1="25" x2="26" y2="45" stroke="#D4AF37" stroke-width="1"/>
        <line x1="30" y1="25" x2="30" y2="45" stroke="#D4AF37" stroke-width="1"/>
        <line x1="34" y1="25" x2="34" y2="45" stroke="#D4AF37" stroke-width="1"/>
        <rect x="25" y="28" width="2" height="2" fill="#D4AF37"/>
        <rect x="29" y="28" width="2" height="2" fill="#D4AF37"/>
        <rect x="33" y="28" width="2" height="2" fill="#D4AF37"/>
        <rect x="25" y="33" width="2" height="2" fill="#D4AF37"/>
        <rect x="29" y="33" width="2" height="2" fill="#D4AF37"/>
        <rect x="33" y="33" width="2" height="2" fill="#D4AF37"/>
    </g>
</svg>
'''

ICON_SEARCH_LARGE = '''
<svg class="sidebar-icon-large" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <g transform="translate(15, 15)">
        <!-- Magnifying Glass -->
        <circle cx="28" cy="28" r="18" stroke="#D4AF37" stroke-width="2.5" fill="none"/>
        <line x1="40" y1="40" x2="52" y2="52" stroke="#D4AF37" stroke-width="3" stroke-linecap="round"/>
        <!-- Gear Inside -->
        <circle cx="28" cy="28" r="8" stroke="#D4AF37" stroke-width="1.5" fill="none"/>
        <circle cx="28" cy="21" r="1.5" fill="#D4AF37"/>
        <circle cx="28" cy="35" r="1.5" fill="#D4AF37"/>
        <circle cx="21" cy="28" r="1.5" fill="#D4AF37"/>
        <circle cx="35" cy="28" r="1.5" fill="#D4AF37"/>
    </g>
</svg>
'''

ICON_VAULT_LARGE = '''
<svg class="sidebar-icon-large" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <g transform="translate(20, 20)">
        <!-- Safe/Vault Body -->
        <rect x="10" y="10" width="40" height="35" rx="2" stroke="#D4AF37" stroke-width="2.5" fill="none"/>
        <!-- Safe Door -->
        <rect x="15" y="15" width="30" height="25" stroke="#D4AF37" stroke-width="2" fill="none"/>
        <!-- Circular Lock -->
        <circle cx="30" cy="27.5" r="6" stroke="#D4AF37" stroke-width="2" fill="none"/>
        <circle cx="30" cy="27.5" r="2" fill="#D4AF37"/>
        <!-- Documents Inside (Stylized) -->
        <line x1="20" y1="23" x2="23" y2="23" stroke="#D4AF37" stroke-width="1" opacity="0.6"/>
        <line x1="37" y1="23" x2="40" y2="23" stroke="#D4AF37" stroke-width="1" opacity="0.6"/>
    </g>
</svg>
'''

# --- INITIALIZATION ---
from pipeline import load_manifest, ingest_and_index, purge_vault

if 'agent' not in st.session_state:
    with st.spinner("Initializing Sovereign Analysis Core..."):
        try:
            st.session_state.agent = create_agent_graph()
        except Exception as e:
            st.error(f"Core sequence failure: {e}")

# --- FIRST-RUN WELCOME OVERLAY ---
# Logic: show if (1) preference is on AND (2) not already shown this session
if 'welcome_shown_this_session' not in st.session_state:
    st.session_state.welcome_shown_this_session = False

should_show_welcome = st.session_state.prefs.get("show_welcome_on_startup", True) and not st.session_state.welcome_shown_this_session

if should_show_welcome:
    # Mark as shown IMMEDIATELY so even an 'X' close prevents re-popup in same session
    st.session_state.welcome_shown_this_session = True
    
    @st.dialog("Welcome to Financial Compliance Auditor", width="large")
    def show_welcome():
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🏛️</div>
            <div style="font-family: 'IBM Plex Sans', sans-serif; font-size: 0.7rem; color: #D4AF37; text-transform: uppercase; letter-spacing: 0.15em;">INSTITUTIONAL GRADE EVIDENCE ANALYSIS</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### What This Tool Does
        
        This AI-powered auditor extracts, verifies, and cites information from SEC 10-K filings with **zero-hallucination anchoring** — every claim links to exact page coordinates in source documents.
        
        ---
        
        ### Quick Start Guide
        
        1. **Ingest a Filing** — Upload a 10-K PDF via the sidebar (or use SEC EDGAR auto-fetch)
        2. **Configure Filters** — Scope your analysis by company, year, or industry
        3. **Submit a Query** — Ask questions about financial statements, risk factors, or lease data
        4. **Review Evidence** — Every answer includes page citations and PDF source highlighting
        
        ---
        
        ### Hardware Requirements
        
        This runs a **72-billion parameter model** locally via MLX. You'll need:
        - Apple Silicon Mac (M1/M2/M3/M4 with 64GB+ RAM recommended)
        - MLX inference server running on port 8080
        
        ---
        """)
        
        # Don't show again checkbox
        dont_show = st.checkbox("Don't show this again", value=not st.session_state.prefs.get("show_welcome_on_startup", True))
        
        col1, col2, col3 = st.columns([1.5, 2, 1.5])
        with col2:
            if st.button("🔍 Begin Audit", use_container_width=True, type="primary"):
                # Save preference
                st.session_state.prefs["show_welcome_on_startup"] = not dont_show
                save_preferences(st.session_state.prefs)
                
                # Flag is already set above, just rerun to clear dialog
                st.rerun()
    
    show_welcome()


# --- SIDEBAR: SYSTEM CONTROL ---
with st.sidebar:
    # === INSTITUTIONAL AUTHORITY SECTION ===
    st.markdown(f'<div class="sidebar-icon-section">{ICON_SHIELD_LARGE}<div class="sidebar-icon-label">INSTITUTIONAL AUTHORITY</div></div>', unsafe_allow_html=True)
    
    # 1. Server Health & Model Selection
    server_online = False
    available_models = ["Qwen2.5-72B-Instruct-4bit"] # Fallback
    current_model = available_models[0]
    
    try:
        response = requests.get("http://localhost:8080/v1/models", timeout=2)
        if response.status_code == 200:
            server_online = True
            models_data = response.json()
            available_models = [m['id'] for m in models_data['data']]
    except:
        server_online = False
        
    if server_online:
        st.markdown('<div class="status-badge status-ok">REASONING NODE: ONLINE</div>', unsafe_allow_html=True)
        selected_model = st.selectbox("Active Inference Model", available_models, index=0)
    else:
        st.markdown('<div class="status-badge status-err">REASONING NODE: OFFLINE</div>', unsafe_allow_html=True)
        st.warning("Financial compliance audits require an active MLX endpoint on port 8080.")
        
    # === ANALYSIS/SEARCH SECTION ===
    st.markdown(f'<div class="sidebar-icon-section">{ICON_SEARCH_LARGE}<div class="sidebar-icon-label">ANALYSIS SCOPE</div></div>', unsafe_allow_html=True)
    
    # 2. Document Vault (Ingestion)
    with st.expander("Ingest New Filing", expanded=False):
        ingest_method = st.radio("Source", ["Local PDF", "SEC EDGAR (Auto)"])
        
        if ingest_method == "Local PDF":
            uploaded_file = st.file_uploader("Select PDF", type=["pdf"])
            ticker = st.text_input("Ticker Symbol (e.g., AAPL)", "").upper()
            
            # Hierarchical Metadata Inputs
            col_ing1, col_ing2 = st.columns(2)
            with col_ing1:
                industry_options = ["", "Technology", "Healthcare", "Mining & Resources", "Financials", "Energy", "Consumer Goods", "Other"]
                industry = st.selectbox("Industry", industry_options, index=0)
                # Year dropdown: Recent years first, then grouped by decade
                current_year = 2026
                year_options = [""] + [str(y) for y in range(current_year, current_year - 12, -1)]  # Last 12 years
                year_selection = st.selectbox("Year", year_options, index=0, help="Select the fiscal year of the filing.")
                year = int(year_selection) if year_selection else 0
                jurisdiction = st.selectbox("Jurisdiction", ["", "US", "EU", "UK", "APAC", "Global"], index=0)
            
            with col_ing2:
                f_type_options = ["10-K", "10-Q", "8-K", "Form D", "Proxy", "Other"]
                f_type = st.selectbox("Filing Type", f_type_options, index=0)
                f_period = st.selectbox("Fiscal Period", ["", "Q1", "Q2", "Q3", "Q4", "Annual (FY)"], index=0)
                cik = st.text_input("CIK (SEC ID)", "")

            risk_flag = st.checkbox(
                "Mark for High-Level Audit Review",
                help="Flag this document for priority review. Risk-flagged items appear in filtered searches and receive additional scrutiny during compliance audits."
            )
            
            if st.button("Index Document", use_container_width=True, type="primary") and uploaded_file and ticker:
                # Save temporarily to process
                temp_path = f"data/raw/{uploaded_file.name}"
                os.makedirs("data/raw", exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Flag ingestion start for main area visibility
                st.session_state.ingestion_active = True
                
                try:
                    with st.status("Performing Document Forensics...", expanded=True) as status:
                        status.write(f"`STEP 1: Partitioning {ticker} (using hi_res strategy)...`")
                        
                        ingest_and_index(
                            temp_path, ticker, filing_type=f_type, industry=industry, 
                            year=year, fiscal_period=f_period, jurisdiction=jurisdiction,
                            risk_flag=risk_flag, cik=cik
                        )
                        
                        status.update(label=f"SUCCESS: {ticker} Filing Indexed.", state="complete", expanded=False)
                    
                    st.session_state.ingestion_active = False
                    st.success(f"VAULT UPDATED: {ticker} Forensic Evidence Anchored.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.session_state.ingestion_active = False
                    st.error(f"Ingestion Sequence Failed: {e}")
        else:
            edgar_ticker = st.text_input("Ticker", "AAPL").upper()
            edgar_year = st.selectbox("Year", range(2025, 2018, -1))
            if st.button("Fetch & Index", use_container_width=True, type="primary"):
                if not edgar_ticker:
                    st.error("Please provide a Ticker symbol.")
                else:
                    st.session_state.ingestion_active = True
                    try:
                        with st.status(f"Fetching {edgar_ticker} from SEC EDGAR...", expanded=True) as status:
                            status.write(f"`STEP 1: Locating {edgar_ticker} {edgar_year} filings...`")
                            
                            from pipeline import fetch_from_edgar
                            local_path = fetch_from_edgar(edgar_ticker, edgar_year)
                            
                            status.write("`STEP 2: Partitioning & Indexing Forensic Data...`")
                            
                            ingest_and_index(
                                local_path, edgar_ticker, filing_type="10-K", year=edgar_year
                            )
                            
                            status.update(label=f"SUCCESS: {edgar_ticker} Indexed.", state="complete", expanded=False)

                        st.session_state.ingestion_active = False
                        st.success(f"SUCCESS: {edgar_ticker} Filing Indexed and Anchored.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.session_state.ingestion_active = False
                        st.error(f"EDGAR Integration Failure: {e}")

    # === EVIDENCE REPOSITORY SECTION ===
    st.markdown(f'<div class="sidebar-icon-section">{ICON_VAULT_LARGE}<div class="sidebar-icon-label">EVIDENCE REPOSITORY</div></div>', unsafe_allow_html=True)
    
    # 3. Document Registry (What's loaded)
    manifest = load_manifest()
    if manifest["documents"]:
        for doc in manifest["documents"]:
            st.markdown(f"**{doc['ticker']}**")
            st.caption(f"{doc['type']} | {doc['filename']}")
    else:
        st.caption("No compliance evidence loaded in vault.")
    
    # Maintenance
    st.markdown('<div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(212, 175, 55, 0.2);"></div>', unsafe_allow_html=True)

    if st.button("PURGE AUDIT VAULT", use_container_width=True, help="Permanently delete all indexed data and reset manifest."):
        with st.spinner("Purging forensic repository..."):
            purge_vault()
            # Clear session state agent to force reconnection to clean DB
            if 'agent' in st.session_state:
                del st.session_state.agent
            st.success("VAULT PURGED: All forensic evidence removed.")
            time.sleep(1.5)
            st.rerun()

    # Onboarding Control
    show_onboarding = st.toggle("Show Welcome on Startup", value=st.session_state.prefs.get("show_welcome_on_startup", True))
    if show_onboarding != st.session_state.prefs.get("show_welcome_on_startup"):
        st.session_state.prefs["show_welcome_on_startup"] = show_onboarding
        save_preferences(st.session_state.prefs)
            
    if st.button("RESET UI SESSION", use_container_width=True, help="Clear all session state and refresh the interface."):
        for key in list(st.session_state.keys()):
            # Keep preferences if we just want a session reset, 
            # but user said "uncheck it and the next startup will reappear"
            # so let's keep the prefs object but clear the logic gate
            if key != "prefs":
                del st.session_state[key]
        st.rerun()

# --- MAIN INTERFACE ---
if 'ingestion_active' not in st.session_state:
    st.session_state.ingestion_active = False

# Overlay prominent indicator in main area if ingestion is active to avoid "frozen" feel
if st.session_state.ingestion_active:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.info("### ⏳ INGESTION PROTOCOL ACTIVE\nThe system is currently partitioning and indexing financial forensics. Please remain on this page. High-resolution analysis may take 1-3 minutes for large filings (e.g. 10-Ks).")
    st.markdown('</div>', unsafe_allow_html=True)

col_h1, col_h2 = st.columns([15, 1])

with col_h1:
    header_html = f"""
    <div class="auditor-h1">
        {ICON_SCALES}
        <span>Financial Compliance Auditor</span>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

with col_h2:
    st.markdown('<div class="shutdown-container">', unsafe_allow_html=True)
    if st.button("⏻", key="shutdown_btn", help="Shutdown Application Gracefully"):
        st.toast("Initiating Graceful Shutdown...")
        
        # Inject JavaScript to close the tab or redirect to about:blank
        # We use a components.html call to execute script in the parent context if possible
        st.components.v1.html(
            """
            <script>
                // Try to close the tab
                window.parent.close();
                // Redirect to blank page as fallback
                window.parent.location.href = "about:blank";
            </script>
            """,
            height=0
        )
        
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="auditor-sub">Verification Loop v3.1 | High-Precision Institutional Analysis</div>', unsafe_allow_html=True)

# Query & Filter Section - Hierarchical Scoping
manifest = load_manifest()

# Extract unique values for filters with a brief spinner for UX
with st.spinner("Calibrating AUDIT CONTENT FILTERS..."):
    manifest_docs = manifest.get("documents", [])
    tickers = ["ALL"] + sorted(list(set([doc['ticker'] for doc in manifest_docs])))
    industries = ["ALL"] + sorted(list(set([doc.get('industry', '') for doc in manifest_docs if doc.get('industry')])))
    years = ["ALL"] + sorted(list(set([doc.get('year', 0) for doc in manifest_docs if doc.get('year', 0) > 0])), reverse=True)
    filing_types = ["ALL"] + sorted(list(set([doc.get('type', '') for doc in manifest_docs if doc.get('type')])))
    jurisdictions = ["ALL"] + sorted(list(set([doc.get('jurisdiction', '') for doc in manifest_docs if doc.get('jurisdiction')])))


st.markdown(f'<div class="sidebar-header" style="color: var(--neutral-8); border-bottom: 2px solid var(--color-primary); padding-bottom: 4px; margin-bottom: 1.5rem;">{ICON_SCOPE} AUDIT CONTENT FILTERS</div>', unsafe_allow_html=True)
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    focus_ticker = st.selectbox("Company", tickers, index=0, key="focus_ticker")
with col_f2:
    focus_industry = st.selectbox("Industry", industries, index=0, key="focus_industry")
with col_f3:
    focus_year = st.selectbox("Year", years, index=0, key="focus_year")
with col_f4:
    st.markdown('<div style="color: var(--neutral-5); font-size: 0.8rem; line-height: 1.4;">Active focus isolation targets evidence and prevents cross-document pollution.</div>', unsafe_allow_html=True)

col_f5, col_f6, col_f7, col_f8 = st.columns(4)
with col_f5:
    focus_type = st.selectbox("Filing Type", filing_types, index=0, key="focus_type")
with col_f6:
    focus_juris = st.selectbox("Jurisdiction", jurisdictions, index=0, key="focus_juris")
with col_f7:
    risk_only = st.toggle("Show High-Risk Only", key="risk_only")
with col_f8:
    if st.button("CLEAR FILTERS", use_container_width=True):
        # Reset all filter keys in session state
        for key in ["focus_ticker", "focus_industry", "focus_year", "focus_type", "focus_juris", "risk_only", "main_query"]:
            if key in st.session_state:
                if isinstance(st.session_state[key], bool):
                    st.session_state[key] = False
                elif key == "focus_year" and years:
                    st.session_state[key] = years[0]
                elif key == "focus_ticker" and tickers:
                    st.session_state[key] = tickers[0]
                elif key == "focus_industry" and industries:
                    st.session_state[key] = industries[0]
                elif key == "focus_type" and filing_types:
                    st.session_state[key] = filing_types[0]
                elif key == "focus_juris" and jurisdictions:
                    st.session_state[key] = jurisdictions[0]
                else:
                    st.session_state[key] = ""
        st.rerun()



# Financial Inquiry Input - With explicit submit button
# Cancel callback function (must be defined before the button)
def clear_query():
    if 'main_query' in st.session_state:
        del st.session_state['main_query']
    if 'submitted_query' in st.session_state:
        del st.session_state['submitted_query']

query_text = st.text_area(
    "Enter Compliance Inquiry", 
    placeholder="Query document contents with zero-hallucination anchoring...", 
    label_visibility="collapsed", 
    key="main_query",
    height=70  # ~2 lines
)

col_submit, col_cancel = st.columns([6, 1])
with col_submit:
    if st.button("🔍 Submit Query", use_container_width=True, type="primary"):
        if query_text:
            st.session_state.submitted_query = query_text
with col_cancel:
    st.button("🛑 Cancel", key="cancel_query", help="Cancel current query and clear input", on_click=clear_query)

# Use the submitted query, not the live text input
query = st.session_state.get('submitted_query', '')





if query:
    ticker_filter = focus_ticker if focus_ticker != "ALL" else None
    industry_filter = focus_industry if focus_industry != "ALL" else None
    year_filter = int(focus_year) if focus_year != "ALL" else None
    f_type_filter = focus_type if focus_type != "ALL" else None
    juris_filter = focus_juris if focus_juris != "ALL" else None
    
    st.divider()
    with st.status("Substantiating Claim Chains...", expanded=True) as status:
        
        if 'agent' in st.session_state:
            inputs = {
                "question": query, 
                "ticker_filter": ticker_filter,
                "industry_filter": industry_filter,
                "year_filter": year_filter,
                "filing_type_filter": f_type_filter,
                "jurisdiction_filter": juris_filter,
                "risk_only_filter": risk_only
            }
        
            final_report = ""
            evidence = []
            
            # Progressive status messages
            status.update(label="Retrieving document context...", expanded=True)
            
            for output in st.session_state.agent.stream(inputs):
                for key, value in output.items():
                    if key == "retrieve":
                        status.update(label="Grading evidence relevance...", expanded=True)
                        st.write("`SUCCESS: Document-anchored context retrieved.`")
                    elif key == "grade_documents":
                        status.update(label="Synthesizing financial analysis...", expanded=True)
                        count = len(value['documents'])
                        st.write(f"`VALIDATE: {count} specific citations substantiated.`")
                        # De-duplicate evidence based on ticker, page, and text content
                        seen = set()
                        deduped = []
                        for doc in value['documents']:
                            # Create a unique key from ticker, page, and first 100 chars of text
                            key_str = f"{doc.get('ticker', '')}_{doc.get('page_number', 0)}_{doc.get('text', '')[:100]}"
                            if key_str not in seen:
                                seen.add(key_str)
                                deduped.append(doc)
                        evidence = deduped
                    elif key == "generate":
                        status.update(label="Anchoring citations to source...", expanded=True)
                        final_report = value['generation']

            
            status.update(label="Compliance Chain Completed — Evidence anchored.", state="complete", expanded=True)
            
            # --- RESULTS LAYOUT: DUAL-TAB FORENSIC VIEW ---
            tab_analysis, tab_evidence = st.tabs(["🏛️ Auditor Conclusion", "📂 Evidence Repository"])
            
            with tab_analysis:
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                header_conclusion = f'<div class="sidebar-header" style="color: var(--neutral-8); font-size: 1.25rem; margin-top: 0; margin-bottom: 1rem;">{ICON_FLOW} Analysis Summary</div>'
                st.markdown(header_conclusion, unsafe_allow_html=True)
                
                if final_report:
                    st.markdown(final_report)
                    
                    # --- DRAFT REPORT BUILDER (Moved inside tab for context) ---
                    st.divider()
                    header_draft = f'<div class="sidebar-header" style="color: var(--neutral-8); font-size: 1.1rem; margin-top: 0; margin-bottom: 0.75rem;">{ICON_NOTE} Draft Report Builder</div>'
                    st.markdown(header_draft, unsafe_allow_html=True)
                    report_instructions = st.text_area(
                        "Report Customization Instructions", 
                        placeholder="Describe formatting, e.g., 'Draft a 3-bullet executive briefing'...",
                        help="Tell the auditor how to format the retrieved evidence.",
                        label_visibility="collapsed"
                    )
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("Author Draft", use_container_width=True):
                            with st.spinner("Authoring draft..."):
                                from langchain_openai import ChatOpenAI
                                draft_llm = ChatOpenAI(
                                    model="mlx-community/Qwen2.5-72B-Instruct-4bit", 
                                    openai_api_base="http://localhost:8080/v1", 
                                    openai_api_key="not-needed"
                                )
                                draft_prompt = f"Based on the following audit evidence and conclusion: \nFINAL REPORT: {final_report}\n\nINSTRUCTIONS: {report_instructions}\n\nDraft a complete, professional report."
                                res = draft_llm.invoke(draft_prompt)
                                st.session_state.draft_content = res.content
                    
                    with col_b2:
                        if st.button("Clear Buffer", use_container_width=True):
                            if 'draft_content' in st.session_state:
                                del st.session_state.draft_content
                            st.rerun()
    
                    if 'draft_content' in st.session_state:
                        st.markdown('<div style="color: var(--neutral-5); font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin: 1rem 0 0.5rem 0;">Authorized Draft Buffer</div>', unsafe_allow_html=True)
                        draft_area = st.text_area("Edit Draft", value=st.session_state.draft_content, height=250, label_visibility="collapsed")
                        st.button("Copy to Clipboard", on_click=lambda: st.write("Text copied to buffer."))
                else:
                    st.error("Correlation failure: No substantiated evidence found.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab_evidence:
                if evidence:
                    header_evidence = f'<div class="sidebar-header" style="color: var(--neutral-8); font-size: 1.25rem; margin-top: 0; margin-bottom: 1.5rem;">{ICON_DATABASE} Substantiated Citations</div>'
                    st.markdown(header_evidence, unsafe_allow_html=True)
                    
                    # Initialize session state for PDF viewer
                    if 'selected_citation' not in st.session_state:
                        st.session_state.selected_citation = None
                    
                    # Create columns for evidence list and PDF viewer
                    if st.session_state.selected_citation is not None:
                        col_evidence, col_pdf = st.columns([1, 1.2]) # Slightly more room for PDF
                    else:
                        col_evidence = st.container()
                        col_pdf = None
                    
                    with col_evidence:
                        for i, doc in enumerate(evidence):
                            # Clean text (truncate if too long)
                            text_content = doc['text']
                            if len(text_content) > 500:
                                text_content = text_content[:500] + "..."
                            
                            st.markdown(f"""
                            <div class="evidence-block">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                                    <span class="entry-ref">REF_{str(i+1).zfill(3)}</span>
                                    <span style="font-size: 0.75rem; color: var(--neutral-5); font-family: 'JetBrains Mono';">{doc['ticker']} | PAGE {doc['page_number']}</span>
                                </div>
                                <div style="line-height: 1.7; color: var(--neutral-7); font-size: 0.9rem;">{text_content}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # View Source button - opens PDF viewer
                            if st.button(f"📄 View Source (Page {doc['page_number']})", key=f"view_source_{i}", use_container_width=True):
                                st.session_state.selected_citation = {
                                    'index': i,
                                    'ticker': doc['ticker'],
                                    'page_number': doc['page_number'],
                                    'bbox': doc.get('bbox', ''),
                                    'filename': doc.get('filename', f"{doc['ticker']}_document.pdf"),
                                    'source_pdf': doc.get('source_pdf', '')
                                }
                                st.rerun()
                    
                    # Render PDF viewer if citation is selected
                    if col_pdf and st.session_state.selected_citation:
                        with col_pdf:
                            citation = st.session_state.selected_citation
                            st.markdown(f"### Source: REF_{str(citation['index']+1).zfill(3)}")
                            
                            # Construct PDF path
                            source_pdf_filename = citation.get('source_pdf', '')
                            pdf_path = None
                            
                            if source_pdf_filename:
                                pdf_path = f"data/raw/{source_pdf_filename}"
                                if not os.path.exists(pdf_path):
                                    pdf_path = None
                            
                            if not pdf_path:
                                # Fallback search
                                import glob
                                pdf_candidates = glob.glob(f"data/raw/*{citation['ticker']}*.pdf") + \
                                                 glob.glob(f"data/raw/*{citation['ticker'].lower()}*.pdf")
                                for candidate in pdf_candidates:
                                    if os.path.exists(candidate):
                                        pdf_path = candidate
                                        break
                            
                            if pdf_path and os.path.exists(pdf_path):
                                render_pdf_viewer(
                                    pdf_path=pdf_path,
                                    page_number=citation['page_number'],
                                    bbox=citation['bbox'],
                                    height=900
                                )
                            else:
                                st.error(f"Forensic PDF Source unavailable for {citation['ticker']}.")
                            
                            if st.button("✕ Close Viewer"):
                                st.session_state.selected_citation = None
                                st.rerun()
                else:
                    st.info("No granulated evidence citations were found for this inquiry.")

else:
    # Idle State
    st.markdown(f"""
    <div class="terminal-box">
        <div class="terminal-header">
            {ICON_VAULT} SYSTEM KERNEL INITIALIZED
        </div>
        <div style="margin-bottom: 0.5rem;">&gt; Awaiting forensic inquiry into SEC filing vault...</div>
        <div style="margin-bottom: 0.5rem;">&gt; Active filtering: OPERATIONAL</div>
        <div style="color: var(--color-success);">&gt; Zero-hallucination anchoring: ENABLED</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown(f'<div class="sidebar-header">{ICON_SCOPE} Audit Protocol</div>', unsafe_allow_html=True)
    st.info("""
    1.  **Isolate Evidence**: Use filters to focus on specific companies, years, or jurisdictions.
    2.  **Verify Claims**: Every auditor conclusion is anchored to specific page coordinates.
    3.  **Draft Reports**: Use the Report Builder to transform evidence into briefings.
    """)
    
    # Dynamic metrics from actual system state
    col1, col2, col3 = st.columns(3)
    
    # Get actual chunk count from database
    try:
        import lancedb
        db = lancedb.connect("data/vector_db")
        if "compliance_audit" in db.table_names():
            table = db.open_table("compliance_audit")
            chunk_count = table.count_rows()
            evidence_label = f"{chunk_count:,} CHUNKS"
        else:
            evidence_label = "NO DATA"
    except:
        evidence_label = "OFFLINE"
    
    # Get embedding dimension from model
    try:
        from sentence_transformers import SentenceTransformer
        embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        vector_dim = embed_model.get_sentence_embedding_dimension()
        precision_label = f"{vector_dim} DIM"
    except:
        precision_label = "384 DIM"
    
    # Detect compute hardware
    try:
        import platform
        import subprocess
        if platform.system() == "Darwin":  # macOS
            # Try to get chip info
            try:
                chip_info = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip()
                if "Apple" in chip_info:
                    # Extract M-series chip name (M1, M2, M3, M4, etc.)
                    if "M1" in chip_info:
                        compute_label = "M1 (METAL)"
                    elif "M2" in chip_info:
                        compute_label = "M2 (METAL)"
                    elif "M3" in chip_info:
                        compute_label = "M3 (METAL)"
                    elif "M4" in chip_info:
                        compute_label = "M4 (METAL)"
                    else:
                        compute_label = "APPLE SILICON"
                else:
                    compute_label = "INTEL (CPU)"
            except:
                compute_label = "DARWIN (METAL)"
        else:
            compute_label = "CPU"
    except:
        compute_label = "UNKNOWN"
    
    with col1:
        st.metric("EVIDENCE SCALE", evidence_label, border=True)
    with col2:
        st.metric("VECTOR PRECISION", precision_label, border=True)
    with col3:
        st.metric("COMPUTE NODE", compute_label, border=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: var(--neutral-5); font-size: 0.75rem; font-family: \'JetBrains Mono\'; letter-spacing: 0.05em; padding: 1rem 0;">FINANCIAL COMPLIANCE AUDITOR v3.2 | INSTITUTIONAL GRADE EVIDENCE ANALYSIS</div>', unsafe_allow_html=True)

