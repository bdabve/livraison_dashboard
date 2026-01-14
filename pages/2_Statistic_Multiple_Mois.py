import streamlit as st
import pandas as pd
import utils


@st.cache_data
def load_date_from_excel(excel_file, selected_months):
    dfs = []
    for month in selected_months:
        data = utils.clean_dataframe(pd.read_excel(excel_file, sheet_name=month, usecols="A:H"))
        if data["success"]:
            dfs.append(data["df"])
        else:
            return {"success": False, "message": data["message"]}
    try:
        dfs = pd.concat(dfs, ignore_index=True)
    except ValueError:
        return {"success": False, "message": "Aucun mois sélectionné."}
    else:
        return {"success": True, "data": dfs}


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


data = load_date_from_excel(excel_file, selected_months)
if not data["success"]:
    st.warning(data["message"])
    st.stop()
else:
    dfs = data["data"]

# ------- Side Bar -------
st.subheader("Global statistics")
st.dataframe(dfs.describe())