import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import pypdfium2 as pdfium

st.set_page_config(page_title="CDP App", layout="wide")

dash = chr(45)

# Hardcoded league registry
LEAGUE_PRESETS = {
    "CDP (Crème Dellar Prem)": 63,
    "SDM (Segundo Del Mundo)": 320,
    "BDR (Best De La Rest)": 378,
    "LDE (Liger Del Eager)": 240
}

# Bind navigation directly to session state
if "page" not in st.session_state:
    st.session_state.page = "Home"

def render_pdf(filename, title):
    base_dir = Path(__file__).resolve().parent
    
    folder = base_dir / "Newsletters"
    if not folder.exists():
        folder = base_dir / "newsletters"
        
    if not folder.exists():
        st.error("Folder not found. Ensure either `Newsletters` or `newsletters` exists in your repository root.")
        return

    target = None
    for f in folder.iterdir():
        if f.is_file() and f.name.lower() == filename.lower():
            target = f
            break

    if not target or not target.exists():
        st.warning(f"Could not find `{filename}` inside `{folder.name}/`.")
        available = [f.name for f in folder.iterdir() if f.is_file()]
        if available:
            st.info(f"Files currently in `{folder.name}/`: {', '.join(available)}")
        return

    pdf_bytes = target.read_bytes()

    st.download_button(
        label=f"📥 Download {title} (PDF)",
        data=pdf_bytes,
        file_name=target.name,
        mime="application/pdf",
        use_container_width=True
    )

    try:
        pdf = pdfium.PdfDocument(pdf_bytes)
        for page_index in range(len(pdf)):
            page = pdf[page_index]
            image = page.render(scale=2).to_pil()
            st.image(image, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering PDF pages: {e}")

@st.cache_data(ttl=3600)
def fetch_fpl_static():
    url = f"https://draft.premierleague.com/api/bootstrap{dash}static"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

@st.cache_data(ttl=600)
def fetch_league_data(league_id):
    if not league_id:
        return None, None
    details_url = f"https://draft.premierleague.com/api/league/{league_id}/details"
    status_url = f"