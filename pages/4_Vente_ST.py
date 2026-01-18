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
month_tab, multi_month_tab = st.tabs(
    ["Vente Par Mois", "Vente Plusieur Mois"],
    default="Vente Plusieur Mois"
)
# ---------------------------------------------------

multi_month_tab.space()
multi_month_tab.markdown("##### 🗃 Tableaux des Données")
multi_month_tab.space()
multi_month_tab.dataframe(df_mois, hide_index=True)      # DATAFRAME CONTAINING ALL DATA

# --- TOTALS ---
df_total_par_mois = (
    df_mois
    .groupby("MOIS", as_index=False)
    .agg(
        livraison=("Total livraison (DA)", "sum"),
        benefice=("Total bénéfice (DA)", "sum"),
    )
)

# Grand Total
df_grand_total = pd.DataFrame({
    "livraison": [df_total_par_mois["livraison"].sum()],
    "benefice": [df_total_par_mois["benefice"].sum()],
})

multi_month_tab.space()
multi_month_tab.subheader("📊 _Totaux mensuels_ : Livraison & Bénéfice", divider="grey", width="content")

# == Display Grande Total
for _, row in df_grand_total.iterrows():
    col1, col2 = multi_month_tab.columns(2)
    col1.metric("💰 Livraison", f"{row['livraison']:,.0f} DA", border=True)
    col2.metric("📈 Bénéfice", f"{row['benefice']:,.0f} DA", border=True)
    multi_month_tab.divider()

# == Display Total par MOIS
for _, row in df_total_par_mois.iterrows():
    multi_month_tab.markdown(f"##### 📆 {row['MOIS']}")
    col1, col2 = multi_month_tab.columns(2)
    col1.metric("💰 Livraison", f"{row['livraison']:,.0f} DA", border=True)
    col2.metric("📈 Bénéfice", f"{row['benefice']:,.0f} DA", border=True)
    multi_month_tab.divider()

# --------------------------------------
# --- Total Par Prevendeur ---
# --------------------------------------
df_total_prevendeur_mois = utils.build_totals_prevendeur_mois(df_mois)

multi_month_tab.space()
multi_month_tab.subheader("📊 _Totaux mensuels_ : Prevendeur", divider="grey", width="content")
multi_month_tab.markdown("##### 🗃 Tableaux des Données")
multi_month_tab.dataframe(df_total_prevendeur_mois, hide_index=True)
multi_month_tab.divider()

# --------------------------------------------------
# Display in metrics
# for prevendeur, group in df_total_prevendeur_mois.groupby("PREVENDEUR"):

    # multi_month_tab.markdown(f"##### 👤 {prevendeur}")

    # for _, row in group.iterrows():
        # multi_month_tab.markdown(f"###### 📆 {row['MOIS']}")

        # col1, col2, _ = multi_month_tab.columns(3)
        # col1.metric("💰 Livraison", f"{row['livraison']:,.0f} DA", border=True)
        # col2.metric("📈 Bénéfice", f"{row['benefice']:,.0f} DA", border=True)

    # multi_month_tab.divider()
# --------------------------------------------------

# --------------------------------------------
# --- Comparing Values With Previous Month ---
# --------------------------------------------

# Show the latest Month
st.sidebar.divider()
months = (
    df_total_prevendeur_mois
    .sort_values("MOIS_NUM")["MOIS"]
    .unique()
)

selected_month = st.sidebar.selectbox(
    "📅 Choisir le mois",
    months,
    index=len(months) - 1  # default = latest month
)

st.sidebar.header(f"**{selected_month}**", text_alignment="center")
#
multi_month_tab.space()
multi_month_tab.subheader(f"{selected_month}", text_alignment="center", divider="grey")

# Select Month DF this work with the Totals DF
df_selection = df_total_prevendeur_mois[df_total_prevendeur_mois["MOIS"] == selected_month]
for _, row in df_selection.iterrows():
    multi_month_tab.markdown(f"##### 👤 {row['PREVENDEUR']}")
    c1, c2 = multi_month_tab.columns(2)
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
    multi_month_tab.divider()

