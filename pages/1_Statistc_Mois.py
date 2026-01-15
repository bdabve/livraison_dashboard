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
excel_file = st.file_uploader("Télécharger le fichier Excel de Livraison", type=["xlsx"])

if not excel_file:
    st.warning("Please upload an Excel file to proceed.")
    st.stop()
else:
    f = pd.ExcelFile(excel_file)
    sheets = f.sheet_names
    st.space("medium")
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
st.sidebar.header(f"**{sheet_name}**", text_alignment="center")
st.sidebar.divider()

# Filter by Livreur
st.sidebar.header('Filtré:')
livreur = st.sidebar.pills(
    'LIVREUR:',
    options=df['LIVREUR'].unique(),
    default=df['LIVREUR'].unique(),
    selection_mode="multi",
    key="livreur"
)

# Filter data based on selection
# df_selection = df.query('LIVREUR == @livreur')

# ----------------------
# ---- Etat Mensuel ----
# ----------------------
st.space()
etat_excel = utils.etat_excel_like_db(df)

st.subheader("💰 _Etat Mensuel_", text_alignment="left", divider="gray", width="stretch")

credit_column, versement_credit_column, acompte_column = st.columns(3)      # Columns
credit_column.error(f"*CRÉDIT:* {etat_excel.get('CREDIT', 0)}", icon="💲")
versement_credit_column.info(f"Versements CRÉDIT {etat_excel.get('VERS. CREDIT', 0)}", icon="💲")
acompte_column.warning(f"*ACCOMPTE:* {etat_excel.get('ACCOMPTE', 0)}", icon="💲")
#
command_column, versement_column, charges_column = st.columns(3)        # Columns
command_column.success(f"*TOTAL COMMANDE:* {etat_excel.get('TOTAL COMMANDE', 0)}", icon="🛵")
versement_column.success(f"*VERSEMENT:* {etat_excel.get('VERSEMENT', 0)}", icon="🚚")
charges_column.error(f"*CHARGES:* {etat_excel.get('CHARGES', 0)}", icon="💸")

st.divider()

# Convert to Pandas dataframe
etat_excel_pd = pd.DataFrame(etat_excel.items(), columns=["TYPE", "MONTANT"])
etat_excel_pd["MONTANT"] = etat_excel_pd["MONTANT"].abs()       # convert to absolute values
etat_types = st.pills(
    "Sélectionner les types à afficher dans le graphique:",
    options=etat_excel_pd["TYPE"].tolist(),
    default=etat_excel_pd["TYPE"].tolist(),
    selection_mode="multi",
    key="etat_types"
)

etat_excel_pd = etat_excel_pd.query('TYPE == @etat_types')
fig_etat = px.pie(
    etat_excel_pd,
    names="TYPE",
    values="MONTANT",
    template="plotly_white",
)
# Display table and chart side by side
widgets.table_fig_columns(etat_excel_pd, fig_etat)
st.divider()

# ----------------------------------
# ---- Display the daily report ----
# ----------------------------------
fields = ["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF"]
etat_journalier = utils.etat_journalier(df, fields)

st.subheader("📋 _Etat Journalier_", divider="gray", width="content")
st.dataframe(
    etat_journalier,
    column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
    hide_index=True
)
st.divider()

# --------------------------------------------------
# ---- Graphique Versement et Commande Par Jour ----
# --------------------------------------------------
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

# --------------------------------
# ---- Etat Total par Livreur ----
# --------------------------------
st.space()
st.subheader("🚚 _Etat Versement Par Livreur_", divider="gray", width="content")
sum_by_driver = utils.sum_by_driver(df, fields, livreur_selection=livreur)

# Graphique Versement par Livreur
if len(sum_by_driver) == 0:
    st.warning("Aucun livreur sélectionné.")
else:
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
    widgets.table_fig_columns(sum_by_driver.reset_index(), fig_livreur)
st.divider()

# ------------------------------------------
# ---- Versement Commande Pourcentage ----
# ------------------------------------------
sum_by_driver = sum_by_driver.reset_index()

versement_pourcent, commande_pourcent = st.columns(2)
with versement_pourcent:
    st.subheader("💵 _Etat Versement_", divider="gray", width="content")
    fig_pourcent = px.pie(
        sum_by_driver,
        names="LIVREUR",
        values="VERSEMENT",
        title="<b>Pourcentage des Versements.</b>",
        template="plotly_white",
    )
    st.plotly_chart(fig_pourcent, width="stretch")

with commande_pourcent:
    st.subheader("🛵 _Etat Prevendeur_", divider="gray", width="content")
    cmd_fig_pourcent = px.pie(
        sum_by_driver,
        names="LIVREUR",
        values="T.LOGICIEL",
        title="<b>Pourcentage des Commandes.</b>",
        template="plotly_white",
    )
    st.plotly_chart(cmd_fig_pourcent, width="stretch")

st.divider()

# ----------------
# ---- Retour ----
# ----------------
st.subheader("🔄 _Etat Retours Par Livreur_", divider="gray", width="content")
st.code(
    "Le retour est calculé comme la différence entre 'T. COMMANDE' et 'T.LOGICIEL'.",
    language="markdown"
)
driver_retour, sum_retour_by_driver = utils.driver_retour(df)
sum_retour_by_driver = sum_retour_by_driver[sum_retour_by_driver["LIVREUR"].isin(livreur)]

retour_chart = px.pie(
    sum_retour_by_driver,
    names="LIVREUR",
    values="RETOUR",
    # title="<b>Retour par Livreur</b>",
    template="plotly_white",
)
widgets.table_fig_columns(sum_retour_by_driver, retour_chart)
st.divider()


# -------------------------------------
# ---- Details for a specific date ----
# -------------------------------------
@st.dialog("Details Journalier")
def day_details():
    import datetime
    st.write("Entrée la date:")
    month_num = utils.MONTHS_NAMES.get(sheet_name)
    date = st.date_input("Date:", datetime.date(2025, month_num, 1))
    if st.button("Submit"):
        st.session_state.day_details = {"day_details": date}
        st.rerun()


label_column, button_column = st.columns([0.7, 0.3], vertical_alignment="bottom")
with label_column:
    st.subheader("📅 _Détails Journée_", divider="gray", width="content")
    # st.write("Cliquer sur le bouton pour voir les détails par jour.")
with button_column:
    st.space("small")
    st.button("Sélectionner Le Jour.", on_click=day_details)

# Proccessing
if "day_details" not in st.session_state:
    pass
else:
    date = st.session_state.day_details["day_details"]
    # st.subheader(f"📅 _Détails pour le {}_", divider="gray", width="content")
    st.space("medium")
    fields = st.pills(
        "Sélectionner les champs à afficher:",
        options=df.columns.tolist()[2:],        # skip the DATE and LIVREUR column
        default=df.columns.tolist()[2:],
        selection_mode="multi"
    )
    st.space()
    st.markdown(f"#### Le {date.strftime('%d/%m/%Y')}", text_alignment="right")
    day_details = utils.get_day_details(df, date, fields)
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

# ----------------------
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
