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

# Page configuration
st.set_page_config(page_title="Vente Dashboard", page_icon=":bar_chart:", layout="wide")
st.title("💱 _Vente_", text_alignment="center")
st.space()


# Load the dataframe with pandas and cache it with streamlit to avoid reload again and again
@st.cache_data
def load_data_from_excel(xls_file):
    data = utils.all_sheets(xls_file)
    return data


# Load data
excel_file = st.file_uploader("Télécharger le fichier Excel de Livraison", type=["xlsx"])

if not excel_file:
    st.warning("Please upload an Excel file to proceed.")
    st.stop()
else:
    all_sheets = load_data_from_excel(excel_file)
    if all_sheets["success"]:
        df_all_sheets = all_sheets["df"]
    else:
        st.warning(all_sheets["message"])
        st.stop()

    # Read By One Sheet
    f = pd.ExcelFile(excel_file)
    sheets = f.sheet_names
    st.space("medium")

    prevendeur = st.sidebar.pills(
        'Prevendeur:',
        options=df_all_sheets["PREVENDEUR"].unique(),
        # default="VENTE",
        key="prevendeur"
    )
    st.session_state.sheet_name = {"prevendeur": prevendeur}


# --------------------------------------------------------------
# --- ALL Sheets ----
st.divider()
st.space("medium")
st.subheader("📋 _Etat Global des Vente Par Produit_", divider="gray", width="content")

# -- Columns for Totals
total_livraison, total_benefice = utils.get_totals_vente(df_all_sheets, "VENTE")
widgets.display_totals(total_livraison, total_benefice)

st.dataframe(
    # This display all Sheets
    df_all_sheets,
    hide_index=True
)

# --------------------------------------------------------------
# ------- Side Bar -------
st.sidebar.header(f"**{prevendeur}**", text_alignment="center")
st.sidebar.divider()

# Filter by Livreur
# st.sidebar.header('Filtré:')

# ----------------------------
# ---- The All DataFrame ----
# ----------------------------
st.divider()
st.space("medium")
st.subheader("📋 _Etat Global des Vente Par Produit_", divider="gray", width="content")

# -- Columns for Totals
total_livraison, total_benefice = utils.get_totals_vente(df_all_sheets, prevendeur)

total_livraison_chart = px.pie(
    total_livraison,
    names="PREVENDEUR",
    values="Total livraison (DA)",
    template="plotly_white",
)
widgets.table_fig_columns(total_livraison, total_livraison_chart)   # Display table and chart side by side

# Bénéfice
total_benefice_chart = px.pie(
    total_benefice,
    names="PREVENDEUR",
    values="Total bénéfice (DA)",
    template="plotly_white",
)
widgets.table_fig_columns(total_benefice, total_benefice_chart)     # Display table and chart side by side


# ----------------------------
# ---- The Hole DataFrame ----
# ----------------------------
st.divider()
st.space("medium")
st.subheader("🛵 _Etat des Vente Par Prevendeur_", divider="gray", width="content")

# prev_total_livraison, prev_total_benefice = utils.get_totals_vente(df_all_sheets, prevendeur)
prev_total_livraison = total_livraison.loc[total_livraison["PREVENDEUR"] == prevendeur]["Total livraison (DA)"]
prev_total_benefice = total_benefice.loc[total_benefice["PREVENDEUR"] == prevendeur]["Total bénéfice (DA)"]

liv_col, benef_col = st.columns(2)
liv_col.dataframe(prev_total_livraison, hide_index=True)
benef_col.dataframe(prev_total_benefice, hide_index=True)
# FIXME
# widgets.display_totals(prev_total_livraison, prev_total_benefice)

df_prevendeur = df_all_sheets[df_all_sheets["PREVENDEUR"].isin([prevendeur])]
st.dataframe(
    # This display all the Global Prevendeur
    df_prevendeur,
    hide_index=True
)
# ----------------------------
# ---- Grouped By Familly ----
# ----------------------------
st.divider()
st.space("medium")
st.subheader("💹 _Produit par Famille_", divider="gray", width="content")

familly_groupe = df_prevendeur.groupby("Famille", as_index=False)[["Quantité", "Total livraison (DA)", "Total bénéfice (DA)"]].sum()
# Chart
famillyy_groupe_chart = px.pie(
    familly_groupe,
    names="Famille",
    values="Quantité",
    template="plotly_white",
)
# Display table and chart side by side
widgets.table_fig_columns(familly_groupe, famillyy_groupe_chart)

# ----------------------------
# ---- Grouped By S.Familly ----
# ----------------------------
st.divider()
st.space("medium")
st.subheader("💹 _Produit par Sous famille %_", divider="gray", width="content")

sfamilly_groupe = df_prevendeur.groupby("Sous famille", as_index=False)[["Quantité"]].sum()
# Chart
sfamilly_groupe_chart = px.pie(
    sfamilly_groupe,
    names="Sous famille",
    values="Quantité",
    template="plotly_white",
)
# Display table and chart side by side
widgets.table_fig_columns(sfamilly_groupe, sfamilly_groupe_chart)
