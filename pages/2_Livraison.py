import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px

import utils
from livreur_tab import render_livreur_tab


@st.cache_data
def load_date_from_excel(excel_file, selected_months):
    return utils.read_livraison_multi_year(excel_file, selected_months)


# Page configuration
st.set_page_config(page_title="Livraison Dashboard", page_icon=":bar_chart:", layout="wide")
st.title(":bar_chart: _Livraison Dashboard Multiple Mois_", text_alignment="center")
st.space()

# Upload Excel files
excel_files = st.file_uploader(
    "Télécharger le fichier Excel de Livraison",
    type=["xlsx"],
    accept_multiple_files=True,
)

if not excel_files:
    st.warning("Please upload an Excel file to proceed.")
    st.stop()

years = set()
months = set()

for file in excel_files:
    filename = os.path.basename(file.name)

    # Extract year from filename
    match = re.search(r"(\d{4})", filename)
    if match:
        years.add(int(match.group(1)))
    else:
        st.warning(f"Année introuvable dans le fichier : {filename}")
        continue

    # Read sheet names as months
    xls = pd.ExcelFile(file)
    months.update(xls.sheet_names)

years_column, months_column = st.columns(2)
with years_column:
    # Year selection
    selected_years = st.multiselect(
        "Select years",
        options=sorted(years),
        default=sorted(years),
    )

with months_column:
    # Month selection
    selected_months = st.multiselect(
        "Select months",
        options=sorted(months),
        default=sorted(months),
    )

data = load_date_from_excel(excel_files, selected_months)
if not data["success"]:
    st.warning(data["message"])
    st.stop()
else:
    dfs = data["data"]

st.divider()

# Create Two Tabs
multi_mois_tab, livreur_tab = st.tabs(
    ["Livraison Multi Mois", "🚚 Rapport Livreur"],
    default="Livraison Multi Mois"
)

# ----------------------------------------------------------------------------
#
# ---- ETAT GLOBAL -------
fields = ["YEAR", "MOIS", "MOIS_NUM", "DATE", "LIVREUR", "T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE"]
multi_mois_tab.subheader("📊 État Global des Livraisons")
multi_mois_tab.space()
# multi_moi_tabdataframe(dfs[fields], width="multi_moi_tabetch", hide_index=True)
multi_mois_tab.divider()
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
multi_mois_tab.markdown("##### 📋 Tableau Croisé des Livraisons par Année et Mois")
multi_mois_tab.dataframe(year_pivot, width="stretch")
multi_mois_tab.divider()
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
multi_mois_tab.space()
multi_mois_tab.markdown("##### 📋 Tableau Croisé des Livraisons par Mois et Livreur")
multi_mois_tab.dataframe(pivot, width="stretch")

# --- Chart
multi_mois_tab.space()
multi_mois_tab.subheader("📈 Visualisation des Livraisons par Mois")
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
multi_mois_tab.plotly_chart(chart_by_mois, width="stretch")

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
multi_mois_tab.space()
multi_mois_tab.subheader("📊 Totaux mensuels _VERSEMENT_ & _COMMANDES_", divider="grey", width="content")

# -- Display Grande Total --
for _, row in df_grand_total.iterrows():
    col1, col2, col3 = multi_mois_tab.columns(3)
    col1.metric("💰 Versement", f"{row['versement']:,.0f} DA", border=True)
    col2.metric("📋 Commandes", f"{row['commandes']:,.0f} DA", border=True)
    col3.metric("💸 Charges", f"{row['charges']:,.0f} DA", border=True)
    multi_mois_tab.divider()

# -- Display Total par MOIS --
for _, row in df_total_par_mois.iterrows():
    multi_mois_tab.markdown(f"##### 📆 {row['MOIS']}")
    col1, col2, col3 = multi_mois_tab.columns(3)
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
    multi_mois_tab.divider()

# ----------------------------------------------------------------------------
# --- Accompte - Crédits - Versement Crédit ---
# ---------------------------------------------
multi_mois_tab.space()
multi_mois_tab.subheader("📊 Détails des Accomptes et Crédits", divider="grey", width="content")
etat_accompte = dfs.groupby(["LIVREUR", "YEAR", "MOIS_NUM", "MOIS"], as_index=False)["VERSEMENT"].sum()
etat_accompte = etat_accompte[etat_accompte["LIVREUR"].isin(["ACCOMPTE", "CREDIT", "VERS. CREDIT"])]
etat_accompte = etat_accompte.pivot_table(
    index=["YEAR", "MOIS"],
    columns="LIVREUR",
    values="VERSEMENT",
    fill_value=0,
)
multi_mois_tab.dataframe(etat_accompte, width="stretch")
multi_mois_tab.divider()
# ----------------------------------------------------------------------------
# TODO:  Build totals by livreur
df_total_par_livreur = (
    dfs
    .loc[dfs["LIVREUR"].isin(["MOHAMED", "AMINE", "TOUFIK", "REDA"])]
    .groupby(["LIVREUR", "MOIS_NUM"], as_index=False)
    .agg(
        versement=("VERSEMENT", "sum"),
        # commandes=("T. COMMANDE", "sum"),
        # charges=("CHARGE", "sum")
    )
    .sort_values("versement", ascending=False)
    .set_index("LIVREUR")
)

multi_mois_tab.dataframe(df_total_par_livreur, width="stretch")
# ----------------------------------------------------------------------------
# ----> LIVREUR TAB <----
# -----------------------

render_livreur_tab(livreur_tab, dfs)

# hide some stylesheet
# hide_st_style = '''
# <style>
#     #MainMenu { visibility: hidden; }
#     header { visibility: hidden; }
#     footer { visibility: hidden; }
# </style>
# '''
# st.markdown(hide_st_style, unsafe_allow_html=True)
