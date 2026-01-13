import streamlit as st
import pandas as pd


# Page configuration
st.set_page_config(page_title="Livraison Dashboard", page_icon=":bar_chart:", layout="wide")
st.title(":bar_chart: _Livraison Dashboard Multiple Mois_", text_alignment="center")
st.space()

# Load data
excel_file = st.file_uploader(
    "Télécharger le fichier Excel de Livraison",
    type=["xlsx"]
)

if not excel_file:
    st.warning("Please upload an Excel file to proceed.")
    st.stop()
else:
    f = pd.ExcelFile(excel_file)
    months = f.sheet_names
    selected_months = st.multiselect("Select months", months, default=months)

dfs = [pd.read_excel(excel_file, sheet_name=m) for m in selected_months]
df_all = pd.concat(dfs, ignore_index=True)

st.subheader("Global statistics")
st.dataframe(df_all.describe())