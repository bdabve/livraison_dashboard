#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
import re
import os
import pandas as pd
import plotly.express as px

# --- Month Names to work with Versement Day Details ---
MONTHS_NAMES = {
    "JANVIER": 1, "FEVRIER": 2, "MARS": 3, "AVRIL": 4, "MAI": 5, "JUIN": 6, "JUILLET": 7,
    "AOUT": 8, "SEPTEMBRE": 9, "OCTOBRE": 10, "NOVEMBRE": 11, "DECEMBRE": 12,
}
# --- Month order (French) ---
mois_order = {
    "JANVIER": 1,
    "FÉVRIER": 2, "FEVRIER": 2,
    "MARS": 3, "AVRIL": 4, "MAI": 5, "JUIN": 6, "JUILLET": 7,
    "AOÛT": 8, "AOUT": 8,
    "SEPTEMBRE": 9, "OCTOBRE": 10,
    "NOVEMBRE": 11, "DECEMBRE": 12,
}

FAMILLE_FIELDS = ["Quantité", "Total livraison (DA)", "Total bénéfice (DA)"]            # Fields


# ------------------------------------------------------
# --- LIVRAISON PAGE ---
# ---------------------
def read_livraison_multi_year(files, selected_months):
    """
    Load multiple Excel files (years) and multiple months into one DataFrame.
    Filename must contain YEAR (e.g. LIVRAISON_2024.xlsx)
    """

    if not selected_months:
        return {"success": False, "message": "Aucun mois sélectionné."}

    if not isinstance(files, (list, tuple)):
        files = [files]

    dfs = []

    try:
        for file in files:
            # --- Extract YEAR from filename ---
            filename = os.path.basename(file.name)
            match = re.search(r"(\d{4})", filename)

            if not match:
                raise ValueError(f"Année introuvable dans le fichier: {filename}")

            year = int(match.group(1))

            # --- Read selected months ---
            for month in selected_months:
                if month not in pd.ExcelFile(file, None).sheet_names:
                    continue
                result = clean_dataframe(
                    pd.read_excel(file, sheet_name=month, usecols="A:H")
                )

                if not result["success"]:
                    return {"success": False, "message": result["message"]}

                df = (
                    result["df"].copy()
                    .assign(
                        YEAR=year,
                        MOIS=month,
                        MOIS_NUM=lambda x: x["MOIS"].map(mois_order),
                    )
                )
                dfs.append(df)

        final_df = pd.concat(dfs, ignore_index=True).sort_values(["YEAR", "MOIS_NUM"])
        # .drop(columns="MOIS_NUM")

        return {"success": True, "data": final_df}

    except ValueError as err:
        return {"success": False, "message": str(err)}


