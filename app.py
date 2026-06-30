import streamlit as st
import json
import os
import pandas as pd

# 1. Page Configuration
st.set_page_config(
    page_title="Spotify Review Discovery Engine",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Spotify Styling Injection
st.markdown("""
<style>
    /* Hide Streamlit Header and Footer */
    header, [data-testid="stHeader"] {
        visibility: hidden !important;
        display: none !important;
    }
    footer, [data-testid="stFooter"] {
        visibility: hidden !important;
        display: none !important;
    }
    /* Global Background & Text */
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
    }
    .block-container, [data-testid="stAppViewBlockContainer"] {
        padding-bottom: 2rem !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #191414 !important;
        border-right: 1px solid #282828;
        transform: none !important;
        margin-left: 0px !important;
        width: 21rem !important;
        display: block !important;
        overflow: hidden !important;
    }

    /* Force the inner scroll container to remain visible and fully sized on all screen widths */
    section[data-testid="stSidebar"] > div {
        transform: none !important;
        margin-left: 0px !important;
        width: 100% !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] * {
        visibility: visible !important;
        opacity: 1 !important;
    }

    /* Hide sidebar collapse/expand buttons on all screen widths */
    .ef3psqc5, .ef3psqc4, [data-testid="collapsedControl"], section[data-testid="stSidebar"] button, [aria-label="Close sidebar"], [aria-label="Expand sidebar"], [aria-label="Open sidebar"] {
        display: none !important;
    }

    /* Position main content next to the permanent sidebar */
    .main {
        margin-left: 21rem !important;
    }
    section[data-testid="stSidebar"] > div,
    [data-testid="stSidebarUserContent"] {
        overflow-y: hidden !important;
        scrollbar-width: none !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0.5rem !important;
    }
    section[data-testid="stSidebar"] > div::-webkit-scrollbar,
    [data-testid="stSidebarUserContent"]::-webkit-scrollbar {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
    }


    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] h2 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stImage"] {
        margin-bottom: 0px !important;
    }
    /* Headers styling */
    h1, h2, h3 {
        color: #1DB954 !important;
        font-weight: 700;
    }
    .main-title {
        font-size: 2.8rem;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        color: #B3B3B3;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    /* Card / Block styling */
    .pm-card {
        background-color: #181818;
        border-left: 4px solid #1DB954;
        padding: 1.5rem;
        border-radius: 6px;
        margin-bottom: 1.5rem;
    }
    .pm-card-title {
        color: #1DB954;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
    }
    .pm-card-content {
        color: #E5E5E5;
        font-size: 1rem;
        line-height: 1.6;
    }
    .quote-box {
        background-color: #282828;
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        font-style: italic;
        color: #FFFFFF;
        border-left: 3px solid #B3B3B3;
    }
</style>
""", unsafe_allow_html=True)

# 3. Helpers to Load Data
@st.cache_data
def load_question_data(q_idx: int) -> dict:
    filepath = f"data/analysis/q{q_idx}/pm_research_question_answers.json"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data[0]
    return {}

# 4. Header Bar
st.markdown('<h1 class="main-title">🎵 Spotify Review Discovery Engine</h1>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Product Management Fellowship Research Dashboard</div>', unsafe_allow_html=True)

# 5. Sidebar Setup
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=80)
st.sidebar.markdown("## Navigation")

question_options = {
    1: "Q1: Why do users struggle to discover new music?",
    2: "Q2: Frustrations with recommendations",
    3: "Q3: Achieved listening behaviors",
    4: "Q4: Causes of repetitive listening",
    5: "Q5: User segment challenges",
    6: "Q6: Consistent unmet needs"
}

