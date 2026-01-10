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

# Page configuration
st.set_page_config(page_title="Livraison Dashboard", page_icon=":bar_chart:", layout="wide")


# Load the dataframe with pandas and cache it with streamlit to avoid reload again and again
@st.cache_data
def load_data_from_excel():
    df = pd.read_excel('./2025-VERSEMENT_LIVREUR_2025.xlsx', sheet_name="DECEMBRE", usecols="A:H", nrows=243)
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    numeric_columns = ["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF"]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # df["OBSERVATION"] = df["OBSERVATION"].astype(str)
    # Remove rows without a valid DATE (e.g. subtotal / footer rows)
    df = df[df["DATE"].notna()]
    df = df.fillna(0)
    return df


# Load data
df = load_data_from_excel()

# ------- Side Bar -------
st.sidebar.header('Filtré:')

livreur = st.sidebar.multiselect(
    'LIVREUR:',
    options=df['LIVREUR'].unique(),
    default=df['LIVREUR'].unique()
)

# Filter data based on selection
df_selection = df.query('LIVREUR == @livreur')

# ----------------------------------------------------
# Etat Journalier
# ---------------
etat_excel = utils.etat_excel_like_db(df_selection)

st.title(":bar_chart: _Livraison Dashboard_", text_alignment="center")
st.space()

accompte_column, credit_column = st.columns(2)
with accompte_column:
    st.subheader(f'ACCOMPTE = {etat_excel["ACCOMPTE"]:,}')

with credit_column:
    st.subheader(f'CREDIT = {etat_excel["CREDIT"]:,}')

versement_column, charge_column = st.columns(2)
with versement_column:
    st.subheader(f'VERS. CREDIT: 💲 {etat_excel["VERS. CREDIT"]:,}')

with charge_column:
    st.subheader(f'CHARGES: 💲 {etat_excel["CHARGES"]:,}')

# ---------------------------------------------------------------------------------
# Display the daily report
fields = ["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF"]
etat_journalier = utils.etat_journalier(df, fields)

st.divider()
st.subheader("📋 _Etat Journalier_", divider="gray", width="content")
st.dataframe(
    etat_journalier,
    column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
    hide_index=True
)

# ---------------------------------------------------------------------------------
st.divider()
st.subheader("💵 Etat _Versements_, _Commandes_ Par Jours", divider="gray", width="content")
# Plotly Bar Chart for VERSEMENT
df_plot = etat_journalier[etat_journalier["Date"] != "TOTAL"]
fig_versement = px.line(
    df_plot,
    x="Date",
    y=["VERSEMENT", "T. COMMANDE"],
    hover_data={"Date": "|%B %d, %Y"},
    # orientation="v",
    title="<b>Etat Versement et Commandes</b>",
    template="plotly_white",
    # color_discrete_sequence=["#0083B8"],
)

# Display the charts
st.plotly_chart(fig_versement, use_container_width=True)

# ----------------------------------------------------
# Etat Total par Livreur
# ------------------------
st.divider()
st.space()
st.subheader("🚚 _Etat Versement Par Livreur_", divider="gray", width="content")
sum_by_driver = utils.sum_by_driver(df_selection, fields)
# sum_by_driver.fillna(0)

# Graphique Versement par Livreur
fig_livreur = px.histogram(
    sum_by_driver,
    x=sum_by_driver.index,
    y=["VERSEMENT", "CHARGE"],
    # color="VERSEMENT",
    barmode="group",
    title="<b>Versement par Livreur</b>",
    text_auto=True,
    template="plotly_white",
)

# Display Result in 2 Columns
table_column, plot_column = st.columns(2)
with table_column:
    st.dataframe(
        sum_by_driver,
        column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
        use_container_width=True
    )

with plot_column:
    st.plotly_chart(fig_livreur, use_container_width=True)  # Display the charts


# ------------------------------
# Versement Livreur Pourcentage
sum_by_driver = sum_by_driver.reset_index()
total_versement = sum_by_driver["VERSEMENT"].sum()
sum_by_driver["VERSEMENT %"] = (sum_by_driver["VERSEMENT"] / total_versement * 100).round(2)

table_pourcent, plot_pourcent = st.columns(2)
with table_pourcent:
    st.html("<b> Pourcentage de Versement par Livreur</b>")
    st.dataframe(
        sum_by_driver[["LIVREUR", "VERSEMENT", "VERSEMENT %"]],
        column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
        hide_index=True,
        use_container_width=True
    )

with plot_pourcent:
    fig_pourcent = px.pie(
        sum_by_driver,
        names="LIVREUR",
        values="VERSEMENT %",
        title="<b>Pourcentage de Versement par Livreur</b>",
        template="plotly_white",
    )
    st.plotly_chart(fig_pourcent, use_container_width=True)

# left_column, right_column = st.columns(2)
# left_column.plotly_chart(fig_versement, use_container_width=True)

# ---------------------------------------------------------------------------------
# ------- COMMANDES -------
st.divider()
st.subheader("🛵 _Etat Prevendeur_", divider="gray", width="content")
total_commandes = sum_by_driver["T. COMMANDE"].sum()
sum_by_driver["COMMANDE %"] = (sum_by_driver["T. COMMANDE"] / total_commandes * 100).round(2)

cmd_table_pourcent, cmd_plot_pourcent = st.columns(2)

with cmd_table_pourcent:
    st.html("<b> Pourcentage des <i>Commandes</i></b>")
    st.dataframe(
        sum_by_driver[["LIVREUR", "T. COMMANDE", "COMMANDE %"]],
        column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
        hide_index=True,
        use_container_width=True
    )

with cmd_plot_pourcent:
    cmd_fig_pourcent = px.pie(
        sum_by_driver,
        names="LIVREUR",
        values="COMMANDE %",
        title="<b>Pourcentage des Commandes par Livreur</b>",
        template="plotly_white",
    )
    st.plotly_chart(cmd_fig_pourcent, use_container_width=True)

# Display the dataframe
# st.subheader("Raw Data")
# st.dataframe(
    # df,
    # column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")}
# )

# hide some stylesheet
# hide_st_style = '''
# <style>
#     #MainMenu { visibility: hidden; }
#     header { visibility: hidden; }
#     footer { visibility: hidden; }
# </style>
# '''
# st.markdown(hide_st_style, unsafe_allow_html=True)
