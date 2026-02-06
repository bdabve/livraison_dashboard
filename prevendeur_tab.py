#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
import utils
import widgets


def render_prevendeur_tab(st, prevendeur_tab, df_mois, selected_month, df_selected_month):
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

    # ==< Total Livraison, Bénéfice For Selected Prevendeur >==
    prevendeur_tab.space()      # First Space Tab
    df_total_prevendeur_mois = utils.build_totals_prevendeur_mois(df_mois)      # Rebuild totals
    df_selection_total_prev = df_total_prevendeur_mois[df_total_prevendeur_mois["MOIS"] == selected_month]

    for _, row in df_selection_total_prev.iterrows():
        if row['PREVENDEUR'] == prevendeur:
            prevendeur_tab.markdown(f"#### 🛵 _{prevendeur} Détails_")
            prevendeur_tab.space()
            widgets.display_prevendeur_totals(prevendeur_tab, row)              # Display Total metric

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
    # DF Product Par Prevendeur
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
