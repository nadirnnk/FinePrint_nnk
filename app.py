import streamlit as st
import requests
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="🔍 FinePrint AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for better mobile display
st.markdown("""
    <style>
        .header-container {
            display: flex;
            align-items: center;
            gap: 30px;
            margin-bottom: 1rem;
        }
        .header-logo img {
            height: 60px;
        }
        .header-text h1 {
            font-size: 2rem;
            margin: 0;
            padding: 0;
        }
        .header-text p {
            margin: 4px 0 0 0;
            font-size: 0.95rem;
            color: #ccc;
        }
    </style>
    <div class="header-container">
        <div class="header-logo">
            <img src="https://raw.githubusercontent.com/nadirnnk/FinePrint/main/images/logo.png">
        </div>
        <div class="header-text">
            <h1>FinePrint AI</h1>
            <p>📌 Spot shady contract clauses in seconds. We never store your files after analysis.</p>
        </div>
    </div>
""", unsafe_allow_html=True)

#--------------------------------------------------------------------------------------------------
# Header with logo
#col1, col2 = st.columns([1, 8])
#with col1:
#    st.image("images/logo.png", width=80)
#with col2:
#    st.title("FinePrint AI")
#    st.caption("📌 Spot shady contract clauses in seconds. We never store your files after analysis. ")

# File upload
uploaded_file = st.file_uploader(
    "**Upload your contract (PDF)**",
    type="pdf",
    help="We never store your files after analysis"
)

if uploaded_file:
    with st.spinner("🔍 Scanning your contract..."):
        # Send to backend
        try:
            response = requests.post(
                "https://fineprint.onrender.com/analyze",  # Updated to your Replit deployment URL
                files={"file": uploaded_file},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Success display
                st.success("Analysis complete!")
                
                # Results tabs
                tab1, tab2 = st.tabs(["📋 Plain English Summary", "📊 Detailed Analysis"])
                
                with tab1:
                    cleaned_text = data["result_text"].replace("Quoted Text:", "**• Quoted Text:**") \
                                      .replace("Potential Risk:", "**• Potential Risk:**") \
                                      .replace("Suggested Fix:", "**• Suggested Fix:**") \
                                      .replace("--- Clause", "\n--- Clause")
                    st.markdown(cleaned_text, unsafe_allow_html=True)
                    
                    # Sharing options
                    st.divider()
                    st.markdown("**Found something shady?**")
                    cols = st.columns(3)
                    cols[0].button("Share Analysis 🔗", 
                                  help="Share your analysis")
                    cols[1].button("Copy Results 📋", 
                                  help="Copy to clipboard")
                    cols[2].download_button(
                        "Save as PDF 💾",
                        data=data["result_text"],
                        file_name=f"contract-analysis-{datetime.now().date()}.txt",
                        mime="text/plain"
                    )
                
                with tab2:
                    st.json(data["result_json"])
                
                # Feature preview
                st.divider()
                st.markdown("""
                <div style="background-color:#f0f2f6;padding:20px;border-radius:10px">
                <h4 style="color:#1e3a8a">🔓 Coming Soon</h4>
                <ul>
                    <li>Batch contract analysis</li>
                    <li>Custom templates</li>
                    <li>Advanced reporting</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.error(f"Error: Could not analyze contract. Please try again.")
        except Exception as e:
            st.error(f"Connection error. Please try again later.")

# Sidebar for user feedback
with st.sidebar:
    st.markdown("### Help Improve FinePrint")
    with st.form(key='feedback'):
        rating = st.slider("How useful was this?", 1, 5, 3)
        comments = st.text_area("What could be better?")
        submitted = st.form_submit_button("Submit Feedback")
        if submitted:
            st.success("Thanks! We'll use this to improve.")

# Footer
st.markdown("---")
st.markdown("""
<small>
⚠️ Disclaimer: FinePrint AI provides educational insights only, not legal advice. 
Consult an attorney for contract review.
</small>
""", unsafe_allow_html=True)
