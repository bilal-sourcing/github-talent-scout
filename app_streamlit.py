#!/usr/bin/env python3
import streamlit as st
import os

st.set_page_config(page_title="🔍 GitHub Talent Scout", page_icon="🔍", layout="wide")
st.markdown("# 🔍 GitHub Talent Scout\nFind tech candidates that match your requirements.")

st.sidebar.markdown("## ⚙️ Search Configuration")
token = st.sidebar.text_input("GitHub Token", type="password", help="Get from https://github.com/settings/tokens")
jd = st.sidebar.text_area("Job Description", height=150, placeholder="Senior Backend Engineer with 6+ years\nMUST HAVE: Python, Django, PostgreSQL, Docker\nNICE TO HAVE: Kubernetes, Redis, AWS")
location = st.sidebar.text_input("Location", value="global", help="global, bangalore, london, etc.")

if st.sidebar.button("🚀 Find Candidates", type="primary", use_container_width=True):
    # Validation
    if not token or len(token) < 20:
        st.error("❌ Invalid GitHub token. Get one from https://github.com/settings/tokens")
        st.stop()
    elif not jd or len(jd) < 20:
        st.error("❌ Job description too short. Please provide more details.")
        st.stop()
    
    os.environ['GITHUB_TOKEN'] = token
    
    try:
        from ultimate_recruiting_engine_v9_5_BIO_OR_REPO import (
            deconstruct_jd_intelligent, get_skills_database, 
            search_github_typo_proof, score_candidates_elite, parse_location_input
        )
        
        # Step 1: Analyze JD
        st.info("🔍 Step 1/4: Analyzing job description...")
        jd_analysis = deconstruct_jd_intelligent(jd)
        st.success("✅ Analysis complete!")
        
        # Display JD Analysis
        st.markdown("---")
        st.markdown("## 📊 Job Requirements Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            role = jd_analysis.get('role_type', 'Unknown').replace('_', ' ')
            st.metric("🎯 Role", role[:25])
        with col2:
            must_have_count = len(jd_analysis.get('core_skills', []))
            st.metric("✅ Must-Have", must_have_count)
        with col3:
            nice_count = len(jd_analysis.get('nice_to_have', []))
            st.metric("🎁 Nice-to-Have", nice_count)
        with col4:
            seniority = jd_analysis.get('seniority_level', 'Unknown')
            st.metric("📈 Seniority", seniority.replace('_', ' ')[:15])
        
        # Show skills
        st.markdown("### Skills Detected")
        skill_col1, skill_col2 = st.columns(2)
        
        with skill_col1:
            st.markdown("**MUST HAVE:**")
            must_skills = jd_analysis.get('core_skills', [])
            if must_skills:
                for skill in must_skills[:8]:
                    skill_name = skill.get('skill', skill) if isinstance(skill, dict) else skill
                    st.write(f"• {skill_name}")
            else:
                st.write("None detected")
        
        with skill_col2:
            st.markdown("**NICE TO HAVE:**")
            nice_skills = jd_analysis.get('nice_to_have', [])
            if nice_skills:
                for skill in nice_skills[:8]:
                    skill_name = skill.get('skill', skill) if isinstance(skill, dict) else skill
                    st.write(f"• {skill_name}")
            else:
                st.write("None detected")
        
        # Step 2: Get skills database
        st.info("⚡ Step 2/4: Loading skills database...")
        skills_db = get_skills_database()
        st.success("✅ Skills database loaded!")
        
        # Step 3: Search candidates
        st.warning("🔎 Step 3/4: Searching GitHub... (this may take 30-60 seconds, please wait)")
        progress_bar = st.progress(0)
        
        location_filter = parse_location_input(location)
        
        # Search with multiple keywords
        all_candidates = []
        search_terms = []
        
        if jd_analysis.get('core_skills'):
            search_terms.extend([s.get('skill', s) if isinstance(s, dict) else s for s in jd_analysis.get('core_skills', [])[:3]])
        
        if not search_terms:
            search_terms = ['python', 'engineer']
        
        for idx, term in enumerate(search_terms):
            try:
                st.write(f"  🔎 Searching for '{term}'...")
                candidates = search_github_typo_proof(term, location_filter)
                all_candidates.extend(candidates)
                progress_bar.progress(min((idx + 1) / len(search_terms), 0.9))
            except Exception as e:
                st.warning(f"⚠️ Error searching for '{term}': {str(e)}")
        
        # Deduplicate
        unique_candidates = {}
        for cand in all_candidates:
            username = cand.get('username')
            if username and username not in unique_candidates:
                unique_candidates[username] = cand
        
        candidates = list(unique_candidates.values())
        st.success(f"✅ Found {len(candidates)} candidates!")
        
        # Step 4: Score candidates
        st.info("⚡ Step 4/4: Scoring candidates...")
        
        if candidates:
            score_candidates_elite(candidates, jd_analysis, skills_db, location_filter)
            candidates = sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)[:20]
        
        progress_bar.progress(1.0)
        st.success("✅ Scoring complete!")
        
        # Display Results
        st.markdown("---")
        st.markdown(f"## ✅ Top {len(candidates)} Candidates")
        
        if not candidates:
            st.warning("⚠️ No candidates found. Try adjusting your search criteria.")
        else:
            # Create candidate cards
            for idx, candidate in enumerate(candidates, 1):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        username = candidate.get('username', 'Unknown')
                        score = int(candidate.get('score', 0))
                        
                        # Score color
                        if score >= 90:
                            score_emoji = "🟢"
                        elif score >= 80:
                            score_emoji = "🟡"
                        else:
                            score_emoji = "🔴"
                        
                        st.markdown(f"### #{idx}. [{score_emoji} @{username}](https://github.com/{username})")
                    
                    with col2:
                        st.metric("Score", f"{score}/100")
                    
                    with col3:
                        bio = candidate.get('bio', 'N/A')
                        if bio and bio != 'N/A':
                            st.caption(f"📝 {bio[:40]}...")
                    
                    # Stats
                    st.write(f"👥 **{candidate.get('followers', 0)} followers** | 📦 **{candidate.get('repos', 0)} repos** | ⭐ **{candidate.get('stars', 0)} stars**")
                    
                    # Location & Activity
                    location_val = candidate.get('location', 'Unknown')
                    activity = candidate.get('last_activity', 'Unknown')
                    st.write(f"📍 {location_val} | ⏰ {activity}")
                    
                    # GitHub Link
                    st.markdown(f"[🔗 View Full GitHub Profile](https://github.com/{username})")
        
        # Clear token
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Tips:\n- Make sure your GitHub token is valid\n- Check your internet connection\n- Try a simpler job description")
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']

else:
    # Welcome screen
    st.markdown("""
    ### 👋 Welcome to GitHub Talent Scout!
    
    **Find tech candidates that match your job requirements in minutes.**
    
    #### How to use:
    1. **Get GitHub Token** - Create one at https://github.com/settings/tokens
    2. **Paste your job requirements** - Use MUST HAVE / NICE TO HAVE format
    3. **Click "Find Candidates"** - Wait 30-60 seconds for results
    
    #### Example Job Description:
    ```
    Senior Backend Engineer with 6+ years experience.
    MUST HAVE: Python, Django, PostgreSQL, Docker, REST APIs.
    NICE TO HAVE: Kubernetes, Redis, AWS, GraphQL.
    ```
    
    #### Features:
    ✅ Searches 100,000+ GitHub profiles  
    ✅ Intelligent skill matching  
    ✅ 100-point scoring system  
    ✅ Works with ANY tech role  
    
    ---
    
    **Built with Claude AI + GitHub API**
    """)
