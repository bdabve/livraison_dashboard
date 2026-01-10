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

st.title(':bar_chart: Livraison Dashboard')
st.markdown('##')
accompte_column, credit_column = st.columns(2)
with accompte_column:
    st.subheader(f'ACCOMPTE: $ {etat_excel["ACCOMPTE"]:,}')

with credit_column:
    st.subheader(f'CREDIT: $ {etat_excel["CREDIT"]:,}')

versement_column, charge_column = st.columns(2)
with versement_column:
    st.subheader(f'VERS. CREDIT: $ {etat_excel["VERS. CREDIT"]:,}')

with charge_column:
    st.subheader(f'CHARGES: $ {etat_excel["CHARGES"]:,}')

st.markdown('---')

# Display the daily report
fields = ["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF"]
etat_journalier = utils.etat_journalier(df, fields)
st.subheader("Etat Journalier")
st.dataframe(
    etat_journalier,
    column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
    hide_index=True
)

st.markdown('---')
st.space()
st.subheader("Versement by Date")
# Plotly Bar Chart for VERSEMENT
df_plot = etat_journalier[etat_journalier["Date"] != "TOTAL"]
fig_versement = px.bar(
    df_plot,
    x="Date",
    y="VERSEMENT",
    orientation="v",
    title="<b>Versement Par Jour</b>",
    template="plotly_white",
    color_discrete_sequence=["#0083B8"],
)
# remove bg color for plot
fig_versement.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=(dict(showgrid=False))
)
# Display the charts
st.plotly_chart(fig_versement, use_container_width=True)


# ----------------------------------------------------
# Etat Total par Livreur
# ------------------------
sum_by_driver = utils.sum_by_driver(df_selection, fields)
st.subheader("Etat Total par Livreur")
st.dataframe(
    sum_by_driver,
    column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
)
print(sum_by_driver)

# Graphique Versement par Livreur
fig_livreur = px.bar(
    sum_by_driver,
    x=sum_by_driver.index,
    y="VERSEMENT",
    orientation="v",
    title="<b>Versement Par Livreur</b>",
    template="plotly_white",
    color_discrete_sequence=["#0083B8"],
)
# remove bg color for plot
fig_livreur.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=(dict(showgrid=False))
)
# Display the charts
st.plotly_chart(fig_livreur, use_container_width=True)

# Versement Livreur Pourcentage
sum_by_driver = sum_by_driver.reset_index()
total_versement = sum_by_driver["VERSEMENT"].sum()
sum_by_driver["VERSEMENT %"] = (sum_by_driver["VERSEMENT"] / total_versement * 100).round(2)

table_pourcent, plot_pourcent = st.columns(2)
with table_pourcent:
    st.subheader("Pourcentage de Versement par Livreur")
    st.dataframe(
        sum_by_driver[["LIVREUR", "VERSEMENT", "VERSEMENT %"]],
        column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
        hide_index=True
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

# Display the dataframe
st.subheader("Raw Data")
st.dataframe(
    df,
    column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")}
)

# hide some stylesheet
# hide_st_style = '''
# <style>
#     #MainMenu { visibility: hidden; }
#     header { visibility: hidden; }
#     footer { visibility: hidden; }
# </style>
# '''
# st.markdown(hide_st_style, unsafe_allow_html=True)
