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
st.title(":bar_chart: _Livraison Dashboard_", text_alignment="center")
st.space()


# Load the dataframe with pandas and cache it with streamlit to avoid reload again and again
@st.cache_data
def load_data_from_excel(excel_file, sheet_name):
    df = pd.read_excel(excel_file, sheet_name=sheet_name, usecols="A:H", nrows=243)
    data = utils.clean_dataframe(df)
    return data


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
    sheets = f.sheet_names
    sheet_name = st.selectbox("Sélectionner la feuille Excel:", sheets)
    st.session_state.sheet_name = {"sheet_name": sheet_name}

if st.session_state.get("sheet_name"):
    data = load_data_from_excel(excel_file, sheet_name)
    if not data["success"]:
        st.warning(data["message"])
        st.stop()
    else:
        df = data["df"]
else:
    st.warning("Please select a sheet to proceed.")
    st.stop()

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
st.space()
etat_excel = utils.etat_excel_like_db(df_selection)

st.subheader("💰 _Etat Mensuel_", text_alignment="left", divider="gray", width="stretch")
data_column, fig_etat_column = st.columns(2)

with data_column:
    st.space("large")
    st.markdown(f"""
        ##### *CRÉDIT:* :orange[💲 {etat_excel['CREDIT']}]
        ##### VERSEMENT CRÉDIT : :green[💵 {etat_excel['VERS. CREDIT']}]
        ##### *ACCOMPTE:* :grey[💲 {etat_excel['ACCOMPTE']}]
        ##### *CHARGES:* :red[💲 {etat_excel['CHARGES']}]""")

# Convert to Pandas dataframe
etat_excel_pd = pd.DataFrame(etat_excel.items(), columns=["TYPE", "MONTANT"])
etat_excel_pd["MONTANT_PIE"] = etat_excel_pd["MONTANT"].abs()       # convert to absolute values

fig_etat = px.pie(
    etat_excel_pd,
    names="TYPE",
    values="MONTANT_PIE",
    # title="<b>Etat Versement et Commandes</b>",
    template="plotly_white",
)
fig_etat_column.plotly_chart(fig_etat, width="stretch")
st.divider()
# ---------------------------------------------------------------------------------
# Display the daily report
# ------------------------
fields = ["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF"]
etat_journalier = utils.etat_journalier(df, fields)

st.subheader("📋 _Etat Journalier_", divider="gray", width="content")
st.dataframe(
    etat_journalier,
    column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
    hide_index=True
)
st.divider()

# ---------------------------------------------------------------------------------
st.subheader("💵 Etat _Versements_, _Commandes_ Par Jours", divider="gray", width="content")
df_plot = etat_journalier[etat_journalier["Date"] != "TOTAL"]
fig_versement = px.line(
    df_plot,
    x="Date",
    y=["VERSEMENT", "T. COMMANDE"],
    hover_data={"Date": "|%B %d, %Y"},
    template="plotly_white",
)

# Display the charts
st.plotly_chart(fig_versement, width="stretch")
st.divider()

# ----------------------------------------------------
# Etat Total par Livreur
# ------------------------
st.space()
st.subheader("🚚 _Etat Versement Par Livreur_", divider="gray", width="content")
livreur_selection = st.multiselect(
    'Sélectionner les livreurs à afficher:',
    options=df['LIVREUR'].unique(),
    default=df['LIVREUR'].unique(),
    width=500
)
# Display Result in 2 Columns
table_column, fig_livreur_column = st.columns(2)

sum_by_driver = utils.sum_by_driver(df, fields, livreur_selection=livreur_selection)
# Graphique Versement par Livreur
if len(sum_by_driver) == 0:
    st.warning("Aucun livreur sélectionné.")
else:
    with table_column:
        # display the table result
        st.space("large")
        st.dataframe(
            sum_by_driver,
            column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
            width="stretch"
        )
    # Create the figure
    fig_livreur = px.histogram(
        sum_by_driver,
        x=sum_by_driver.index,
        y=["VERSEMENT", "CHARGE"],
        barmode="group",
        # title="<b>Versement par Livreur</b>",
        text_auto=True,
        template="plotly_white",
    )
    # display the chart
    fig_livreur_column.plotly_chart(fig_livreur, width="stretch")

st.divider()

# ------------------------------
# Versement Livreur Pourcentage
sum_by_driver = sum_by_driver.reset_index()

