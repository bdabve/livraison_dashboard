#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# author        : el3arbi bdabve@gmail.com
# created       :
# desc          :
# ----------------------------------------------------------------------------

import pandas as pd
import utils
import plotly.express as px
import streamlit as st
import widgets


# ------------------------
# == Configuration
# ------------------------
FAMILLE_FIELDS = ["Quantité", "Total livraison (DA)", "Total bénéfice (DA)"]            # Fields

st.set_page_config(page_title="Vente Dashboard", page_icon=":bar_chart:", layout="wide")
st.title("💱 _Vente_", text_alignment="center")
st.space()

# ----------------------------------------------------------------

# ----------------------------------------------------------------
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
    else:
        st.warning(df_data_mois["message"])
        st.stop()

# Create Two Tabs
global_tab, prevendeur_tab = st.tabs(
    ["Etat Par Mois", "Etat Prevendeur détails"],
    default="Etat Par Mois"
)
# ---------------------------------------------------
# === Tableau Des Produit Etat Générale ===
# -----------------------------------------
global_tab.space()
global_tab.markdown("##### 🗃 Tableaux des Données")
global_tab.space()
global_tab.dataframe(df_mois, hide_index=True)      # ALL DATAFRAME

# --- TOTALS ---
df_total_par_mois = (
    df_mois
    .groupby("MOIS", as_index=False)
    .agg(
        livraison=("Total livraison (DA)", "sum"),
        benefice=("Total bénéfice (DA)", "sum"),
    )
)
# --- Grand Total ---
df_grand_total = pd.DataFrame({
    "livraison": [df_total_par_mois["livraison"].sum()],
    "benefice": [df_total_par_mois["benefice"].sum()],
})

global_tab.space()
global_tab.subheader("📊 Totaux mensuels _Livraison_ & _Bénéfice_", divider="grey", width="content")

# == Display Grande Total ==
for _, row in df_grand_total.iterrows():
    col1, col2 = global_tab.columns(2)
    col1.metric("💰 Livraison", f"{row['livraison']:,.0f} DA", border=True)
    col2.metric("📈 Bénéfice", f"{row['benefice']:,.0f} DA", border=True)
    global_tab.divider()

# == Display Total par MOIS ==
for _, row in df_total_par_mois.iterrows():
    global_tab.markdown(f"##### 📆 {row['MOIS']}")
    col1, col2 = global_tab.columns(2)
    col1.metric("💰 Livraison", f"{row['livraison']:,.0f} DA", border=True)
    col2.metric("📈 Bénéfice", f"{row['benefice']:,.0f} DA", border=True)
    global_tab.divider()

# ----------------------------
# --- Total Par Prevendeur ---
# ----------------------------
df_total_prevendeur_mois = utils.build_totals_prevendeur_mois(df_mois)

global_tab.space()
global_tab.subheader("📊 _Totaux mensuels par Prevendeur_", divider="grey", width="content")
global_tab.markdown("##### 🗃 Tableaux des Données")
global_tab.space()
global_tab.dataframe(df_total_prevendeur_mois, hide_index=True)
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

# DATAFRAME GENERAL MOIS
df_selected_month = df_mois[df_mois["MOIS"] == selected_month]      # MOIS DATAFRAME
#
global_tab.space()
global_tab.subheader(f"{selected_month}", text_alignment="center", divider="grey")

# Select Month DF this work with the Totals DF
df_selection_total_prev = df_total_prevendeur_mois[df_total_prevendeur_mois["MOIS"] == selected_month]
for _, row in df_selection_total_prev.iterrows():
    global_tab.markdown(f"##### 👤 {row['PREVENDEUR']}")
    c1, c2 = global_tab.columns(2)
    c1.metric(
        "💰 Livraison",
        f"{row['livraison']:,.0f} DA",
        delta=f"{row['delta_livraison']:,.0f} DA",
        border=True
    )
    c2.metric(
        "📈 Bénéfice",
        f"{row['benefice']:,.0f} DA",
        delta=f"{row['delta_benefice']:,.0f} DA",
        border=True
    )
    global_tab.divider()

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