def read_livraison_files(excel_file, selected_months):
    """
    This function load multipla months in one df
    """
    dfs = []
    for month in selected_months:
        data = clean_dataframe(pd.read_excel(excel_file, sheet_name=month, usecols="A:H"))
        if data["success"]:
            df = data["df"]
            df["MOIS"] = month
            # --- Month order (French) ---
            df["MOIS_NUM"] = df["MOIS"].map(mois_order)
            df = df.sort_values("MOIS_NUM")             # .drop(columns=["MOIS_NUM"])

            dfs.append(df)
        else:
            return {"success": False, "message": data["message"]}
    try:
        dfs = pd.concat(dfs, ignore_index=True)
    except ValueError:
        return {"success": False, "message": "Aucun mois sélectionné."}
    else:
        return {"success": True, "data": dfs}


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
    Calculate RETOUR = T. COMMANDE - T.LOGICIEL
    Returns:
        - Detailed rows (with TOTAL row)
        - Sum of RETOUR grouped by LIVREUR
    """
    df = clean_df.copy()                                    # --- Work on a copy
    df["RETOUR"] = df["T. COMMANDE"] - df["T.LOGICIEL"]     # --- Compute RETOUR
    # --- Keep needed columns & drop NaNs
    retour = (
        df[["DATE", "LIVREUR", "T. COMMANDE", "T.LOGICIEL", "RETOUR"]]
        .dropna(subset=["T. COMMANDE", "T.LOGICIEL"])
        .copy()
    )
    # --- Sum RETOUR by driver (BEFORE adding TOTAL row)
    sum_retour_by_driver = (
        retour.groupby("LIVREUR", as_index=False)["RETOUR"]
        .sum()
    )
    # --- TOTAL row
    total_row = pd.DataFrame([{
        "DATE": None,
        "LIVREUR": "TOTAL",
        "T. COMMANDE": retour["T. COMMANDE"].sum(),
        "T.LOGICIEL": retour["T.LOGICIEL"].sum(),
        "RETOUR": retour["RETOUR"].sum(),
    }])
    # --- Append TOTAL row
    retour = pd.concat([retour, total_row], ignore_index=True)
    return retour, sum_retour_by_driver


def get_day_details(clean_df, day, fields):
    """
    Show details for a specific day
    :clean_df: DataFrame
    :day: str or datetime [YYYY-MM-DD]
    :fields: list of fields to sum
    """
    day = pd.to_datetime(day, errors="coerce").date()
    daily_details = (
        clean_df
        .groupby(["DATE", "LIVREUR"], as_index=False)[fields]
        .sum()
    )
    daily_details["OBSERVATION"] = daily_details["OBSERVATION"].astype("string")

    if day in daily_details["DATE"].values:
        return {"success": True, "data": daily_details[daily_details["DATE"] == day]}
    else:
        return {"success": False, "data": "No data"}


def driver_observations(clean_df):
    """
    Generate observations for each driver based on their performance.
    :clean_df: DataFrame
    """
    driver_obs = clean_df.groupby(["LIVREUR"])["OBSERVATION"].sum()
    return driver_obs.reset_index()


# ----------------------------------------------------------------------
# ---- VENTE PAGE ----
# --------------------
def read_sales_files(files):
    # Accept single file or list of files
    if not isinstance(files, (list, tuple)):
        files = [files]

    dfs = []
    cols = ["Famille", "Sous famille", "Produit", "Quantité.1", "Total livraison (DA)", "Total bénéfice (DA)"]

    try:
        for file in files:
            xls = pd.ExcelFile(file)

            # --- Extract month & year from filename ---
            filename = os.path.basename(file.name)  # VENTE_JANVIER_2026.xlsx
            name, _ = os.path.splitext(filename)

            match = re.search(r"_([A-ZÉÈÊÎÔÛ]+)_(\d{4})$", name)
            if not match:
                return {"success": False, "message": f"Fichier invalide: {filename}"}

            mois = match.group(1)
            year = int(match.group(2))

            # --- Read sheets ---
            for sheet in xls.sheet_names[1:]:
                df = pd.read_excel(
                    file,
                    sheet_name=sheet,
                    skiprows=14,
                    header=0,
                    usecols=cols,
                )
                df = (
                    df[df["Famille"].notna()]              # Drop totals
                    .rename(columns={"Quantité.1": "Quantité"})
                    .assign(
                        PREVENDEUR=sheet,
                        YEAR=year,
                        MOIS=mois,
                        MOIS_NUM=lambda x: x["MOIS"].map(mois_order),
                    )
                )
                dfs.append(df)
        final_df = pd.concat(dfs, ignore_index=True)
        final_df.sort_values(by=["YEAR", "MOIS_NUM", "MOIS"])
        return {"success": True, "df": final_df}
    except Exception as err:
        return {"success": False, "message": str(err)}


def build_totals_mois(df_mois: pd.DataFrame) -> pd.DataFrame:
    """
    Totaux par MOIS avec variation par rapport au mois précédent.
    """

    # --- Group & aggregate ---
    df_total = (
        df_mois
        .groupby(["YEAR", "MOIS_NUM", "MOIS"], as_index=False)
        .agg(
            livraison=("Total livraison (DA)", "sum"),
            benefice=("Total bénéfice (DA)", "sum"),
        )
        .sort_values(["YEAR", "MOIS_NUM"])
    )

    # --- Deltas (month over month) ---
    df_total["delta_livraison"] = df_total["livraison"].diff().fillna(0)
    df_total["delta_benefice"] = df_total["benefice"].diff().fillna(0)

    # --- Percentage deltas ---
    df_total["delta_livraison_pct"] = (
        df_total["livraison"].pct_change().mul(100).fillna(0)
    )
    df_total["delta_benefice_pct"] = (
        df_total["benefice"].pct_change().mul(100).fillna(0)
    )

    return df_total.reset_index(drop=True)


def build_totals_prevendeur_mois(df_mois: pd.DataFrame) -> pd.DataFrame:
    """
    Totaux par PREVENDEUR et par MOIS,
    avec variation (delta) par rapport au mois précédent.
    """

    # --- Group & aggregate ---
    df_total = (
        df_mois
        .groupby(["PREVENDEUR", "YEAR", "MOIS_NUM", "MOIS"], as_index=False)
        .agg(
            livraison=("Total livraison (DA)", "sum"),
            benefice=("Total bénéfice (DA)", "sum"),
        )
        .sort_values(["YEAR", "MOIS_NUM"])
    )

    # --- Deltas (month over month per PREVENDEUR) ---
    df_total["delta_livraison"] = (
        df_total
        .groupby("PREVENDEUR")["livraison"]
        .diff()
        .fillna(0)
    )

    df_total["delta_benefice"] = (
        df_total
        .groupby("PREVENDEUR")["benefice"]
        .diff()
        .fillna(0)
    )

    # --- Percentage deltas ---
    df_total["delta_livraison_pct"] = (
        df_total
        .groupby("PREVENDEUR")["livraison"]
        .pct_change()
        .mul(100)
        .fillna(0)
    )

    df_total["delta_benefice_pct"] = (
        df_total
        .groupby("PREVENDEUR")["benefice"]
        .pct_change()
        .mul(100)
        .fillna(0)
    )

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
