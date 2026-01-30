import streamlit as st
import pandas as pd
import utils
import plotly.express as px


@st.cache_data
def load_date_from_excel(excel_file, selected_months):
    return utils.read_livraison_multi_year(excel_file, selected_months)
    # return utils.read_livraison_files(excel_file, selected_months)


# Page configuration
st.set_page_config(page_title="Livraison Dashboard", page_icon=":bar_chart:", layout="wide")
st.title(":bar_chart: _Livraison Dashboard Multiple Mois_", text_alignment="center")
st.space()

# Load data
excel_file = st.file_uploader(
    "Télécharger le fichier Excel de Livraison",
    accept_multiple_files=True,
    type=["xlsx"]
)

if not excel_file:
    st.warning("Please upload an Excel file to proceed.")
    st.stop()
else:
    months = list()
    for file in excel_file:
        f = pd.ExcelFile(file)
        for sheet in f.sheet_names:
            months.append(sheet)
    # Select Months
    selected_months = st.multiselect("Select months", months, default=months)


data = load_date_from_excel(excel_file, selected_months)
if not data["success"]:
    st.warning(data["message"])
    st.stop()
else:
    dfs = data["data"]

st.divider()
# ----------------------------------------------------------------------------
#
# ---- ETAT GLOBAL -------
fields = ["YEAR", "MOIS", "MOIS_NUM", "DATE", "LIVREUR", "T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE"]
st.subheader("📊 État Global des Livraisons")
st.space()
st.dataframe(dfs[fields], width="stretch", hide_index=True)
st.divider()
#
# ---- Pivot Table Yearly
dfs["YEAR"] = dfs["YEAR"].astype(str)
year_pivot = pd.pivot_table(
    dfs,
    index=["YEAR", "MOIS"],
    values=["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE"],
    aggfunc="sum",
    margins=True, margins_name="Total Général",
    fill_value=0,
    sort=False,
)
st.markdown("##### 📋 Tableau Croisé des Livraisons par Année et Mois")
st.dataframe(year_pivot, width="stretch")
st.divider()
#
# --- Pivot Table Mois Livreur---
pivot = pd.pivot_table(
    dfs,
    index=["MOIS", "LIVREUR"],
    values=["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE"],
    aggfunc="sum",
    margins=True, margins_name="Total Général",
    fill_value=0,
    sort=False,
)
st.space()
st.markdown("##### 📋 Tableau Croisé des Livraisons par Mois et Livreur")
st.dataframe(pivot, width="stretch")

# --- Chart
st.space()
st.subheader("📈 Visualisation des Livraisons par Mois")
chart_data = (
    dfs
    .groupby(["YEAR", "MOIS", "MOIS_NUM"], as_index=False)
    .agg(
        versement=("VERSEMENT", "sum"),
        commandes=("T. COMMANDE", "sum"),
        charges=("CHARGE", "sum")
    )
    .sort_values(["YEAR", "MOIS_NUM"])
    .set_index("MOIS")
)
chart_by_mois = px.histogram(
    chart_data,
    x=chart_data.index,
    y=["versement", "commandes", "charges"],
    barmode="group",
    title="Livraisons par Mois",
    labels={
        "value": "Montant (DA)",
        "MOIS": "Mois",
        "variable": "Type"
    },
    height=400,
)
st.plotly_chart(chart_by_mois, width="stretch")

# ----------------------------------------------------------------------------
# --- Filter Month ---
#
months = dfs.sort_values("MOIS")["MOIS"].unique()
selected_month = st.sidebar.selectbox(
    "📅 Choisir le mois",
    months,
    index=len(months) - 1  # default = latest month
)
st.sidebar.header(f"**{selected_month}**", text_alignment="center")
st.sidebar.divider()
# ----------------------------------------------------------------------------
# --- Etat par MOIS ---
df_total_par_mois = (
    dfs
    .groupby(["YEAR", "MOIS_NUM", "MOIS"], as_index=False)
    .agg(
        versement=("VERSEMENT", "sum"),
        commandes=("T. COMMANDE", "sum"),
        charges=("CHARGE", "sum")
    )
    .sort_values("YEAR")
)
# --- Calculate Deltas ---
df_total_par_mois["delta_versement"] = df_total_par_mois["versement"].diff()
df_total_par_mois["delta_commandes"] = df_total_par_mois["commandes"].diff()
df_total_par_mois["delta_charges"] = df_total_par_mois["charges"].diff()

# Pourcentage
df_total_par_mois["delta_versement_pct"] = df_total_par_mois["versement"].pct_change() * 100
df_total_par_mois["delta_commandes_pct"] = df_total_par_mois["commandes"].pct_change() * 100
df_total_par_mois["delta_charges_pct"] = df_total_par_mois["charges"].pct_change() * 100

# --- Grand Total ---
df_grand_total = pd.DataFrame({
    "versement": [df_total_par_mois["versement"].sum()],
    "commandes": [df_total_par_mois["commandes"].sum()],
    "charges": [df_total_par_mois["charges"].sum()]
})

# ----------------
st.space()
st.subheader("📊 Totaux mensuels _VERSEMENT_ & _COMMANDES_", divider="grey", width="content")

# -- Display Grande Total --
for _, row in df_grand_total.iterrows():
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Versement", f"{row['versement']:,.0f} DA", border=True)
    col2.metric("📋 Commandes", f"{row['commandes']:,.0f} DA", border=True)
    col3.metric("💸 Charges", f"{row['charges']:,.0f} DA", border=True)
    st.divider()

# -- Display Total par MOIS --
for _, row in df_total_par_mois.iterrows():
    st.markdown(f"##### 📆 {row['MOIS']}")
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "💰 Versement",
        f"{row['versement']:,.0f} DA",
        # delta=f"{row['delta_versement']:,.0f} DA" if not pd.isna(row["delta_versement"]) else None,
        delta=f"{row['delta_versement_pct']:.1f}%" if not pd.isna(row["delta_versement_pct"]) else None,
        border=True,
    )
    #
    col2.metric(
        "📋 Commandes",
        f"{row['commandes']:,.0f} DA",
        # delta=f"{row['delta_commandes']:,.0f} DA" if not pd.isna(row["delta_commandes"]) else None,
        delta=f"{row['delta_commandes_pct']:.1f}%" if not pd.isna(row["delta_commandes_pct"]) else None,
        border=True,
    )
    #
    col3.metric(
        "💸 Charges",
        f"{row['charges']:,.0f} DA",
        # delta=f"{row['delta_charges']:,.0f} DA" if not pd.isna(row["delta_charges"]) else None,
        delta=f"{row['delta_charges_pct']:.1f}%" if not pd.isna(row["delta_charges_pct"]) else None,
        border=True,
    )
    st.divider()
