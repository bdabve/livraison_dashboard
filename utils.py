#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# author        : el3arbi bdabve@gmail.com
# created       :
# desc          :
# ----------------------------------------------------------------------------
import pandas as pd


def clean_dataframe(df):
    try:
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
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
    charges = clean_df.groupby(["DATE"])[["CHARGE"]].sum()
    charges = charges["CHARGE"].sum()

    # --- Sum VERSEMENT by LIVREUR ---
    vers_by_livreur = clean_df.groupby("LIVREUR", as_index=False)["VERSEMENT"].sum()
    livreur = vers_by_livreur[vers_by_livreur["LIVREUR"].isin(["ACCOMPTE", "CREDIT", "VERS. CREDIT"])]
    livreur = livreur.set_index("LIVREUR")
    # Extract values safely
    etat_excel = {
        "ACCOMPTE": float(livreur["VERSEMENT"].get("ACCOMPTE", 0)),
        "CREDIT": float(livreur["VERSEMENT"].get("CREDIT", 0)),
        "VERS. CREDIT": float(livreur["VERSEMENT"].get("VERS. CREDIT", 0)),
        "CHARGES": float(charges),
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
    driver_stats = driver_stats.sort_values(by="VERSEMENT", ascending=False)
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

    sum_retour_by_driver = (
        retour.groupby("LIVREUR")["RETOUR"]
        .sum()
        .reset_index()
    )

    return retour, sum_retour_by_driver


def show_day_details(clean_df, day, fields):
    """
    Show details for a specific day
    :clean_df: DataFrame
    :day: str or datetime [YYYY-MM-DD]
    :fields: list of fields to sum
    """
    daily_details = clean_df.groupby(["DATE", "LIVREUR"])[fields].sum()
    # daily_details = daily_details.sort_values(by="T.LOGICIEL", ascending=False)

    # daily_details["OBSERVATION"] = daily_details["OBSERVATION"].astype("string")
    # Convert input to datetime
    day = pd.to_datetime(day).normalize()

    if day in daily_details.index.get_level_values("DATE"):
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
