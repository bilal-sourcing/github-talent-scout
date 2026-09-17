#!/usr/bin/env python3
import streamlit as st
import os

st.set_page_config(page_title="🔍 GitHub Talent Scout", page_icon="🔍", layout="wide")
st.markdown("# 🔍 GitHub Talent Scout\nFind tech candidates in seconds.")

st.sidebar.markdown("## ⚙️ Search")
token = st.sidebar.text_input("GitHub Token", type="password", help="Get from https://github.com/settings/tokens")
jd = st.sidebar.text_area("Job Description", height=120, placeholder="Senior Backend Engineer...\nMUST HAVE: Python, Django...")
location = st.sidebar.text_input("Location", value="global")

if st.sidebar.button("🚀 Find Candidates", type="primary"):
    if not token or len(token) < 20:
        st.error("❌ Invalid GitHub token")
    elif not jd or len(jd) < 20:
        st.error("❌ Job description too short")
    else:
        os.environ['GITHUB_TOKEN'] = token
        try:
            from ultimate_recruiting_engine_v9_5_BIO_OR_REPO import (
                deconstruct_jd_intelligent, get_skills_database, 
                search_github_typo_proof, score_candidates_elite, parse_location_input
            )
            
            with st.spinner("🔍 Analyzing..."):
                jd_analysis = deconstruct_jd_intelligent(jd)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🎯 Role", jd_analysis.get('role_type', 'Unknown').replace('_', ' ')[:20])
            col2.metric("✅ Must", len(jd_analysis.get('core_skills', [])))
            col3.metric("🎁 Nice", len(jd_analysis.get('nice_to_have', [])))
            
            with st.spinner("🔎 Searching GitHub..."):
                skills_db = get_skills_database()
                location_filter = parse_location_input(location)
                candidates = search_github_typo_proof('python', location_filter)
            
            if candidates:
                score_candidates_elite(candidates, jd_analysis, skills_db, location_filter)
                candidates = sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)[:10]
            
            st.markdown(f"## ✅ Found {len(candidates)} Candidates")
            
            if candidates:
                for idx, c in enumerate(candidates, 1):
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        col1.markdown(f"### #{idx}. [@{c.get('username')}](https://github.com/{c.get('username')})")
                        col2.metric("Score", f"{int(c.get('score', 0))}/100")
                        st.write(f"👥 {c.get('followers', 0)} followers | 📦 {c.get('repos', 0)} repos | ⭐ {c.get('stars', 0)} stars")
                        st.markdown(f"[View Profile](https://github.com/{c.get('username')})")
        except Exception as e:
            st.error(f"Error: {str(e)}")

else:
    st.markdown("### How to use:\n1. Paste GitHub token\n2. Paste job description\n3. Click Find Candidates\n\n✅ Works with any tech role")
