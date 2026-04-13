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
    1. **Structure:** Each sample must consist of exactly **4 rows** (Avg, SD, RSD, MQL).
    2. **Required Columns:** `Category` and `Label`.
    3. **Element Header Row:** Must contain Symbol, Wavelength, View, and Tuning info.
    
    ### **RSD Monitoring Logic**
    * **RSD < 6%:** Considered stable.
    * **6% - 10%:** Flagged with **"!"** (Questionable).
    * **> 10% (and > LOQ):** Flagged with **"!!"** (High variability, inspect result).
    """)

# --- Sidebar Settings ---
st.sidebar.header("RSD Control Limits")
rsd_low = st.sidebar.slider("Yellow Flag (!)", 1.0, 15.0, 6.0, 0.5)
rsd_high = st.sidebar.slider("Red Flag (!!)", 1.0, 25.0, 10.0, 0.5)

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your source CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    
    elements = [col for col in df.columns if col not in ['Category', 'Label']]
    final_results = []
    mql_values = {} # Для хранения значений MQL для финальной строки

    total_rows = len(df)
    valid_rows = total_rows - (total_rows % 4)

    for i in range(0, valid_rows, 4):
        block = df.iloc[i : i + 4].copy()
        block['Category'] = block['Category'].astype(str).str.strip()
        sample_name = str(block['Label'].iloc[0]).strip()
        
        new_row = {'Sample Name': sample_name}
        
        for el in elements:
            try:
                # Извлекаем данные из блока
                avg_val = block[block['Category'].str.contains('average', case=False, na=False)][el].values[0]
                sd_val  = float(block[block['Category'].str.contains('SD', case=False, na=False)][el].values[0])
                rsd_val = float(block[block['Category'].str.contains('RSD', case=False, na=False)][el].values[0])
                mql_val = float(block[block['Category'].str.contains('MQL', case=False, na=False)][el].values[0])
                
                # Сохраняем MQL (перезаписываем, так как они одинаковые)
                if el not in mql_values:
                    mql_values[el] = mql_val
                
                # Основная логика обработки
                if "<LQ" in str(avg_val) or float(avg_val) < mql_val:
                    res = f"<{round(sd_val * 10, 3)}"
                else:
                    num_avg = float(avg_val)
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

    if final_results:
        res_df = pd.DataFrame(final_results)
        
        # ДОБАВЛЕНИЕ СТРОКИ MQL В КОНЕЦ
        if mql_values:
            mql_row = {'Sample Name': 'MQL, mg/L'}
            mql_row.update(mql_values)
            res_df = pd.concat([res_df, pd.DataFrame([mql_row])], ignore_index=True)

        st.success(f"Processed {len(final_results)} samples + MQL reference row.")
        st.dataframe(res_df)

        # Скачивание
        output = io.BytesIO()
        res_df.to_csv(output, index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 DOWNLOAD PROCESSED REPORT", 
            data=output.getvalue(), 
            file_name="ICP_Analysis_Report.csv", 
            mime="text/csv"
        )
