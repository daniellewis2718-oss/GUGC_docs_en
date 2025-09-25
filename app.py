import json
from pathlib import Path
from typing import Dict, List, Any

import streamlit as st
import urllib.parse

BASE_PREFIX = "https://act-webstatic.hoyoverse.com/ugc-tutorial/knowledge/sea/en-us/"
BASE_SUFFIX = "/content.html"

st.set_page_config(page_title="HoYo Knowledge Linker", layout="wide")
st.title("HoYo Knowledge Linker")

st.caption("Build and open HoYoverse UGC Knowledge links from a title → real_id catalog.")

# --- Load data ---
def load_default_catalog() -> Any:
    p = Path(__file__).parent / "catalog.json"
    if p.exists():
        try:
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Could not parse bundled catalog.json: {e}")
    return None

uploaded = st.file_uploader("Upload catalog.json (optional)", type=["json"], help="If omitted, the app will try to use the bundled catalog.json in the repo.")
raw = None
if uploaded is not None:
    try:
        raw = json.load(uploaded)
    except Exception as e:
        st.error(f"Invalid JSON: {e}")
else:
    raw = load_default_catalog()

# --- Normalize / flatten ---
def walk(node: Dict[str, Any], crumbs: List[str], out: List[Dict[str, Any]]):
    title = str(node.get("title", "")).strip()
    real_id = str(node.get("real_id", "")).strip()
    if title and real_id:
        out.append({
            "title": title,
            "real_id": real_id,
            "crumbs": crumbs.copy()
        })
    for child in node.get("children", []) or []:
        walk(child, crumbs + ([title] if title else []), out)

def normalize(raw: Any) -> List[Dict[str, Any]]:
    flat: List[Dict[str, Any]] = []
    if raw is None:
        return flat
    if isinstance(raw, list):
        for root in raw:
            if isinstance(root, dict):
                walk(root, [], flat)
    elif isinstance(raw, dict):
        # Accept simple mapping: { "Title": "real_id" }
        # or nested dict with "children"
        if "title" in raw or "real_id" in raw or "children" in raw:
            walk(raw, [], flat)
        else:
            for k, v in raw.items():
                flat.append({"title": str(k), "real_id": str(v), "crumbs": []})
    return flat

flat = normalize(raw)

# --- Controls ---
left, mid, right = st.columns([2,1,1])
with left:
    q = st.text_input("Search by title", placeholder="Type to filter…").strip().lower()
with mid:
    sort_mode = st.radio("Sort", ["A→Z", "Z→A"], horizontal=True)
with right:
    st.metric("Items", len(flat))

# --- Filter/sort ---
rows = [r for r in flat if (q in r["title"].lower())] if q else flat[:]
rows.sort(key=lambda r: r["title"], reverse=(sort_mode=="Z→A"))

st.write("---")

# --- List ---
if not rows:
    st.info("No matches.")
else:
    for r in rows:
        url = f"{BASE_PREFIX}{urllib.parse.quote(r['real_id'])}{BASE_SUFFIX}"
        col1, col2, col3 = st.columns([4,3,1])
        with col1:
            title_line = r["title"]
            if r.get("crumbs"):
                title_line += "  ·  " + " › ".join(r["crumbs"])
            st.markdown(f"**[{title_line}]({url})**")
        with col2:
            st.code(r["real_id"], language=None)
        with col3:
            st.markdown(f"[Open link]({url})")

st.write("---")
st.caption("Pattern: https://act-webstatic.hoyoverse.com/ugc-tutorial/knowledge/sea/en-us/<real_id>/content.html")
