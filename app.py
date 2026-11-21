"""Streamlit interface for EvidenceTrail."""
import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.evidencetrail.agent import ResearchAgent

load_dotenv(Path(__file__).parent / ".env")
st.set_page_config(page_title="EvidenceTrail", page_icon="🔎", layout="wide")
st.markdown("""<style>
.block-container {max-width: 1320px; padding-top: 2.5rem}
h1,h2,h3 {letter-spacing: -.03em}
h1 {font-size: 4rem !important}
h2 {font-size: 2rem !important}
div[data-testid='stMarkdown'] p, div[data-testid='stMarkdown'] li {font-size: 1.16rem; line-height: 1.6}
textarea, button, label {font-size: 1.12rem !important}
div[data-testid='stMetric'] {background: #101b2d; padding: 1rem; border-radius: .7rem}
div[data-testid='stToolbar'] {display: none}
</style>""", unsafe_allow_html=True)
st.title("EvidenceTrail")
st.caption("AI research with a visible evidence trail • Nebius Token Factory + Tavily")

ready = all(os.getenv(k, "").strip() for k in ("NEBIUS_API_KEY", "TAVILY_API_KEY", "NEBIUS_MODEL"))
if not ready:
    st.warning("Add NEBIUS_API_KEY, TAVILY_API_KEY, and NEBIUS_MODEL to .env before running a research task.")

question = st.text_area("Research question", "What does recent evidence say about the benefits and limitations of heat pumps in cold climates?", height=95)
run = st.button("Research with live sources", type="primary", disabled=not ready)
if run:
    trace_box = st.empty()
    seen = []
    def show_event(event):
        seen.append(f"**{event.step}** · {event.detail}")
        trace_box.markdown("\n\n".join(seen))
    try:
        with st.spinner("Planning, searching, checking evidence, and synthesizing…"):
            result = ResearchAgent().run(question, show_event)
        st.session_state["result"] = result.model_dump()
    except Exception as exc:
        st.error(str(exc))

if "result" in st.session_state:
    result = st.session_state["result"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Tavily searches", result["tavily_searches"])
    c2.metric("Sources", len(result["sources"]))
    c3.metric("Nebius calls", result["nebius_calls"])
    st.subheader("Research report")
    st.markdown(result["report"])
    st.subheader("Original sources")
    for source in result["sources"]:
        with st.expander(f'[{source["id"]}] {source["title"]}'):
            st.link_button("Open original source", source["url"])
            st.caption(source["url"])
            st.write(source["content"])
            st.caption("Search queries: " + " · ".join(source["queries"]))
    with st.expander("Reproducible research trace"):
        for event in result["trace"]:
            st.write(f'{event["at"]} · {event["step"]} · {event["detail"]}')
        st.download_button("Download JSON trace and report", json.dumps(result, indent=2, ensure_ascii=False), "evidencetrail-research.json", "application/json")
