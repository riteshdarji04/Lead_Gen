"""
app.py - Streamlit UI for AI Lead Generation Pipeline
======================================================
User-friendly dashboard for:
- Scenario 1: Upload CSV/use Google Sheets
- Scenario 2: Auto-discover companies by criteria
- View results and statistics
- Download processed leads

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import subprocess
import sys
import os
from datetime import datetime
import time

# Set page configuration
st.set_page_config(
    page_title="AI Lead Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .title-style {
        color: #667eea;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - NAVIGATION
# ============================================================================

st.sidebar.markdown("# 🤖 AI Lead Generator")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Select Page",
    ["🏠 Dashboard", "📊 Scenario 1", "🔍 Scenario 2", "📈 Results", "⚙️ Settings"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# Settings in sidebar
with st.sidebar.expander("⚙️ Quick Settings"):
    api_key_status = "✅ Set" if os.getenv("OPENROUTER_API_KEY") else "❌ Not Set"
    sheets_id_status = "✅ Set" if os.getenv("GOOGLE_SHEET_ID") else "❌ Not Set"
    
    st.write(f"**OpenRouter API:** {api_key_status}")
    st.write(f"**Google Sheets ID:** {sheets_id_status}")
    
    if st.button("🔄 Reload Configuration"):
        st.rerun()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

def run_pipeline(command: list) -> dict:
    """Run the pipeline command and capture output"""
    try:
        # Fix: Use UTF-8 encoding on Windows
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',  # Add this
            timeout=600,
            env=os.environ
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Pipeline execution timed out",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def load_results_csv() -> pd.DataFrame:
    """Load results.csv if it exists"""
    results_path = Path("data/output/results.csv")
    
    if results_path.exists():
        try:
            return pd.read_csv(results_path)
        except Exception as e:
            st.error(f"Error loading results: {e}")
            return None
    return None

def get_google_sheet_data() -> dict:
    """Get statistics about Google Sheet"""
    try:
        # Import here to avoid issues if not set up
        from src.sheets_integration import SheetsIntegration
        
        sheets = SheetsIntegration()
        sheets.get_worksheet()
        
        row_count = sheets.get_row_count()
        
        return {
            "success": True,
            "row_count": row_count,
            "url": sheets.get_sheet_url()
        }
    except Exception as e:
        return {
            "success": False,
            "row_count": 0,
            "error": str(e)
        }

def format_results_summary(results_df: pd.DataFrame) -> dict:
    """Get summary from results CSV"""
    if results_df is None or results_df.empty:
        return {
            "total": 0,
            "successful": 0,
            "skipped": 0,
            "success_rate": 0
        }
    
    summary = {
        "total": len(results_df),
        "successful": len(results_df[results_df['Email Status'] == 'success']),
        "skipped": len(results_df[results_df['Email Status'] == 'skipped']),
    }
    
    if summary['total'] > 0:
        summary['success_rate'] = (summary['successful'] + summary['skipped']) / summary['total'] * 100
    else:
        summary['success_rate'] = 0
    
    return summary

# ============================================================================
# PAGE 1: DASHBOARD
# ============================================================================

if page == "🏠 Dashboard":
    st.markdown('<div class="title-style">🤖 AI Lead Generator Dashboard</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Welcome to your **AI Lead Generation Platform**! 
    
    This tool helps you:
    - 📋 Process lead lists from CSV or Google Sheets
    - 🔍 Auto-discover companies matching your criteria
    - 🤖 Generate AI-powered business summaries
    - ✉️ Create personalized outreach emails
    - 📊 Track all results and metrics
    """)
    
    st.markdown("---")
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    results_df = load_results_csv()
    summary = format_results_summary(results_df)
    sheets_data = get_google_sheet_data()
    
    with col1:
        st.metric("Current Session", f"{summary['total']} leads")
    
    with col2:
        st.metric("✅ Successful", summary['successful'])
    
    with col3:
        st.metric("⏭️ Skipped", summary['skipped'])
    
    with col4:
        st.metric("📊 Success Rate", f"{summary['success_rate']:.1f}%")
    
    st.markdown("---")
    
    # Quick Start
    st.subheader("Quick Start")
    
    tab1, tab2 = st.tabs(["Scenario 1: Use Your List", "Scenario 2: Auto-Discover"])
    
    with tab1:
        st.markdown("""
        **Upload a CSV file with companies or use Google Sheets**
        
        What you need:
        - Company names
        - Email addresses (optional)
        - Websites (optional)
        - Industry (optional)
        
        We'll handle the rest! ✨
        """)
        
    
    with tab2:
        st.markdown("""
        **Let us find companies for you!**
        
        Provide:
        - Industry (e.g., "Healthcare AI", "Fintech")
        - Location (optional)
        - Number of companies to find
        
        We'll discover and process them automatically! 🚀
        """)
        