# -------------------------------------------------------------------------
# TAB_ ONE MONTH
# -------------
total_livraison_chart = px.pie(
    df_selection,
    names="PREVENDEUR",
    values="livraison",
    title="Livraison",
    template="plotly_white",
)

# Bénéfice
total_benefice_chart = px.pie(
    df_selection,
    names="PREVENDEUR",
    values="benefice",
    title="Bénéfice",
    template="plotly_white",
)
multi_month_tab.space()
widgets.two_chart_columns(multi_month_tab, total_livraison_chart, total_benefice_chart)
# -----------------------------------------------------------------------------
multi_month_tab.divider()
multi_month_tab.space()

# Select Prevendeur
prevendeur = st.sidebar.pills(
    'Prevendeur:',
    options=df_mois["PREVENDEUR"].unique(),
    default=df_mois["PREVENDEUR"].unique()[0],
    key="prevendeur"
)

st.sidebar.header(f"**{prevendeur}**", text_alignment="center")
st.sidebar.divider()

# --- Month order (French) ---
mois_order = {
    "Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4,
    "Mai": 5, "Juin": 6, "Juillet": 7, "Août": 8,
    "Septembre": 9, "Octobre": 10,
    "VENTE_NOVEMBRE_2025.xlsx": 11,
    "VENTE_DECEMBRE_2025.xlsx": 12,
}

for _, row in df_selection.iterrows():
    if row['PREVENDEUR'] == prevendeur:
        multi_month_tab.subheader(f"🛵 _{prevendeur} Détail_", divider="grey", width="content")
        multi_month_tab.space()
        widgets.display_prevendeur_totals(multi_month_tab, row)              # Display Total metric

df_prevendeur_totals = df_selection[df_selection["PREVENDEUR"] == prevendeur]     # DF_PREVENDEUR

# ----------------------------
# ---- Grouped By Familly ----
# ----------------------------
df_selected_month = df_mois[df_mois["MOIS"] == selected_month]
df_prevendeur = df_selected_month[df_selected_month["PREVENDEUR"] == prevendeur]

multi_month_tab.space("medium")
multi_month_tab.markdown("##### 🗃 Tableaux des Produit")
multi_month_tab.dataframe(df_prevendeur, hide_index=True)       # DUMP DATAFRAME

multi_month_tab.divider()
multi_month_tab.space("medium")
multi_month_tab.markdown("#### 💹 **Produits par Famille**")
multi_month_tab.space("medium")

fields = ["Quantité", "Total livraison (DA)", "Total bénéfice (DA)"]            # Fields
familly_groupe = df_prevendeur.groupby("Famille", as_index=False)[fields].sum()

# Chart
familly_chart = px.pie(
    familly_groupe,
    names="Famille",
    values="Quantité",
    title="Produit par famille",
    template="plotly_white",
)
# Display table and chart side by side
# with table_column:
# root.space("large")
table_column, chart_column = multi_month_tab.columns(2)
table_column.dataframe(familly_groupe, hide_index=True, width="stretch")
chart_column.plotly_chart(familly_chart, width="stretch")

# ----------------------------
# ---- Grouped By S.Familly ----
# ----------------------------
# TODO: select s.famille from selectbox familly
multi_month_tab.divider()
multi_month_tab.space("medium")
multi_month_tab.markdown("#### 💹 _Produit par Sous famille %_")
multi_month_tab.space("medium")

sfamilly_groupe = df_prevendeur.groupby("Sous famille", as_index=False)[["Quantité"]].sum()
# Chart
sfamilly_chart = px.pie(
    sfamilly_groupe,
    names="Sous famille",
    values="Quantité",
    template="plotly_white",
)
# Display table and chart side by side
table_column, chart_column = multi_month_tab.columns(2)
table_column.dataframe(sfamilly_groupe, hide_index=True, width="stretch")
chart_column.plotly_chart(sfamilly_chart, width="stretch")
# widgets.table_fig_columns(sfamilly_groupe, sfamilly_groupe_chart)