st.sidebar.markdown("Select PM Research Question")
selected_q_idx = st.sidebar.selectbox(
    "Select PM Research Question",
    options=list(question_options.keys()),
    format_func=lambda x: question_options[x],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("## Database Statistics")
st.sidebar.metric(label="Total Raw Reviews Ingested", value="5,000")

st.sidebar.markdown("""
**Source Platforms:**
- App Store reviews
- Play Store reviews
- Reddit discussions
- Spotify Community forums
- Social media conversations
""")


# 6. Load data for the selected question
q_data = load_question_data(selected_q_idx)

if not q_data:
    st.error(f"Error: Data for Question {selected_q_idx} not found. Please run the analysis script first.")
else:
    # 7. Main Panel
    st.markdown(f"## {q_data['question_id']}: {q_data['question']}")
    st.markdown("---")

    # Layout for PM Synthesis (stacked full-width/landscape)
    st.markdown(f"""
    <div class="pm-card" style="border-left-color: #1DB954;">
        <div class="pm-card-title" style="color: #1DB954;">📌 Conclusion</div>
        <div class="pm-card-content" style="font-weight: 500; font-size: 1.15rem; line-height: 1.6;">{q_data['conclusion']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="pm-card" style="border-left-color: #2D96FF;">
        <div class="pm-card-title" style="color: #2D96FF;">📖 Detailed Explanation</div>
        <div class="pm-card-content" style="font-size: 0.98rem; line-height: 1.6;">
            <p style="margin-bottom: 0.8rem;"><strong>Answer:</strong> {q_data['answer']}</p>
            <p style="margin-bottom: 0.8rem;"><strong>Why It Is Happening:</strong> {q_data['why_it_is_happening']}</p>
            <p style="margin-bottom: 0px;"><strong>Product Implication:</strong> {q_data['product_implication']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


    # 8. Platform Breakdown & Charts
    st.markdown("### Platform Evidence Breakdown")
    breakdown = q_data['platform_breakdown']
    
    # Display metrics bar
    m_cols = st.columns(5)
    platforms_names = list(breakdown.keys())
    for idx, p_name in enumerate(platforms_names):
        with m_cols[idx]:
            label = p_name.replace("_", " ").title()
            val = breakdown[p_name]
            st.metric(label=label, value=f"{val} reviews")

    # Simple chart of platform distribution
    df_breakdown = pd.DataFrame({
        "Platform": [p.replace("_", " ").title() for p in breakdown.keys()],
        "Review Count": list(breakdown.values())
    })
    st.bar_chart(df_breakdown.set_index("Platform"), color="#1DB954")

    # 9. Key Themes & Quotes
    st.markdown("---")
    st.markdown("### Key Themes & Representative User Quotes")

    themes = q_data.get('themes', [])
    for theme in themes:
        theme_name = theme['theme_name']
        theme_summary = theme['theme_summary']
        review_count = theme['review_count']
        quotes = theme.get('representative_quotes', [])
        platforms = [p.replace("_", " ").title() for p in theme.get('platforms_seen', [])]

        with st.expander(f"✨ Theme: {theme_name} ({review_count} reviews) - Seen on: {', '.join(platforms)}"):
            st.markdown(f"**Theme Summary:** {theme_summary}")
            st.markdown("**Representative User Quotes:**")
            if not quotes:
                st.write("*No representative quotes found for this theme.*")
            for q in quotes:
                st.markdown(f'<div class="quote-box">"{q.strip()}"</div>', unsafe_allow_html=True)

    # 10. Review Explorer Tab
    st.markdown("---")
    st.markdown("### 🔍 Raw Reviews & Comments Explorer")
    
    selected_platform = st.selectbox(
        "Filter reviews by Platform Source:",
        options=list(breakdown.keys()),
        format_func=lambda x: x.replace("_", " ").title()
    )

    matched_reviews = q_data.get('matched_reviews', [])
    filtered_reviews = [r for r in matched_reviews if r['source_platform'] == selected_platform]

    if not filtered_reviews:
        st.write("*No matched reviews found for this platform under this question.*")
    else:
        st.write(f"Showing {len(filtered_reviews)} matching reviews:")
        
        # Paginate or list them inside expandable sections
        max_display = min(15, len(filtered_reviews))
        for r_idx in range(max_display):
            rev = filtered_reviews[r_idx]
            title = rev.get('title', '').strip()
            rating_str = f" ⭐ {rev['rating']}/5" if rev.get('rating') else ""
            date_str = rev.get('published_at', '')[:10]
            header = f"Review #{r_idx+1} ({date_str}){rating_str}"
            if title:
                header += f" - \"{title}\""
            
            with st.expander(header):
                st.write(rev['raw_text'])
                st.markdown(f"**Source URL:** [Link]({rev['source_url']})")



# 12. Strategic Footer
st.markdown(
    "<div style='text-align: center; color: #888; padding: 10px;'>"
    "Spotify Review Discovery Engine &copy; 2026. Made with 💚 using Streamlit."
    "</div>",
    unsafe_allow_html=True
)
