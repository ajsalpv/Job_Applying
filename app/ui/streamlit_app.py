"""
Streamlit UI - Job Application Dashboard
"""
import streamlit as st
import requests
from typing import List, Dict, Any
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api"

# Page config
st.set_page_config(
    page_title="AI Job Application Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .job-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
    }
    .score-high { color: #4CAF50; font-weight: bold; }
    .score-medium { color: #FF9800; font-weight: bold; }
    .score-low { color: #F44336; font-weight: bold; }
    .stat-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if "jobs" not in st.session_state:
        st.session_state.jobs = []
    if "selected_jobs" not in st.session_state:
        st.session_state.selected_jobs = []
    if "current_page" not in st.session_state:
        st.session_state.current_page = "search"
    if "generated_content" not in st.session_state:
        st.session_state.generated_content = {}


def api_call(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make API call to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, params=data)
        else:
            response = requests.post(url, json=data)
        
        # Check if response is JSON
        if "application/json" in response.headers.get("Content-Type", ""):
            return response.json()
        else:
            st.error(f"Backend Error ({response.status_code}): {response.text[:200]}...")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to backend. Make sure FastAPI server is running.")
        return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def render_sidebar():
    """Render sidebar navigation"""
    st.sidebar.markdown("# 🎯 Job Agent")
    st.sidebar.divider()
    
    page = st.sidebar.radio(
        "Navigation",
        ["🔍 Search Jobs", "📋 My Applications", "📊 Statistics", "⚙️ Settings"],
        label_visibility="collapsed",
    )
    
    st.sidebar.divider()
    
    # Quick stats
    st.sidebar.markdown("### 📈 Quick Stats")
    stats = api_call("/applications/stats")
    if stats:
        col1, col2 = st.sidebar.columns(2)
        col1.metric("Applied", stats.get("total_applied", 0))
        col2.metric("Interviews", stats.get("interviews", 0))
    
    st.sidebar.markdown("### ⏰ Scheduler")
    sched_status = api_call("/scheduler/status")
    if sched_status:
        is_running = sched_status.get("running", False)
        interval = sched_status.get("interval_minutes", 30)
        
        status_color = "🟢" if is_running else "🔴"
        st.sidebar.write(f"Status: {status_color} {'Running' if is_running else 'Stopped'}")
        st.sidebar.write(f"Interval: {interval} mins")
        
        col1, col2 = st.sidebar.columns(2)
        if is_running:
            if col1.button("Stop"):
                api_call("/scheduler/stop", method="POST")
                st.rerun()
        else:
            if col1.button("Start"):
                api_call("/scheduler/start", method="POST")
                st.rerun()
    
    return page


def render_search_page():
    """Render job search page"""
    st.markdown('<h1 class="main-header">🔍 Find Your Next AI Role</h1>', unsafe_allow_html=True)
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            keywords = st.text_input(
                "🎯 Job Keywords",
                value="AI Engineer",
                placeholder="AI Engineer, ML Engineer, LLM Developer..."
            )
            locations = st.text_input(
                "📍 Locations",
                value="Bangalore, Remote",
                placeholder="Comma-separated locations"
            )
        
        with col2:
            platforms = st.multiselect(
                "🌐 Platforms",
                ["linkedin", "indeed", "naukri"],
                default=["linkedin", "indeed", "naukri"]
            )
            min_score = st.slider(
                "📊 Minimum Fit Score",
                0, 100, 70
            )
        
        submitted = st.form_submit_button("🚀 Search Jobs", use_container_width=True)
    
    if submitted:
        with st.spinner("🔍 Searching across platforms..."):
            result = api_call(
                "/jobs/search",
                method="POST",
                data={
                    "keywords": keywords,
                    "locations": [loc.strip() for loc in locations.split(",")],
                    "platforms": platforms,
                    "min_score": min_score,
                }
            )
            
            if result and result.get("success"):
                st.session_state.jobs = result.get("jobs", [])
                st.success(f"✅ Found {len(st.session_state.jobs)} matching jobs!")
            else:
                st.error("Search failed. Check backend logs.")
    
    # Display jobs
    if st.session_state.jobs:
        st.divider()
        st.subheader(f"📋 Found {len(st.session_state.jobs)} Jobs")
        
        # Select all checkbox
        select_all = st.checkbox("Select All Jobs")
        
        selected = []
        for job in st.session_state.jobs:
            col1, col2, col3 = st.columns([0.5, 3, 1])
            
            with col1:
                check = st.checkbox(
                    "Select",
                    key=job.get("job_url"),
                    value=select_all,
                    label_visibility="collapsed"
                )
                if check:
                    selected.append(job.get("job_url"))
            
            with col2:
                score = job.get("fit_score", 0)
                score_class = "score-high" if score >= 80 else "score-medium" if score >= 60 else "score-low"
                
                st.markdown(f"""
                **{job.get('role')}** at **{job.get('company')}**  
                📍 {job.get('location')} | 🌐 {job.get('platform')}  
                <span class="{score_class}">Score: {score}%</span>
                """, unsafe_allow_html=True)
            
            with col3:
                if st.button("🔗 View", key=f"view_{job.get('job_url')}"):
                    st.markdown(f"[Open Job]({job.get('job_url')})")
            
            st.divider()
        
        st.session_state.selected_jobs = selected
        
        # Action buttons
        if selected:
            st.success(f"✅ {len(selected)} jobs selected")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Generate Resume & Cover Letters", use_container_width=True):
                    with st.spinner("Generating content..."):
                        result = api_call(
                            "/jobs/approve",
                            method="POST",
                            data={"job_urls": selected}
                        )
                        if result and result.get("success"):
                            st.success("✅ Content generated! Check 'My Applications' tab.")
            
            with col2:
                if st.button("📋 Add to Tracking", use_container_width=True):
                    st.success("✅ Jobs added to tracking sheet!")


def render_applications_page():
    """Render applications management page"""
    st.markdown('<h1 class="main-header">📋 My Applications</h1>', unsafe_allow_html=True)
    
    # Get follow-ups
    followups = api_call("/applications/followups", data={"days_threshold": 7})
    
    if followups and followups.get("followups"):
        st.warning(f"⏰ {len(followups['followups'])} applications need follow-up!")
        
        with st.expander("View Follow-ups"):
            for f in followups["followups"]:
                st.markdown(f"""
                **{f.get('role')}** at **{f.get('company')}**  
                Applied: {f.get('applied_date')} ({f.get('days_since')} days ago)  
                Status: {f.get('status')}
                """)
                if st.button(f"Generate Follow-up Email", key=f"followup_{f.get('company')}"):
                    st.info("Follow-up email generation coming soon!")
                st.divider()
    # Valid Applications List
    st.subheader("📝 All Applications")
    all_apps = api_call("/applications")
    
    if all_apps and all_apps.get("applications"):
        apps = all_apps.get("applications", [])
        
        # Filter filters (Optional: Add search/filter here)
        
        for app in apps:
            with st.expander(f"{app.get('role')} at {app.get('company')} ({app.get('status')})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**📍 Location:** {app.get('location')}")
                    st.markdown(f"**📅 Applied:** {app.get('date')}")
                    st.markdown(f"**🌐 Platform:** {app.get('platform')}")
                    st.markdown(f"**🔗 URL:** [Link]({app.get('job_url')})")
                    
                    if app.get("notes"):
                        st.info(f"Notes: {app.get('notes')}")
                        
                with col2:
                    st.metric("Fit Score", f"{app.get('fit_score')}%")
                
                st.divider()
                
                # Interview Prep Section
                st.markdown("### 🎓 Interview Prep")
                
                tab1, tab2, tab3 = st.tabs(["💡 Prep Tips", "📚 Skills to Learn", "📄 Job Description"])
                
                with tab1:
                    if app.get("interview_prep"):
                        # Parse string representation (it might be raw text or list representation)
                        st.markdown(app.get("interview_prep"))
                    else:
                        st.write("No specific tips generated yet.")
                        
                with tab2:
                    if app.get("skills_to_learn"):
                        st.markdown(app.get("skills_to_learn"))
                    else:
                        st.write("No skill gaps identified.")
                        
                with tab3:
                    st.text(app.get("job_description"))
                    
    else:
        st.info("No applications tracked yet.")
    # Manual content generation
    st.subheader("📝 Generate Application Content")
    
    with st.form("content_form"):
        company = st.text_input("Company Name")
        role = st.text_input("Role/Title")
        job_desc = st.text_area("Job Description", height=200)
        
        col1, col2 = st.columns(2)
        with col1:
            gen_resume = st.form_submit_button("📄 Generate Resume Bullets")
        with col2:
            gen_cover = st.form_submit_button("✉️ Generate Cover Letter")
    
    if gen_resume and company and role and job_desc:
        with st.spinner("Generating optimized resume..."):
            result = api_call(
                "/resume/generate",
                method="POST",
                data={
                    "company": company,
                    "role": role,
                    "job_description": job_desc,
                }
            )
            if result:
                st.subheader("📄 Optimized Resume Bullets")
                for bullet in result.get("optimized_bullets", []):
                    st.markdown(f"• {bullet}")
                
                st.markdown("**Keywords included:**")
                st.write(", ".join(result.get("keywords_included", [])))
    
    if gen_cover and company and role and job_desc:
        with st.spinner("Generating cover letter..."):
            result = api_call(
                "/cover-letter/generate",
                method="POST",
                data={
                    "company": company,
                    "role": role,
                    "job_description": job_desc,
                }
            )
            if result:
                st.subheader("✉️ Cover Letter")
                st.markdown(result.get("cover_letter", ""))
                
                st.download_button(
                    "📥 Download Cover Letter",
                    result.get("cover_letter", ""),
                    file_name=f"cover_letter_{company}.txt",
                )


def render_stats_page():
    """Render statistics page"""
    st.markdown('<h1 class="main-header">📊 Application Statistics</h1>', unsafe_allow_html=True)
    
    stats = api_call("/applications/stats")
    
    if stats:
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="stat-card">', unsafe_allow_html=True)
            st.metric("Total Discovered", stats.get("total_discovered", 0))
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="stat-card">', unsafe_allow_html=True)
            st.metric("Applied", stats.get("total_applied", 0))
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="stat-card">', unsafe_allow_html=True)
            st.metric("Interviews", stats.get("interviews", 0))
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="stat-card">', unsafe_allow_html=True)
            st.metric("Offers", stats.get("offers", 0))
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Success rate
        success_rate = stats.get("success_rate", 0)
        st.subheader(f"📈 Success Rate: {success_rate}%")
        st.progress(success_rate / 100)
        
        # Status breakdown
        st.subheader("📊 Status Breakdown")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            - ✅ Applied: **{stats.get('total_applied', 0)}**
            - 🎤 Interviews: **{stats.get('interviews', 0)}**
            - 🎉 Offers: **{stats.get('offers', 0)}**
            """)
        
        with col2:
            st.markdown(f"""
            - ❌ Rejected: **{stats.get('rejected', 0)}**
            - 🕐 No Response: **{stats.get('no_response', 0)}**
            """)
    else:
        st.info("No statistics available. Start applying to see your progress!")


def render_settings_page():
    """Render settings page"""
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    st.subheader("👤 User Profile")
    
    with st.form("profile_form"):
        name = st.text_input("Name", value="Ajsal PV")
        email = st.text_input("Email", value="pvajsal27@gmail.com")
        phone = st.text_input("Phone", value="+91 7356793165")
        location = st.text_input("Location", value="Bangalore, India")
        
        st.subheader("🎯 Job Preferences")
        target_roles = st.text_input(
            "Target Roles (comma-separated)",
            value="AI Engineer, ML Engineer, Machine Learning Engineer"
        )
        experience = st.number_input("Years of Experience", min_value=0, max_value=10, value=1)
        
        if st.form_submit_button("Save Settings"):
            st.success("✅ Settings saved!")
    
    st.divider()
    
    st.subheader("🔌 API Configuration")
    with st.expander("API Settings & Health Check", expanded=True):
        st.text_input("Backend URL", value=API_BASE_URL, disabled=True)
        
        # Test connection
        if st.button("🔍 Run Comprehensive Health Check"):
            health = api_call("/health")
            state = api_call("/workflow/state")
            sched = api_call("/scheduler/status")
            
            if health:
                st.success("✅ Backend is reachable")
                st.json({
                    "health": health,
                    "scheduler": sched,
                    "workflow": state
                })
            else:
                st.error("❌ Cannot connect to backend. Please ensure you are running 'python run_server.py'")

        st.info("💡 **Tip for Windows:** If discovery fails with 'NotImplementedError', make sure you are NOT running via 'uvicorn' directly. Use 'python run_server.py' instead.")



def main():
    """Main application"""
    init_session_state()
    
    page = render_sidebar()
    
    if "Search" in page:
        render_search_page()
    elif "Applications" in page:
        render_applications_page()
    elif "Statistics" in page:
        render_stats_page()
    elif "Settings" in page:
        render_settings_page()


if __name__ == "__main__":
    main()
