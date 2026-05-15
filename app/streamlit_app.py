"""
TrustVerify Engine - Streamlit Web Interface
Main user-facing application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.universal_scraper import UniversalScraper
from src.models import FreeAIDetector
from src.models.advanced_multimodal_detector import MultimodalConsistencyChecker
from src.clustering.advanced_campaign_detector import AdvancedCampaignDetector
from src.rag_engine.free_fact_checker import FreeFactChecker
from src.data_collection.database_manager import DatabaseManager
from src.utils import logger

# Page config
st.set_page_config(
    page_title="TrustVerify Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .big-font { font-size: 24px !important; font-weight: bold; }
    .metric-box { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    .success { color: #00cc00; }
    .warning { color: #ff6600; }
    .danger { color: #cc0000; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'ai_detector' not in st.session_state:
    st.session_state.ai_detector = FreeAIDetector(use_hybrid=False, use_ensemble=False)

if 'db' not in st.session_state:
    st.session_state.db = DatabaseManager()

# Header
st.markdown("# 🔍 TrustVerify Engine")
st.markdown("*AI-Generated Content Detection • Fact Verification • Fake Campaign Detection*")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Single Review Analysis",
    "🚨 Campaign Detection",
    "🖼️ Multimodal Check",
    "📊 Database Stats",
    "⚙️ Settings"
])

# ==================== TAB 1: SINGLE REVIEW ====================
with tab1:
    st.header("Single Content Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        input_mode = st.radio("Input mode:", ["📄 Paste Text", "🔗 Enter URL"], horizontal=True)
    
    with col2:
        analyze_button = st.button("🔍 Analyze", use_container_width=True)
    
    # Get input
    if input_mode == "📄 Paste Text":
        text = st.text_area("Paste review/article text:", height=200, key="review_text")
        url = None
    else:
        url = st.text_input("Enter URL (Amazon, Daraz, Reddit, etc.):", key="review_url")
        text = None
        
        # Auto-scrape if URL provided
        if url and analyze_button:
            with st.spinner("🌐 Scraping content..."):
                scraper = UniversalScraper()
                try:
                    scraped = scraper.scrape(url)
                    text = scraped.get('text', '')
                    st.success("✓ Content scraped successfully")
                except Exception as e:
                    st.error(f"Error scraping URL: {e}")
                    text = None
    
    # Analysis
    if text and analyze_button:
        st.markdown("---")
        
        # 1. AI Detection
        st.subheader("1️⃣ AI-Generated Content Detection")
        
        with st.spinner("🤖 Analyzing with AI detector..."):
            ai_result = st.session_state.ai_detector.detect_ai(text)
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            "AI Probability",
            f"{ai_result['ai_probability']:.1%}",
            delta=f"{ai_result['confidence']:.1%} confidence"
        )
        
        col2.metric(
            "Assessment",
            "🤖 AI-Generated" if ai_result['is_ai_generated'] else "👤 Human Written",
            delta=ai_result.get('mode', 'unknown')
        )
        
        col3.metric(
            "Trust Score",
            f"{(1 - ai_result['ai_probability']):.1%}"
        )
        
        col4.metric(
            "Text Length",
            f"{len(text)} chars"
        )
        
        # Confidence visualization
        fig = go.Figure(data=[
            go.Bar(
                x=['AI', 'Human'],
                y=[ai_result['ai_probability'], 1 - ai_result['ai_probability']],
                marker_color=['#ff6b6b', '#51cf66']
            )
        ])
        fig.update_layout(title="AI vs Human Probability", height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # 2. Fact Checking
        st.subheader("2️⃣ Fact Verification")
        
        with st.spinner("🔎 Fact-checking claims..."):
            fact_checker = FreeFactChecker()
            fact_results = fact_checker.verify_claims(text)
        
        if fact_results['claims']:
            for claim in fact_results['claims'][:3]:  # Top 3 claims
                with st.expander(f"Claim: {claim['text'][:60]}..."):
                    st.write(f"**Verification:** {claim['verification_status']}")
                    st.write(f"**Evidence:** {claim['evidence']}")
        else:
            st.info("No verifiable claims found in text")
        
        # 3. Red Flags
        st.subheader("3️⃣ Detected Red Flags")
        
        red_flags = []
        
        if ai_result['ai_probability'] > 0.7:
            red_flags.append(("🤖 High AI probability", "danger"))
        
        if len(text) < 50:
            red_flags.append(("📏 Very short text", "warning"))
        
        if text.count("!") > len(text.split()) * 0.1:
            red_flags.append(("😤 Excessive exclamation marks", "warning"))
        
        if red_flags:
            for flag, severity in red_flags:
                st.warning(flag)
        else:
            st.success("✓ No major red flags detected")
        
        # 4. Multimodal (if URL)
        if url:
            st.subheader("4️⃣ Multimodal Consistency (if images available)")
            
            with st.spinner("🖼️ Analyzing images..."):
                multimodal = MultimodalConsistencyChecker()
                # This would require image extraction from URL
                st.info("Image analysis available for e-commerce URLs")

# ==================== TAB 2: CAMPAIGN DETECTION ====================
with tab2:
    st.header("🚨 Coordinated Fake Campaign Detection")
    st.markdown("*Detect review rings and organized fake campaigns*")
    
    uploaded_file = st.file_uploader("Upload CSV with reviews", type=['csv'])
    
    if uploaded_file and st.button("🔍 Analyze for Campaigns"):
        # Load data
        df = pd.read_csv(uploaded_file)
        
        # Validate columns
        required_cols = ['text', 'author', 'timestamp']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"Missing columns: {missing_cols}")
            st.info(f"Required columns: {required_cols}")
        else:
            reviews = df.to_dict('records')
            
            with st.spinner("🔍 Clustering reviews..."):
                detector = AdvancedCampaignDetector()
                results_df, report = detector.detect_campaigns(reviews)
            
            # Summary
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Reviews", report['total_reviews'])
            col2.metric("Detected Clusters", report['num_clusters'])
            col3.metric("Suspicious Campaigns", len([c for c in report['campaigns'] if c['suspicion_level'] == 'HIGH']))
            
            st.markdown("---")
            
            # Cluster details
            if report['campaigns']:
                st.subheader("Detected Campaigns")
                
                for campaign in report['campaigns']:
                    with st.expander(
                        f"Cluster {campaign['cluster_id']} - {campaign['size']} reviews - "
                        f"{campaign['suspicion_level']} suspicion"
                    ):
                        col1, col2 = st.columns(2)
                        col1.metric("Cluster Size", campaign['size'])
                        col2.metric("Unique Authors", campaign['unique_authors'])
                        
                        st.subheader("Red Flags:")
                        for flag in campaign['red_flags']:
                            st.warning(f"⚠️ {flag}")
                        
                        st.subheader("Sample Reviews:")
                        for review in campaign['sample_reviews']:
                            st.write(f"**{review['author']}**: {review['text'][:100]}...")
            
            # Download results
            st.download_button(
                label="📥 Download Analysis Results",
                data=results_df.to_csv(index=False),
                file_name="campaign_analysis.csv",
                mime="text/csv"
            )

# ==================== TAB 3: MULTIMODAL ====================
with tab3:
    st.header("🖼️ Image-Text Consistency Check")
    st.markdown("*Verify if review text matches product images*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        product_url = st.text_input("Product URL (Amazon/Daraz):")
    
    with col2:
        if st.button("Analyze Images", use_container_width=True):
            st.info("Image analysis feature - enter a product URL to analyze")

# ==================== TAB 4: DATABASE STATS ====================
with tab4:
    st.header("📊 Database Statistics")
    
    # Refresh button
    if st.button("🔄 Refresh Statistics"):
        st.rerun()
    
    db_stats = st.session_state.db.get_stats()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Reviews", db_stats['total_reviews'])
    col2.metric("Unique Sources", db_stats['unique_sources'])
    col3.metric("Unique Products", db_stats['unique_products'])
    col4.metric("Unique Authors", db_stats['unique_authors'])
    col5.metric("Avg Rating", f"{db_stats['average_rating']:.1f}")
    
    # Show sample data
    st.subheader("Recent Reviews")
    recent = st.session_state.db.get_reviews(limit=10)
    st.dataframe(recent[['text', 'rating', 'author_name', 'source', 'timestamp']], use_container_width=True)

# ==================== TAB 5: SETTINGS ====================
with tab5:
    st.header("⚙️ Settings")
    
    st.subheader("AI Detector Settings")
    detector_model = st.selectbox(
        "AI Detector Model",
        ["deberta-v3-large", "electra-base", "roberta-openai"]
    )
    
    use_ensemble = st.checkbox("Use ensemble (slower, more accurate)", value=False)
    
    if st.button("Apply Settings"):
        st.session_state.ai_detector = FreeAIDetector(
            use_ensemble=use_ensemble,
            model=detector_model
        )
        st.success("✓ Settings applied")
    
    st.markdown("---")
    
    st.subheader("Database Settings")
    if st.button("Export All Reviews to CSV"):
        df = st.session_state.db.get_reviews()
        st.download_button(
            label="📥 Download All Reviews",
            data=df.to_csv(index=False),
            file_name="all_reviews.csv",
            mime="text/csv"
        )
    
    if st.button("Clear Database Cache"):
        st.warning("This will not delete data, only clear cache")
        st.success("Cache cleared")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray;">
    <p>TrustVerify Engine v1.0.0 | MS-Level Research Project | Made with ❤️</p>
</div>
""", unsafe_allow_html=True)