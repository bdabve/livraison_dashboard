#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# author        : el3arbi bdabve@gmail.com
# created       :
# desc          :
# ----------------------------------------------------------------------------
import pandas as pd
import plotly.express as px

MONTHS_NAMES = {
    "JANVIER": 1, "FÉVRIER": 2, "MARS": 3, "AVRIL": 4,
    "MAI": 5, "JUIN": 6, "JUILLET": 7, "AOÛT": 8,
    "SEPTEMBRE": 9, "OCTOBRE": 10, "NOVEMBRE": 11, "DECEMBRE": 12
}
FAMILLE_FIELDS = ["Quantité", "Total livraison (DA)", "Total bénéfice (DA)"]            # Fields


def clean_dataframe(df):
    try:
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce").dt.date
    except KeyError:
        return {"success": False, "message": "La colonne 'DATE' est manquante dans le fichier Excel."}

    numeric_columns = ["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["DATE"].notna()]     # Remove rows without a valid DATE (e.g. subtotal / footer rows)
    df["OBSERVATION"] = df["OBSERVATION"].astype(str).replace("nan", "")
    df = df.fillna(0)
    return {"success": True, "df": df}


def etat_excel_like_db(clean_df):
    """
    this function return
    ["ACCOMTE", "CREDIT", "VERSEMENT CREDIT", "CHARGE"] to display in QLabel Excel Etat
    """
    versement = clean_df.groupby(["DATE"])[["VERSEMENT"]].sum()
    total_command = clean_df.groupby(["DATE"])[["T.LOGICIEL"]].sum()
    charges = clean_df.groupby(["DATE"])[["CHARGE"]].sum()

    # --- Sum VERSEMENT by LIVREUR ---
    vers_by_livreur = clean_df.groupby("LIVREUR", as_index=False)["VERSEMENT"].sum()
    livreur = vers_by_livreur[vers_by_livreur["LIVREUR"].isin(["ACCOMPTE", "CREDIT", "VERS. CREDIT"])]
    livreur = livreur.set_index("LIVREUR")

    retour = clean_df.copy()
    retour["RETOUR"] = retour["T. COMMANDE"] - retour["T.LOGICIEL"]
    total_retour = retour.groupby("LIVREUR", as_index=False)["RETOUR"].sum()
    # Extract values safely
    etat_excel = {
        "ACCOMPTE": float(livreur["VERSEMENT"].get("ACCOMPTE", 0)),
        "CREDIT": float(livreur["VERSEMENT"].get("CREDIT", 0)),
        "VERS. CREDIT": float(livreur["VERSEMENT"].get("VERS. CREDIT", 0)),
        "VERSEMENT": float(versement["VERSEMENT"].sum()),
        "TOTAL COMMANDE": float(total_command["T.LOGICIEL"].sum()),
        "CHARGES": float(charges["CHARGE"].sum()),
        "RETOUR": float(total_retour.set_index("LIVREUR").get("RETOUR", {}).sum()),
    }
    return etat_excel


def etat_journalier(clean_df, fields):
    """
    Total par jour avec ligne des totaux
    :clean_df: clean by date
    :fields: list of fields to sum
    """
    # --- SUM By Date
    daily_stats = clean_df.groupby("DATE")[fields].sum()       # without observation
    daily_stats = daily_stats.sort_values(by="DATE", ascending=True)
    # daily_stats.index = daily_stats.index.date  # Convert to date only

    # Create totals row
    total_row = pd.DataFrame(daily_stats.sum()).T
    total_row.index = ["TOTAL"]
    # Append totals inside table
    etat_journalier = pd.concat([daily_stats, total_row])
    etat_journalier.index.name = "Date"
    return etat_journalier.reset_index()


def sum_by_driver(clean_df, fields, livreur_selection=["AMINE", "TOUFIK", "REDA", "MOHAMED"]):
    """
    ETAT TOTAL BY LIVREUR
    clean_df: DataFrame
    fields: list of fields to sum
    """
    # --- TOTAL PAR LIVREUR SUMMARY ---
    driver_stats = clean_df.groupby("LIVREUR", as_index=False)[fields].sum()
    driver_stats = driver_stats[driver_stats["LIVREUR"].isin(livreur_selection)]
    driver_stats = driver_stats.set_index("LIVREUR")
    return driver_stats


def driver_retour(clean_df):
    """
    Calculate the difference between 'T. COMMANDE' and 'T.LOGICIEL'
    and return detailed rows + sum grouped by livreur.
    """
    df = clean_df.copy()
    df["RETOUR"] = df["T. COMMANDE"] - df["T.LOGICIEL"]

    retour = df[["DATE", "LIVREUR", "T. COMMANDE", "T.LOGICIEL", "RETOUR"]].dropna().copy()
    # Format DATE
    retour["DATE"] = retour["DATE"].dt.strftime("%d/%m/%Y")

    # === TOTAL ROW ===
    total_row = {
        "DATE": "",
        "LIVREUR": "TOTAL",
        "T. COMMANDE": retour["T. COMMANDE"].sum(),
        "T.LOGICIEL": retour["T.LOGICIEL"].sum(),
        "RETOUR": retour["RETOUR"].sum(),
    }

    # Append total row
    retour = pd.concat([retour, pd.DataFrame([total_row])], ignore_index=True)

    sum_retour_by_driver = (retour.groupby("LIVREUR")["RETOUR"].sum().reset_index())

    return retour, sum_retour_by_driver


def get_day_details(clean_df, day, fields):
    """
    Show details for a specific day
    :clean_df: DataFrame
    :day: str or datetime [YYYY-MM-DD]
    :fields: list of fields to sum
    """
    daily_details = clean_df.groupby(["DATE", "LIVREUR"])[fields].sum()
    # daily_details = daily_details.sort_values(by="T.LOGICIEL", ascending=False)
    daily_details["OBSERVATION"] = daily_details["OBSERVATION"].astype("string")

    # Convert input to datetime
    day = pd.to_datetime(day).normalize()

    if day in daily_details.index.get_level_values("DATE"):
        # TODO: return selected livreur
        return {"success": True, "data": daily_details.loc[day].reset_index()}
    else:
        return {"success": False, "data": "No data"}


def driver_observations(clean_df):
    """
    Generate observations for each driver based on their performance.
    :clean_df: DataFrame
    """
    driver_obs = clean_df.groupby(["LIVREUR"])["OBSERVATION"].sum()
    return driver_obs.reset_index()


# --------------------
# ---- VENTE PAGE ----
# --------------------
def all_sheets(file_name, multiple=False):
    xls = pd.ExcelFile(file_name)

    dfs = []
    cols = ["Famille", "Sous famille", "Produit", "Quantité.1", "Total livraison (DA)", "Total bénéfice (DA)"]
    try:
        for sheet in xls.sheet_names[1:]:
            df = pd.read_excel(file_name, sheet_name=sheet, skiprows=14, header=0)
            df = df[cols]       # Used coloumns
            df = df.rename(columns={"Quantité.1": "Quantité"})      # rename
            df["PREVENDEUR"] = sheet

            # This work with multiple file
            if multiple: df["MOIS"] = file_name.name.replace("xlsx", "")

            df = df[df["Famille"].notna()]      # Drop Totals
            dfs.append(df)

        final_df = pd.concat(dfs, ignore_index=True)
        return {"success": True, "df": final_df}
    except Exception as err:
        return {"success": False, "message": err}


def multiple_files(xls_files: list):
    dfs = []
    for up_file in xls_files:
        data = all_sheets(up_file, multiple=True)
        if data["success"]: dfs.append(data["df"])
        else: return {"success": False, "message": data["message"]}

    final_df = pd.concat(dfs, ignore_index=True)
    return {"success": True, "df": final_df}


def get_totals_vente(df, prevendeur):
    """
    Returns total livraison and total bénéfice.
    If prevendeur == 'VENTE' → global totals
    Else → totals grouped by PREVENDEUR
    """
    if prevendeur == "VENTE":
        return {
            "livraison": df["Total livraison (DA)"].sum(),
            "benefice": df["Total bénéfice (DA)"].sum(),
        }

    grouped = (
        df.groupby("PREVENDEUR", as_index=False)
        .agg(
            livraison=("Total livraison (DA)", "sum"),
            benefice=("Total bénéfice (DA)", "sum"),
        )
    )

    return grouped


def build_totals_prevendeur_mois(df_mois: pd.DataFrame) -> pd.DataFrame:
    """
    Total Par Prevendeur
    with delta of previous Mois
    """

    df = df_mois.copy()

    # --- Group totals ---
    df_total = (
        df.groupby(["PREVENDEUR", "MOIS"], as_index=False)
        .agg(
            livraison=("Total livraison (DA)", "sum"),
            benefice=("Total bénéfice (DA)", "sum"),
        )
    )

    # --- Month order (French) ---
    mois_order = {
        "Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4,
        "Mai": 5, "Juin": 6, "Juillet": 7, "Août": 8,
        "Septembre": 9, "Octobre": 10,
        "VENTE_NOVEMBRE_2025.xlsx": 11,
        "VENTE_DECEMBRE_2025.xlsx": 12,
    }

    df_total["MOIS_NUM"] = df_total["MOIS"].map(mois_order)

    # --- Sort correctly ---
    df_total = df_total.sort_values(["PREVENDEUR", "MOIS_NUM"])

    # --- Previous month values ---
    df_total["livraison_prev"] = df_total.groupby("PREVENDEUR")["livraison"].shift(1)
    df_total["benefice_prev"] = df_total.groupby("PREVENDEUR")["benefice"].shift(1)

    # ✅ Replace NaN with 0
    df_total[["livraison_prev", "benefice_prev"]] = (
        df_total[["livraison_prev", "benefice_prev"]].fillna(0)
    )

    # --- Delta ---
    df_total["delta_livraison"] = df_total["livraison"] - df_total["livraison_prev"]
    df_total["delta_benefice"] = df_total["benefice"] - df_total["benefice_prev"]

    return df_total.reset_index(drop=True)


def familly_groupe(df):
    """
    This will return
    df grouped by familly
    familly chart %
    """
    familly_groupe = (
        df
        .groupby("Famille", as_index=False)[FAMILLE_FIELDS]
        .sum()
        .sort_values("Quantité", ascending=False)
    )
    # Chart
    familly_chart = px.pie(
        df,
        names="Famille",
        values="Quantité",
        title="Produit par famille",
        template="plotly_white",
    )
    return familly_groupe, familly_chart


def sfamilly_groupe(df):
    sfamilly_groupe = (
        df.groupby("Sous famille", as_index=False)[FAMILLE_FIELDS]
        .sum()
        .sort_values("Quantité", ascending=False)
    )

    # Chart
    sfamilly_chart = px.pie(
        sfamilly_groupe,
        names="Sous famille",
        values="Quantité",
        title="Produit Par Sous Famille %",
        template="plotly_white",
    )
    return sfamilly_groupe, sfamilly_chart