# ============================================================================
# PAGE 2: SCENARIO 1
# ============================================================================

elif page == "📊 Scenario 1":
    st.markdown('<div class="title-style">📊 Scenario 1: Process Your Lead List</div>', unsafe_allow_html=True)
    
    st.markdown("Upload a CSV file or use leads from Google Sheets")
    
    st.markdown("---")
    
    # Options
    tab1, tab2 = st.tabs(["CSV Upload", "Google Sheets"])
    
    with tab1:
        st.subheader("📤 Upload CSV File")
        
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            help="CSV should have columns: company_name, email, website, industry"
        )
        
        if uploaded_file:
            # Display preview
            df = pd.read_csv(uploaded_file)
            st.write("**Preview:**")
            st.dataframe(df.head())
            
            # Save to data folder
            # Sanitize filename (remove emojis)
            safe_filename = uploaded_file.name.encode('ascii', 'ignore').decode('ascii')
            csv_path = Path("data") / safe_filename
            csv_path.parent.mkdir(exist_ok=True)
            
            with open(csv_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ File saved to {csv_path}")
            
            # Process settings
            col1, col2 = st.columns(2)
            
            with col1:
                max_leads = st.slider(
                    "Maximum leads to process",
                    min_value=1,
                    max_value=len(df),
                    value=min(10, len(df))
                )
            
            with col2:
                update_sheets = st.checkbox(
                    "Update Google Sheets",
                    value=True,
                    help="Append results to Google Sheets"
                )
            
            # Run button
            if st.button("🚀 Process Leads", key="s1_run"):
                with st.spinner("🔄 Processing leads... This may take a few minutes"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Build command
                    command = [
                        sys.executable,
                        "-m",
                        "src.main",
                        "--scenario", "1",
                        "--source", "csv",
                        "--csv", str(csv_path),
                        "--max-leads", str(max_leads),
                    ]
                    
                    if not update_sheets:
                        command.append("--no-sheets-update")
                    
                    # Run pipeline
                    result = run_pipeline(command)
                    
                    # Show output
                    if result['success']:
                        st.success("✅ Pipeline completed successfully!")
                        
                        # Load and display results
                        results_df = load_results_csv()
                        if results_df is not None:
                            summary = format_results_summary(results_df)
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Processed", summary['total'])
                            with col2:
                                st.metric("✅ Success", summary['successful'])
                            with col3:
                                st.metric("⏭️ Skipped", summary['skipped'])
                            with col4:
                                st.metric("📊 Rate", f"{summary['success_rate']:.1f}%")
                            
                            st.subheader("Results Preview")
                            st.dataframe(results_df.head(10))
                    else:
                        st.error("❌ Pipeline failed")
                        st.error(result['stderr'])

    with tab2:
        st.subheader("📊 Use Google Sheets")
        
        st.info("""
        ℹ️ Configure your Google Sheet in Settings first!
        
        Columns needed:
        - company_name
        - email
        - website
        - industry
        """)
        
        max_leads = st.slider(
            "Maximum leads to process",
            min_value=1,
            max_value=500,
            value=10
        )
        
        if st.button("🚀 Process from Google Sheets", key="s1_sheets"):
            with st.spinner("🔄 Processing leads..."):
                command = [
                    sys.executable,
                    "-m",
                    "src.main",
                    "--scenario", "1",
                    "--source", "google_sheets",
                    "--max-leads", str(max_leads),
                ]
                
                result = run_pipeline(command)
                
                if result['success']:
                    st.success("✅ Completed!")
                    results_df = load_results_csv()
                    if results_df is not None:
                        st.dataframe(results_df)
                else:
                    st.error("❌ Failed")
                    st.error(result['stderr'])

# ============================================================================
# PAGE 3: SCENARIO 2
# ============================================================================

elif page == "🔍 Scenario 2":
    st.markdown('<div class="title-style">🔍 Scenario 2: Auto-Discover Companies</div>', unsafe_allow_html=True)
    
    st.markdown("Find companies by industry and process them automatically")
    
    st.markdown("---")
    
    # Input form
    col1, col2 = st.columns(2)
    
    with col1:
        industry = st.text_input(
            "🏭 Industry",
            placeholder="e.g., Healthcare AI, Fintech, SaaS",
            help="What industry are you targeting?"
        )
        
        topic = st.text_input(
            "🏷️ GitHub Topic (optional)",
            placeholder="e.g., healthcare-ai, fintech",
            help="GitHub topic to search for relevant projects"
        )
    
    with col2:
        location = st.text_input(
            "📍 Location (optional)",
            placeholder="e.g., USA, India, UK",
            help="Geographic location filter"
        )
        
        num_results = st.slider(
            "# Companies to Find",
            min_value=1,
            max_value=100,
            value=10
        )
    
    st.markdown("---")
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        update_sheets = st.checkbox(
            "Update Google Sheets",
            value=True
        )
    
    # Run button
    if st.button("🚀 Discover & Process", key="s2_run"):
        if not industry:
            st.error("❌ Please enter an industry!")
        else:
            with st.spinner(f"🔄 Discovering companies in {industry}... This may take a few minutes"):
                # Build command
                command = [
                    sys.executable,
                    "-m",
                    "src.main",
                    "--scenario", "2",
                    "--industry", industry,
                    "--num-results", str(num_results),
                ]
                
                if topic:
                    command.extend(["--topic", topic])
                
                if location:
                    command.extend(["--location", location])
                
                if not update_sheets:
                    command.append("--no-sheets-update")
                
                # Run pipeline
                result = run_pipeline(command)
                
                # Show results
                if result['success']:
                    st.success("✅ Discovery and processing completed!")
                    
                    results_df = load_results_csv()
                    if results_df is not None:
                        summary = format_results_summary(results_df)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Found", summary['total'])
                        with col2:
                            st.metric("✅ Success", summary['successful'])
                        with col3:
                            st.metric("⏭️ Skipped", summary['skipped'])
                        with col4:
                            st.metric("📊 Rate", f"{summary['success_rate']:.1f}%")
                        
                        st.subheader("Results")
                        st.dataframe(results_df)
                else:
                    st.error("❌ Discovery failed")
                    st.error(result['stderr'])

# ============================================================================
# PAGE 4: RESULTS
# ============================================================================

elif page == "📈 Results":
    st.markdown('<div class="title-style">📈 Results & Analytics</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Current Session", "All-Time Stats", "Download"])
    
    with tab1:
        st.subheader("📊 Current Session Results")
        
        results_df = load_results_csv()
        
        if results_df is not None and not results_df.empty:
            summary = format_results_summary(results_df)
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Leads", summary['total'])
            with col2:
                st.metric("✅ Successful", summary['successful'])
            with col3:
                st.metric("⏭️ Skipped", summary['skipped'])
            with col4:
                st.metric("📊 Success Rate", f"{summary['success_rate']:.1f}%")
            
            st.markdown("---")
            
            # Table
            st.write("**Detailed Results:**")
            st.dataframe(results_df, use_container_width=True)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                status_counts = results_df['Email Status'].value_counts()
                st.bar_chart(status_counts)
                st.caption("Email Status Distribution")
            
            with col2:
                industry_counts = results_df['Industry'].value_counts().head(10)
                st.bar_chart(industry_counts)
                st.caption("Top Industries")
        
        else:
            st.info("No results yet. Run a scenario to generate results!")
    
    with tab2:
        st.subheader("📊 All-Time Statistics")
        
        sheets_data = get_google_sheet_data()
        
        if sheets_data['success']:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Rows in Google Sheet", sheets_data['row_count'])
            
            with col2:
                if st.button("🔗 Open Google Sheet"):
                    st.write(f"[Click here to view]({sheets_data['url']})")
            
            st.info("""
            ℹ️ **Google Sheet Statistics**
            
            Your Google Sheet contains:
            - All processed leads from all sessions
            - Including successful, skipped, and failed leads
            - Historical data that's never deleted
            - Perfect for long-term analysis
            """)
        else:
            st.error(f"Could not access Google Sheet: {sheets_data.get('error', 'Unknown error')}")
    
    with tab3:
        st.subheader("📥 Download Results")
        
        results_df = load_results_csv()
        
        if results_df is not None and not results_df.empty:
            # CSV download
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Current Results (CSV)",
                data=csv,
                file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Excel download (if openpyxl is available)
            try:
                import openpyxl
                excel_data = results_df.to_excel(index=False)
                st.download_button(
                    label="📥 Download Current Results (Excel)",
                    data=excel_data,
                    file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.ms-excel"
                )
            except:
                pass
        else:
            st.info("No results to download. Run a scenario first!")

# ============================================================================
# PAGE 5: SETTINGS
# ============================================================================

elif page == "⚙️ Settings":
    st.markdown('<div class="title-style">⚙️ Settings & Configuration</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("🔑 API Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**OpenRouter API**")
        openrouter_status = os.getenv("OPENROUTER_API_KEY")
        if openrouter_status:
            st.success("✅ API Key configured")
        else:
            st.error("❌ API Key not configured")
            st.info("""
            Add to your `.env` file:
            ```
            OPENROUTER_API_KEY=sk-or-v1-xxx...
            ```
            """)
    
    with col2:
        st.write("**Google Sheets**")
        sheets_status = os.getenv("GOOGLE_SHEET_ID")
        if sheets_status:
            st.success("✅ Sheet ID configured")
        else:
            st.error("❌ Sheet ID not configured")
            st.info("""
            Add to your `.env` file:
            ```
            GOOGLE_SHEET_ID=your-sheet-id-here
            ```
            """)
    
    st.markdown("---")
    
    st.subheader("📁 File Locations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Results File:**")
        results_path = Path("data/output/results.csv")
        if results_path.exists():
            st.success(f"✅ {results_path}")
        else:
            st.warning(f"⚠️ {results_path} (not created yet)")
    
    with col2:
        st.write("**Log File:**")
        log_path = Path("data/logs/processing.log")
        if log_path.exists():
            st.success(f"✅ {log_path}")
        else:
            st.warning(f"⚠️ {log_path} (not created yet)")
    
    st.markdown("---")
    
    st.subheader("🔄 Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reload Configuration"):
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Results File"):
            results_path = Path("data/output/results.csv")
            if results_path.exists():
                results_path.unlink()
                st.success("✅ Results file cleared")
            else:
                st.info("No results file to clear")
    
    st.markdown("---")
    
    st.subheader("📚 Help & Documentation")
    
    with st.expander("❓ How to use Scenario 1"):
        st.markdown("""
        1. Prepare a CSV file with company data
        2. Upload it on the "Scenario 1" page
        3. Set maximum leads to process
        4. Click "Process Leads"
        5. Results appear in `data/output/results.csv`
        """)
    
    with st.expander("❓ How to use Scenario 2"):
        st.markdown("""
        1. Go to "Scenario 2" page
        2. Enter industry (required)
        3. Enter GitHub topic (optional)
        4. Enter location (optional)
        5. Set number of companies to find
        6. Click "Discover & Process"
        7. Results appear in `data/output/results.csv`
        """)
    
    with st.expander("❓ Understanding Results"):
        st.markdown("""
        **Email Status:**
        - ✅ Success: Email was generated
        - ⏭️ Skipped: Not enough data to process
        - ❌ Failed: Error during processing
        
        **Scrape Status:**
        - success: Website content extracted
        - failed: Could not access website
        
        **Summary Status:**
        - success: AI summary generated
        - skipped: No content to summarize
        """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.9em;'>
    <p>🤖 AI Lead Generation Pipeline | Built with Streamlit</p>
    <p>For documentation and support, visit the project repository</p>
</div>
""", unsafe_allow_html=True)