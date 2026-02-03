#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
import pandas as pd
import streamlit as st
import plotly.express as px

import utils
import widgets


def render_livreur_tab(livreur_tab, dfs):
    # --------------------------------
    # ---- Livreur Report Tab   ----
    # --------------------------------
    selected_year_livreur = st.sidebar.selectbox(
        "📅 Choisir l'année",
        options=sorted(dfs["YEAR"].unique()),
        index=len(dfs["YEAR"].unique()) - 1
    )
    # with lv_month_column:
    months = dfs.sort_values("MOIS")["MOIS"].unique()
    selected_month_livreur = st.sidebar.selectbox(
        "📅 Choisir le mois",
        options=sorted(dfs["MOIS"].unique()),
        index=len(dfs["MOIS"].unique()) - 1,
    )
    st.sidebar.header(f"**{selected_month_livreur}-{selected_year_livreur}**", text_alignment="center")
    st.sidebar.divider()

    # --- Select the month/year df to work with
    df_livreur = dfs[
        (dfs["YEAR"] == selected_year_livreur) &
        (dfs["MOIS"] == selected_month_livreur)
    ]
    if df_livreur.empty:
        livreur_tab.warning(f"Aucune donnée pour le mois **{selected_month_livreur}-{selected_year_livreur}**.")
        st.stop()

    livreur_tab.space()

    # ----------------------------------------------------------------------------
    # --- Filter Month ---
    #
    # --- Filter by Livreur
    st.sidebar.header('Filtré:')
    livreur = st.sidebar.pills(
        'LIVREUR:',
        options=df_livreur['LIVREUR'].unique(),
        default=df_livreur['LIVREUR'].unique(),
        selection_mode="multi",
        key="livreur"
    )

    # --- Etat Excel Like
    etat_excel = utils.etat_excel_like_db(df_livreur)

    livreur_tab.subheader("💰 _Etat Mensuel_", text_alignment="left", divider="gray", width="stretch")

    # Metrics for Etats Excel
    credit_column, vers_credit_column, acompte_column = livreur_tab.columns(3)      # Columns
    credit_column.metric("💲 *CRÉDIT:* ", etat_excel.get("CREDIT", 0), border=True)
    vers_credit_column.metric("💰 *Versements CRÉDIT:* ", etat_excel.get('VERS. CREDIT', 0), border=True)
    acompte_column.metric("💳 *ACCOMPTE:* ", etat_excel.get('ACCOMPTE', 0), border=True)
    #
    command_column, versement_column, charges_column = livreur_tab.columns(3)        # Columns
    command_column.metric("🛵 *TOTAL COMMANDE:* ", etat_excel.get('TOTAL COMMANDE', 0), border=True)
    versement_column.metric("🚚 *VERSEMENT:* ", etat_excel.get('VERSEMENT', 0), border=True)
    charges_column.metric("💸 *CHARGES:* ", etat_excel.get('CHARGES', 0), border=True)
    livreur_tab.divider()

    # Convert to Pandas dataframe
    etat_excel_pd = pd.DataFrame(etat_excel.items(), columns=["TYPE", "MONTANT"])
    etat_excel_pd["MONTANT"] = etat_excel_pd["MONTANT"].abs()       # convert to absolute values

    etat_types = livreur_tab.pills(
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
    widgets.table_chart_column(livreur_tab, etat_excel_pd, fig_etat)
    livreur_tab.divider()

    # ----------------------------------
    # ---> Report Etat Journalier  <----
    # ----------------------------------
    fields = ["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF"]
    livreur_tab.subheader("📋 _Etat Journalier_", divider="gray", width="content")
    etat_journalier = pd.pivot_table(
        df_livreur,
        index="DATE",
        values=fields,
        aggfunc="sum",
        margins=True, margins_name="TOTAL",
        fill_value=0,
        sort=False
    )
    etat_journalier.name = "Date"
    livreur_tab.dataframe(etat_journalier)       # Dispaly in Streamlit
    livreur_tab.divider()

    # ----------------------------------------------------
    # ----< Graphique Versement et Commande Par Jour <----
    # ----------------------------------------------------
    livreur_tab.subheader("💵 Etat _Versements_, _Commandes_ Par Jours", divider="gray", width="content")
    # Prepare the data for the Chart
    df_plot = (
        df_livreur.groupby("DATE")[["VERSEMENT", "T. COMMANDE"]]
        .sum()
        .sort_index()
        .reset_index()
    )
    # Build the Chart
    fig_versement = px.line(
        df_plot,
        x="DATE",
        y=["VERSEMENT", "T. COMMANDE"],
        markers=True,
        hover_data={"DATE": "|%B %d, %Y"},
        template="plotly_white",
    )

    fig_versement.update_layout(
        title="Évolution des versements et commandes",
        xaxis_title="Date",
        yaxis_title="Montant (DA)",
        legend_title="Type",
    )
    # Display the Chart
    livreur_tab.plotly_chart(fig_versement, width="stretch")
    livreur_tab.divider()

    # --------------------------------
    # ---< Etat Total par Livreur >---
    # --------------------------------
    livreur_tab.space()
    livreur_tab.subheader("🚚 _Etat Versement Par Livreur_", divider="gray", width="content")
    fields = ["VERSEMENT", "CHARGE"]
    sum_by_driver = utils.sum_by_driver(df_livreur, fields, livreur_selection=livreur)
    sum_by_driver = sum_by_driver.sort_values(by="VERSEMENT", ascending=False)
    # Graphique Versement par Livreur
    if len(sum_by_driver) == 0:
        livreur_tab.warning("Aucun livreur sélectionné.")
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
        fig_livreur.update_layout(
            xaxis_title="Livreur",
            yaxis_title="Montant (DA)",
            legend_title="Type",
        )
        # display the chart
        widgets.table_chart_column(livreur_tab, sum_by_driver.reset_index(), fig_livreur)
    livreur_tab.divider()

    # ----------------------------------------
    # ---< Versement Commande Pourcentage >---
    # ----------------------------------------
    fields = ["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF"]
    sum_by_driver = utils.sum_by_driver(df_livreur, fields, livreur_selection=livreur)
    sum_by_driver = sum_by_driver.reset_index()
    # Versement Chart
    etat_vers_chart = px.pie(
        sum_by_driver,
        names="LIVREUR",
        values="VERSEMENT",
        title="<b>💵 Etat Versement</b>",
        template="plotly_white",
    )
    # Commande Chart
    etat_cmd_chart = px.pie(
        sum_by_driver,
        names="LIVREUR",
        values="T.LOGICIEL",
        title="<b>🛵 Etat Prevendeur</b>",
        template="plotly_white",
    )
    widgets.two_chart_columns(livreur_tab, etat_vers_chart, etat_cmd_chart)
    livreur_tab.divider()

    # ----------------
    # ---< Retour >---
    # ----------------
    livreur_tab.subheader("🔄 _Etat Retours Par Livreur_", divider="gray", width="content")
    livreur_tab.code(
        "Le retour est calculé comme la différence entre 'T. COMMANDE' et 'T.LOGICIEL'.",
        language="markdown"
    )
    driver_retour, sum_retour_by_driver = utils.driver_retour(df_livreur)
    sum_retour_by_driver = sum_retour_by_driver[sum_retour_by_driver["LIVREUR"].isin(livreur)]

    retour_chart = px.pie(
        sum_retour_by_driver,
        names="LIVREUR",
        values="RETOUR",
        # title="<b>Retour par Livreur</b>",
        template="plotly_white",
    )
    widgets.table_chart_column(livreur_tab, sum_retour_by_driver, retour_chart)
    livreur_tab.divider()

    # -------------------------------------
    # ---< Details for a specific date >---
    # -------------------------------------
    @st.dialog("Details Journalier")
    def day_details():
        import datetime
        livreur_tab.write("Entrée la date:")
        month_num = utils.MONTHS_NAMES.get(selected_month_livreur)
        date = st.date_input("Date:", datetime.date(int(selected_year_livreur), int(month_num), 1))
        if st.button("Submit"):
            st.session_state.day_details = {"day_details": date}
            st.rerun()

    label_column, button_column = livreur_tab.columns([0.7, 0.3], vertical_alignment="bottom")
    label_column.subheader("📅 _Détails Journée_", divider="gray", width="content")
    with button_column:
        st.space("small")
        st.button("Sélectionner Le Jour.", on_click=day_details)

    # Proccessing day details
    if "day_details" not in st.session_state:
        pass
    else:
        date = st.session_state.day_details["day_details"]
        livreur_tab.space("medium")

        # Get Fields from pills
        fields = livreur_tab.pills(
            "Sélectionner les champs à afficher:",
            options=df_livreur.columns.tolist()[2:],        # skip the DATE and LIVREUR column
            default=df_livreur.columns.tolist()[2:],
            selection_mode="multi"
        )
        livreur_tab.space()
        livreur_tab.markdown(f"#### Le {date.strftime('%d/%m/%Y')}", text_alignment="right")
        day_details = utils.get_day_details(df_livreur, date, fields)
        if not day_details["success"]:
            livreur_tab.warning("Aucune donnée pour cette date.")
        else:
            day_details = day_details["data"]

            livreur_tab.dataframe(
                day_details,
                column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")},
                hide_index=True,
                width="stretch"
            )
    livreur_tab.divider()

    # ----------------------
    # ---< Observations >---
    # ----------------------
    livreur_tab.subheader("🧾 Les Observations", divider="gray", width="content")
    observations = utils.driver_observations(df_livreur)
    options_column, display_column = livreur_tab.columns([0.4, 0.6], border=True, gap="small")
    with options_column:
        obs_livreur = st.selectbox(
            "Sélectionner le livreur pour voir les observations:",
            options=observations["LIVREUR"].unique()
        )
    with display_column:
        filtered_observations = observations[observations["LIVREUR"] == obs_livreur]
        # livreur_tab.markdown(f"##### **{obs_livreur}** Observations")
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
