#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
import pandas as pd
import utils
import plotly.express as px
import streamlit as st
import widgets

# ------------------------
# == Configuration
# ------------------------
st.set_page_config(page_title="Vente Dashboard", page_icon=":bar_chart:", layout="wide")
st.title("💱 _Vente_", text_alignment="center")
st.space()


@st.cache_data
def load_data_multiple_excel(xls_files: list):
    data = utils.multiple_files(xls_files)
    return data


xls_files = st.file_uploader(
    "Télécharger les fichier Excel par Mois",
    accept_multiple_files=True,
    type=["xlsx"]
)

if not xls_files:
    st.warning("Please upload Excel files to proceed.")
    st.stop()
else:
    df_data_mois = load_data_multiple_excel(xls_files)
    if df_data_mois["success"]:
        df_mois = df_data_mois["df"]
        df_mois = df_mois.sort_values(by=["YEAR", "MOIS_NUM", "MOIS"])
    else:
        st.warning(df_data_mois["message"])
        st.stop()

# Create Two Tabs
global_tab, prevendeur_tab = st.tabs(
    ["Etat Par Mois", "Etat Prevendeur détails"],
    default="Etat Par Mois"
)
# ----------------------------------------------------------------
# --- TOTALS ---
# -----------------------------------------------
#
# -- DEBUG
# global_tab.dataframe(df_mois)
# -----------------------------------------------

df_total_par_mois = utils.build_totals_mois(df_mois)

# --- Grand Total ---
df_grand_total = pd.DataFrame({
    "livraison": [df_total_par_mois["livraison"].sum()],
    "benefice": [df_total_par_mois["benefice"].sum()],
})
# --------------------------------------------------------
global_tab.space()
global_tab.subheader("📊 Totaux mensuels _Livraison_ & _Bénéfice_", divider="grey", width="content")

# -- Display Grande Total --
for _, row in df_grand_total.iterrows():
    col1, col2 = global_tab.columns(2)
    col1.metric("💰 Livraison", f"{row['livraison']:,.0f} DA", border=True)
    col2.metric("📈 Bénéfice", f"{row['benefice']:,.0f} DA", border=True)
global_tab.divider()

# -- Display Total par MOIS --
for _, row in df_total_par_mois.iterrows():
    global_tab.markdown(f"##### 📆 {row['MOIS']} - {row['YEAR']}")
    widgets.display_totals(global_tab, row)

# ----------------------------
# --- Total Par Prevendeur ---
# ----------------------------
df_total_prevendeur_mois = utils.build_totals_prevendeur_mois(df_mois)
# -----------------------------------------------
# DEBUG
# global_tab.dataframe(df_total_prevendeur_mois)
# -----------------------------------------------

pivot = df_total_prevendeur_mois.pivot_table(
    index="PREVENDEUR",
    columns="MOIS",
    values=["livraison", "benefice"],
    aggfunc="sum",
    fill_value=0,
    margins=True, margins_name="Totals",
    sort=False
)
global_tab.space()
global_tab.subheader("📈 _Vue croisée Pré-vendeur / Mois_", divider="grey", width="content")
global_tab.space()
global_tab.dataframe(pivot, width="stretch")
global_tab.divider()
# --------------------
# --- Filter Month ---
# --------------------
months = df_total_prevendeur_mois.sort_values("MOIS_NUM")["MOIS"].unique()
selected_month = st.sidebar.selectbox(
    "📅 Choisir le mois",
    months,
    index=len(months) - 1  # default = latest month
)
st.sidebar.header(f"**{selected_month}**", text_alignment="center")
st.sidebar.divider()
# -------------------------------------------------------------------------------
#
global_tab.space()
global_tab.subheader(f"{selected_month}", text_alignment="center", divider="grey")

# DATAFRAME Total PREVEUNDEUR Per Month
df_selection_total_prev = df_total_prevendeur_mois[df_total_prevendeur_mois["MOIS"] == selected_month]
# -------------------------------
# -------------------------------
for _, row in df_selection_total_prev.iterrows():
    global_tab.markdown(f"##### 👤 {row['PREVENDEUR']}")
    widgets.display_prevendeur_totals(global_tab, row)

# Prevendeur Livraison Chart
total_livraison_chart = px.pie(
    df_selection_total_prev,
    names="PREVENDEUR",
    values="livraison",
    title="Livraison %",
    template="plotly_white",
)

# Prevendeur Bénéfice Chart
total_benefice_chart = px.pie(
    df_selection_total_prev,
    names="PREVENDEUR",
    values="benefice",
    title="Bénéfice %",
    template="plotly_white",
)
global_tab.space()
widgets.two_chart_columns(global_tab, total_livraison_chart, total_benefice_chart)
global_tab.divider()

# ---------------------------------------------------
# === Tableau Des Produit Etat Générale ===
# -----------------------------------------
# DATAFRAME GENERAL MOIS
df_selected_month = df_mois[df_mois["MOIS"] == selected_month]      # MOIS DATAFRAME
df_produit = (
    df_selected_month
    .groupby(["Produit"], as_index=False)
    .agg(
        qte=("Quantité", "sum"),
        livraison=("Total livraison (DA)", "sum"),
        benefice=("Total bénéfice (DA)", "sum")
    )
    .sort_values("qte", ascending=False)
    .rename(columns={"qte": "Quantité", "livraison": "Total Livraison", "benefice": "Total Bénéfice"})
)

global_tab.space()
global_tab.markdown("##### 🗃 Tableaux des Produit")
global_tab.space()

