import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="ICP-OES Data Processor", page_icon="🧪")

# --- UI Header ---
st.title("🧪 ICP-OES Analytical Tool")
st.write("Professional utility for processing atomic spectrometry data.")

# --- Instructions Section ---
with st.expander("ℹ️ View Input File Requirements & RSD Logic"):
    st.markdown("""
    ### **Input File Requirements**
    1. **Structure:** Each sample must consist of exactly **4 rows** in this specific order:
        * `Concentration average`
        * `Concentration SD`
        * `Concentration RSD`
        * `MQL`
    2. **Required Columns:**
        * `Category`: Identifying the row type (Avg, SD, etc.).
        * `Label`: The Sample Name (repeated in all 4 rows or at least the first row).
    3. **Element Header Row:** Each cell in the element columns should contain: **Element Symbol, Wavelength (nm), View (Axial/Radial), and Tuning Set info.**
    4. **Format:** Standard CSV (comma-separated).

    ### **RSD Monitoring Logic**
    You may customize the RSD% limits in the sidebar to suit your analytical requirements. 
    * **Default Calculation:** By default, all averages with an **RSD < 6%** are considered stable.
    * **Questionable Results (!):** RSD values between **6% and 10%** are flagged with a **"!"**. These results should be treated with caution.
    * **High Variability (!!):** If the sample average is above the LOQ (calculated as $SD \\times 10$), but the **RSD exceeds 10%**, the result is flagged with **"!!"**. 
    
    **Note:** Results marked with "!!" require thorough inspection, as high variability often indicates poor reliability and may necessitate re-evaluation.
    """)

# --- Sidebar Settings ---
st.sidebar.header("RSD Control Limits")
st.sidebar.write("Customize your flagging thresholds:")
rsd_low = st.sidebar.slider("Yellow Flag (!)", 1.0, 15.0, 6.0, 0.5)
rsd_high = st.sidebar.slider("Red Flag (!!)", 1.0, 25.0, 10.0, 0.5)

st.sidebar.markdown("---")
st.sidebar.info("Tip: Adjust these limits based on your specific method validation requirements.")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your source CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    
    elements = [col for col in df.columns if col not in ['Category', 'Label']]
    final_results = []
    
    total_rows = len(df)
    valid_rows = total_rows - (total_rows % 4)

    for i in range(0, valid_rows, 4):
        block = df.iloc[i : i + 4].copy()
        block['Category'] = block['Category'].astype(str).str.strip()
        sample_name = str(block['Label'].iloc[0]).strip()
        
        new_row = {'Sample Name': sample_name}
        
        for el in elements:
            try:
                avg_row = block[block['Category'].str.contains('average', case=False, na=False)]
                sd_row = block[block['Category'].str.contains('SD', case=False, na=False)]
                rsd_row = block[block['Category'].str.contains('RSD', case=False)]
