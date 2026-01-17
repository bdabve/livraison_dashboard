#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# author        : el3arbi bdabve@gmail.com
# created       :
# desc          :
# ----------------------------------------------------------------------------

# import pandas as pd
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


# Load the dataframe with pandas and cache it with streamlit to avoid reload again and again
@st.cache_data
def load_data_from_excel(xls_file):
    data = utils.all_sheets(xls_file)
    return data


@st.cache_data
def load_data_multiple_excel(xls_files: list):
    data = utils.multiple_files(xls_files)
    return data


# Load data
excel_file = st.file_uploader("Télécharger le fichier Excel des Ventes", type=["xlsx"])

if not excel_file:
    st.warning("Please upload an Excel file to proceed.")
    st.stop()
else:
    all_sheets = load_data_from_excel(excel_file)
    if all_sheets["success"]:
        df = all_sheets["df"]
    else:
        st.warning(all_sheets["message"])
        st.stop()

# ==== Side Bar ======

# Select Prevendeur
prevendeur = st.sidebar.pills(
    'Prevendeur:',
    options=df["PREVENDEUR"].unique(),
    default=df["PREVENDEUR"].unique()[0],
    key="prevendeur"
)

st.sidebar.header(f"**{prevendeur}**", text_alignment="center")
st.sidebar.divider()


# --------------------------------------------------------------
# --- UI ----
#

st.divider()
st.space("medium")
st.subheader("📋 _Etat Global des Vente Par Produit_", divider="gray", width="content")

# -----------
# -- Totals
df_totals = utils.get_totals_vente(df, "VENTE")
widgets.display_totals(df_totals)                   # Display totals

# Total par Prevendeur
df_totals_prevendeur = utils.get_totals_vente(df, "PREVENDEUR")
df_totals_prevendeur = df_totals_prevendeur.sort_values(by="livraison", ascending=False)

# display product dataframe
st.space("medium")
st.markdown("#### *_Produits_*")
st.dataframe(df, hide_index=True)       # DUMP DATAFRAME
# ------------------------------
# ---- Etat Prevendeur %----
# ------------------------------
st.divider()
st.subheader("📋 _Etat Prevendeur_", divider="gray", width="content")
# st.space("medium")

for _, row in df_totals_prevendeur.iterrows():
    st.markdown(f"##### 👤 {row['PREVENDEUR']}")
    widgets.display_prevendeur_totals(row)          # Display metric totals

st.dataframe(df_totals_prevendeur, hide_index=True)      # DATAFRAME TOTALS PREV

total_livraison_chart = px.pie(
    df_totals_prevendeur,
    names="PREVENDEUR",
    values="livraison",
    title="Livraison",
    template="plotly_white",
)

# Bénéfice
total_benefice_chart = px.pie(
    df_totals_prevendeur,
    names="PREVENDEUR",
    values="benefice",
    title="Bénéfice",
    template="plotly_white",
)
widgets.two_chart_columns(total_livraison_chart, total_benefice_chart)

# ----------------------------
# ---- The  ----
# ----------------------------
st.divider()
st.space()

for _, row in df_totals_prevendeur.iterrows():
    if row['PREVENDEUR'] == prevendeur:
        st.subheader(f"🛵 _{prevendeur} Détail_", width="content")
        st.space()
        widgets.display_prevendeur_totals(row)              # Display Total metric

df_prevendeur = df[df["PREVENDEUR"].isin([prevendeur])]     # DF_PREVENDEUR
st.dataframe(df_prevendeur, hide_index=True)                # Display DataFrame

# ----------------------------
# ---- Grouped By Familly ----
# ----------------------------
st.divider()
st.space("medium")
st.subheader("💹 _Produit par Famille_", divider="gray", width="content")
fields = ["Quantité", "Total livraison (DA)", "Total bénéfice (DA)"]            # Fields
familly_groupe = df_prevendeur.groupby("Famille", as_index=False)[fields].sum()
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

# -----------------------------------
# ---- TODO: Prevendeur By Month ----
# -----------------------------------
st.divider()
st.space()
st.subheader("📆 _Etat Par Mois_", divider="gray", width="content")
st.space()
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

st.dataframe(df_mois, hide_index=True)
