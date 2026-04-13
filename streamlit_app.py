import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="ICP-OES Lab Tool", page_icon="🧪")

st.title("🧪 Обработка данных ICP-OES")
st.write("Настройте пороги RSD и загрузите ваш CSV файл.")

# Настройки порогов в боковой панели
st.sidebar.header("Параметры контроля")
rsd_low = st.sidebar.slider("Порог для '!' (RSD %)", 1.0, 15.0, 6.0, 0.5)
rsd_high = st.sidebar.slider("Порог для '!!' (RSD %)", 1.0, 25.0, 10.0, 0.5)

uploaded_file = st.file_uploader("Перетащите сюда файл .csv", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    
    # Логика обработки
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
                rsd_row = block[block['Category'].str.contains('RSD', case=False, na=False)]
                mql_row = block[block['Category'].str.contains('MQL', case=False, na=False)]

                avg_raw = avg_row[el].values[0]
                sd_val = float(sd_row[el].values[0])
                rsd_val = float(rsd_row[el].values[0])
                mql_val = float(mql_row[el].values[0])
                
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
    
    st.success(f"Обработано образцов: {len(res_df)}")
    st.dataframe(res_df) # Предпросмотр таблицы на сайте

    # Подготовка к скачиванию
    output = io.BytesIO()
    res_df.to_csv(output, index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 СКАЧАТЬ ГОТОВЫЙ ОТЧЕТ",
        data=output.getvalue(),
        file_name="ICP_Processed_Report.csv",
        mime="text/csv"
    )