# ------------------------------------------
# ---- Grouped By Familly Etat Générale ----
# ------------------------------------------
global_tab.divider()
global_tab.space("medium")
global_tab.markdown("#### 💹 **Produits par Famille**")
global_tab.space("medium")

familly_groupe = df_selected_month.groupby("Famille", as_index=False)[FAMILLE_FIELDS].sum()
# Chart
familly_chart = px.pie(
    df_selected_month,
    names="Famille",
    values="Quantité",
    title="Produit par famille",
    template="plotly_white",
)
# Display table and chart side by side
widgets.table_chart_column(global_tab, familly_groupe, familly_chart)
# -------------------------------------------------------------------------------------
#   === TAB PREVENDEUR DETAIL ===
# -------------------------------
prevendeur = st.sidebar.pills(
    # Select Prevendeur
    'Prevendeur:',
    options=df_mois["PREVENDEUR"].unique(),
    default=df_mois["PREVENDEUR"].unique()[0],
    key="prevendeur"
)

st.sidebar.header(f"**{prevendeur}**", text_alignment="center")
st.sidebar.divider()

# --- Total Livraison, Bénéfice For Selected Prevendeur ---
for _, row in df_selection_total_prev.iterrows():
    if row['PREVENDEUR'] == prevendeur:
        prevendeur_tab.subheader(f"🛵 _{prevendeur} Détail_", divider="grey", width="content")
        prevendeur_tab.space()
        widgets.display_prevendeur_totals(prevendeur_tab, row)              # Display Total metric

# === Global Data Par Prevendeur ===
df_selected_month = df_mois[df_mois["MOIS"] == selected_month]
df_prevendeur = df_selected_month[df_selected_month["PREVENDEUR"] == prevendeur]
prevendeur_tab.space("medium")
prevendeur_tab.markdown("##### 🗃 Tableaux des Produit")
prevendeur_tab.space()
prevendeur_tab.dataframe(df_prevendeur, hide_index=True)       # DUMP DATAFRAME

# ----------------------------
# ---- Grouped By Familly ----
# ----------------------------
prevendeur_tab.divider()
prevendeur_tab.space("medium")
prevendeur_tab.markdown("#### 💹 **Produits par Famille**")
prevendeur_tab.space("medium")

familly_groupe = df_prevendeur.groupby("Famille", as_index=False)[FAMILLE_FIELDS].sum()

# Chart
familly_chart = px.pie(
    familly_groupe,
    names="Famille",
    values="Quantité",
    title="Produit par famille",
    template="plotly_white",
)
# Display table and chart side by side
widgets.table_chart_column(prevendeur_tab, familly_groupe, familly_chart)

# ------------------------------
# ---- Grouped By S.Familly ----
# ------------------------------
prevendeur_tab.divider()
prevendeur_tab.space("medium")
prevendeur_tab.markdown("#### 💹 _Produit par Sous famille %_")
prevendeur_tab.space("medium")

famille = df_prevendeur.sort_values("Famille")["Famille"].unique()
selected_famille = prevendeur_tab.selectbox(
    "Choisir le famille",
    famille,
    index=len(famille) - 1  # default = latest month
)
prevendeur_tab.space()

sfamille_selection = (df_prevendeur[df_prevendeur["Famille"] == selected_famille])
sfamilly_groupe = sfamille_selection.groupby("Sous famille", as_index=False)[FAMILLE_FIELDS].sum()

# Chart
sfamilly_chart = px.pie(
    sfamilly_groupe,
    names="Sous famille",
    values="Quantité",
    title="Produit Par Sous Famille %",
    template="plotly_white",
)
# Display table and chart side by side
widgets.table_chart_column(prevendeur_tab, sfamilly_groupe, sfamilly_chart)
