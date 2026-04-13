import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="ICP-OES Data Processor", page_icon="🧪")

# --- UI Header ---
st.title("🧪 ICP-OES Analytical Tool")
st.write("Professional utility for processing atomic spectrometry data.")

# --- Instructions Section ---
with st.expander("ℹ️ View Input File Requirements"):
    st.markdown("""
    **The source CSV file must follow these rules:**
    1. **Structure:** Each sample must consist of exactly **4 rows** in this specific order:
        * `Concentration average`
        * `Concentration SD`
        * `Concentration RSD`
        * `MQL`
    2. **Columns:** The file must contain at least the following columns:
        * `Category`: Identifying the row type (Avg, SD, etc.)
        * `Label`: The Sample Name (repeated or in the first row of the block)
        * `Element Columns`: Chemical elements (e.g., Fe, Cu, Zn...) with numeric data.
    3. **Format:** Save as a Standard CSV (comma-separated).
    """)

# --- Sidebar Settings ---
st.sidebar.header("RSD Control Limits")
st.sidebar.write("Set thresholds for visual flags:")
rsd_low = st.sidebar.slider("Yellow Flag (!)", 1.0, 15.0, 6.0, 0.5, help="Mark values with '!' if RSD exceeds this limit.")
rsd_high = st.sidebar.slider("Red Flag (!!)", 1.0, 25.0, 10.0, 0.5, help="Mark values with '!!' if RSD exceeds this limit.")

st.sidebar.markdown("---")
st.sidebar.info("Tip: RSD thresholds help identify stability issues in the plasma.")

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
                # Identification by Category labels
                avg_row = block[block['Category'].str.contains('average', case=False, na=False)]
                sd_row = block[block['Category'].str.contains('SD', case=False, na=False)]
                rsd_row = block[block['Category'].str.contains('RSD', case=False, na=False)]
                mql_row = block[block['Category'].str.contains('MQL', case=False, na=False)]

                avg_raw = avg_row[el].values[0]
                sd_val = float(sd_row[el].values[0])
                rsd_val = float(rsd_row[el].values[0])
                mql_val = float(mql_row[el].values[0])
                
                # Logic: MQL check and RSD flagging
                if "<LQ" in str(avg_raw) or float(avg_raw) < mql_val:
                    res = f"<{round(sd_val * 10, 3)}"
                else:
                    num_avg = float(avg_raw)
                    if rsd_val > rsd_high:
                        res = f"{num_avg}!!"
                    elif rsd_val > rsd_low:
                        res = f"{num_avg}!"
                    else:
                        res = str(num_avg)
                new_row[el] = res
            except:
                new_row[el] = "n/a"
        
        final_results.append(new_row)

    res_df = pd.DataFrame(final_results)
    
    st.subheader("Results Preview")
    st.success(f"Successfully processed {len(res_df)} samples.")
    st.dataframe(res_df)

    # Download Button
    output = io.BytesIO()
    res_df.to_csv(output, index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 DOWNLOAD PROCESSED REPORT",
        data=output.getvalue(),
        file_name="ICP_Analysis_Report.csv",
        mime="text/csv"
    )