versement_pourcent, commande_pourcent = st.columns(2)
with versement_pourcent:
    st.subheader("💵 _Etat Versement_", divider="gray", width="content")
    fig_pourcent = px.pie(
        sum_by_driver,
        names="LIVREUR",
        values="VERSEMENT",
        title="<b>Pourcentage de Versement par Livreur</b>",
        template="plotly_white",
    )
    st.plotly_chart(fig_pourcent, width="stretch")

with commande_pourcent:
    st.subheader("🛵 _Etat Prevendeur_", divider="gray", width="content")
    cmd_fig_pourcent = px.pie(
        sum_by_driver,
        names="LIVREUR",
        values="T.LOGICIEL",
        title="<b>Pourcentage des Commandes par Livreur</b>",
        template="plotly_white",
    )
    st.plotly_chart(cmd_fig_pourcent, width="stretch")

st.divider()

# ---------------------------------------------------------------------------------
# ---- Retour ----
# ----------------
driver_retour, sum_retour_by_driver = utils.driver_retour(df)
sum_retour_by_driver = sum_retour_by_driver[sum_retour_by_driver["LIVREUR"].isin(["AMINE", "TOUFIK", "REDA"])]
st.subheader("🔄 _Etat Retours Par Livreur_", divider="gray", width="content")

sum_retour_column, fig_retour_column = st.columns(2)
with sum_retour_column:
    st.space("large")
    st.dataframe(
        sum_retour_by_driver,
        hide_index=True,
        width="stretch"
    )

fig_retour = px.pie(
    sum_retour_by_driver,
    names="LIVREUR",
    values="RETOUR",
    title="<b>Retour par Livreur</b>",
    template="plotly_white",
)
fig_retour_column.plotly_chart(fig_retour, width="stretch")
st.divider()


# ---------------------------------------------
# ---- Details for a specific date ----
# -------------------------------------
@st.dialog("Details Journalier")
def day_details():
    import datetime
    st.write("Entrée la date:")
    date = st.date_input("Date:", datetime.date(2025, 12, 1))
    if st.button("Submit"):
        st.session_state.day_details = {"day_details": date}
        st.rerun()


label_column, button_column = st.columns([0.3, 0.3])
with label_column:
    st.write("Cliquer sur le bouton pour voir les détails par jour.")
with button_column:
    st.button("Sélectionner Le Jour.", on_click=day_details)

# Proccessing
if "day_details" not in st.session_state:
    pass
else:
    date = st.session_state.day_details["day_details"]
    st.subheader(f"📅 _Détails pour le {date.strftime('%d/%m/%Y')}_", divider="gray", width="content")

    fields = st.multiselect(
        "Sélectionner les champs à afficher:",
        options=["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF", "OBSERVATION"],
        default=["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF", "OBSERVATION"]
    )
    day_details = utils.show_day_details(df, date, fields)
    if not day_details["success"]:
        st.warning("Aucune donnée pour cette date.")
    else:
        day_details = day_details["data"]
        st.dataframe(
            day_details,
            column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
            hide_index=True,
            width="stretch"
        )
st.divider()

# ---------------------------------------------
# ---- Observations ----
# ----------------------
st.subheader("🧾 Les Observations", divider="gray", width="content")
observations = utils.driver_observations(df)
options_column, display_column = st.columns([0.4, 0.6], border=True, gap="small")
with options_column:
    option = st.selectbox(
        "Sélectionner le livreur pour voir les observations:",
        options=observations["LIVREUR"].unique()
    )
with display_column:
    filtered_observations = observations[observations["LIVREUR"] == option]
    st.markdown(f"##### Observations pour le livreur: {option}")
    for obs in filtered_observations["OBSERVATION"]:
        parts = obs.split("•")
        cleaned_lines = []
        for part in parts:
            part = part.strip()
            if part:
                cleaned_lines.append(part)
        try:
            cleaned_lines[0] = f"- {cleaned_lines[0]}"
            st.markdown("\n- ".join(cleaned_lines))
        except IndexError:
            st.markdown("- Aucune observation.")


# hide some stylesheet
# hide_st_style = '''
# <style>
#     #MainMenu { visibility: hidden; }
#     header { visibility: hidden; }
#     footer { visibility: hidden; }
# </style>
# '''
# st.markdown(hide_st_style, unsafe_allow_html=True)