# --- Search Products
input_col, space_col = global_tab.columns(2)
search_product = input_col.text_input(
    label="Search Product",
    placeholder="Rechercher par produit",
    key="search_products",
    icon="🔎"
)
if search_product:
    mask = df_produit["Produit"].astype(str).str.contains(search_product, case=False, na=False)
    df_produit = df_produit[mask]

# Display the Product Dataframe
global_tab.dataframe(df_produit, hide_index=True)
global_tab.divider()

# ------------------------------------------
# ---- Grouped By Familly Etat Générale ----
# ------------------------------------------
global_tab.space()
global_tab.markdown("#### 📑 **Produits par Famille**")
global_tab.space()

familly_groupe, familly_chart = utils.familly_groupe(df_selected_month)     # Get the data
widgets.table_chart_column(global_tab, familly_groupe, familly_chart)       # Display table and chart side by side
global_tab.divider()

# -------------------------------------------
# ---- Grouped By S.Familly Etat Générale----
# -------------------------------------------
global_tab.space()
global_tab.markdown("#### 📑 _Produit par Sous famille %_")
global_tab.space()

famille = df_selected_month.sort_values("Famille")["Famille"].unique()
# Two Columns
col1, col2 = global_tab.columns(2)
selected_famille = col1.selectbox("Choisir la famille", famille, index=0, key="global_familly_selectbox")

global_tab.space()
sfamille_selection = df_selected_month[df_selected_month["Famille"] == selected_famille]
sfamilly_groupe, sfamilly_chart = utils.sfamilly_groupe(sfamille_selection)     # Get Famille DF, Famille Chart
widgets.table_chart_column(global_tab, sfamilly_groupe, sfamilly_chart)     # Display table and chart side by side
# -------------------------------------------------------------------------------------
#   === TAB PREVENDEUR DETAIL ===
# -------------------------------
#
# Sidebar Select Prevendeur
prevendeur = st.sidebar.pills(
    'Prevendeur:',
    options=df_mois["PREVENDEUR"].unique(),
    default=df_mois["PREVENDEUR"].unique()[0],
    key="prevendeur"
)
#
st.sidebar.header(f"**{prevendeur}**", text_alignment="center")
st.sidebar.divider()

# --- Total Livraison, Bénéfice For Selected Prevendeur ---
prevendeur_tab.space()      # First Space Tab
for _, row in df_selection_total_prev.iterrows():
    if row['PREVENDEUR'] == prevendeur:
        prevendeur_tab.markdown(f"#### 🛵 _{prevendeur} Détails_")
        # prevendeur_tab.subheader(f" _{prevendeur} Détail_", divider="grey", width="content")
        prevendeur_tab.space()
        widgets.display_prevendeur_totals(prevendeur_tab, row)              # Display Total metric
#
# --- Global Data Par Prevendeur ---
df_prevendeur = df_selected_month[df_selected_month["PREVENDEUR"] == prevendeur]
#
# --- Filter and Display Products ---
df_produit_prev = (
    df_selected_month
    .groupby(["Produit", "PREVENDEUR"], as_index=False)
    .agg(
        qte=("Quantité", "sum"),
        livraison=("Total livraison (DA)", "sum"),
        benefice=("Total bénéfice (DA)", "sum")
    )
    .sort_values("qte", ascending=False)
    .rename(columns={"qte": "Quantité", "livraison": "Total Livraison", "benefice": "Total Bénéfice"})
)
# DF Selected Prevendeur
df_produit_prev = df_produit_prev[df_produit_prev["PREVENDEUR"] == prevendeur]

prevendeur_tab.markdown("##### 🗃 Tableaux des Produit")
prevendeur_tab.space()

# Search Products
input_col, space_col = prevendeur_tab.columns(2)
search_product_prev = input_col.text_input(
    label="Search Product",
    placeholder="Rechercher par produit",
    key="search_products_prev",
    icon="🔎"
)
if search_product_prev:
    mask = df_produit_prev["Produit"].astype(str).str.contains(search_product_prev, case=False, na=False)
    df_produit_prev = df_produit_prev[mask]

prevendeur_tab.dataframe(df_produit_prev, hide_index=True)      # Display DataFrame
prevendeur_tab.divider()

# ----------------------------
# ---- Grouped By Familly ----
# ----------------------------
prevendeur_tab.space()
prevendeur_tab.markdown("#### 📑 **Produits par Famille**")
prevendeur_tab.space()

familly_groupe, familly_chart = utils.familly_groupe(df_prevendeur)             # Get Famille DF, Famille Chart
widgets.table_chart_column(prevendeur_tab, familly_groupe, familly_chart)       # Display table and chart side by side
prevendeur_tab.divider()

# ------------------------------
# ---- Grouped By S.Familly ----
# ------------------------------
prevendeur_tab.space()
prevendeur_tab.markdown("#### 📑 _Produit par Sous famille %_")
prevendeur_tab.space()

famille = df_prevendeur.sort_values("Famille")["Famille"].unique()
# Two Columns
col1, col2 = prevendeur_tab.columns(2)
selected_famille = col1.selectbox("Choisir le famille", famille, index=0)

prevendeur_tab.space()
sfamille_selection = df_prevendeur[df_prevendeur["Famille"] == selected_famille]
sfamilly_groupe, sfamilly_chart = utils.sfamilly_groupe(sfamille_selection)     # Get Famille DF, Famille Chart
widgets.table_chart_column(prevendeur_tab, sfamilly_groupe, sfamilly_chart)     # Display table and chart side by side
