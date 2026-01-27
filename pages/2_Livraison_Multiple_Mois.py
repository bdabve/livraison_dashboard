import streamlit as st
import pandas as pd
import utils


@st.cache_data
def load_date_from_excel(excel_file, selected_months):
    dfs = []
    for month in selected_months:
        data = utils.clean_dataframe(pd.read_excel(excel_file, sheet_name=month, usecols="A:H"))
        if data["success"]:
            df = data["df"]
            df["MOIS"] = month
            # --- Month order (French) ---
            mois_order = {
                "JANVIER": 1, "FEVRIER": 2, "MARS": 3, "AVRIL": 4,
                "MAI": 5, "JUIN": 6, "JUILLET": 7, "AOÛT": 8,
                "SEPTEMBRE": 9, "OCTOBRE": 10, "NOVEMBRE": 11, "DECEMBRE": 12,
            }
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


# Page configuration
st.set_page_config(page_title="Livraison Dashboard", page_icon=":bar_chart:", layout="wide")
st.title(":bar_chart: _Livraison Dashboard Multiple Mois_", text_alignment="center")
st.space()

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
    months = f.sheet_names
    selected_months = st.multiselect("Select months", months, default=months)


data = load_date_from_excel(excel_file, selected_months)
if not data["success"]:
    st.warning(data["message"])
    st.stop()
else:
    dfs = data["data"]

st.divider()
# ----------------------------------------------------------------------------
# ------- ETAT GLOBAL -------
fields = ["MOIS", "MOIS_NUM", "DATE", "LIVREUR", "T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE"]
st.subheader("📊 État Global des Livraisons")
st.space()
st.dataframe(dfs[fields], width="stretch", hide_index=True)
st.space()
# ----------------------------------------------------------------------------
# --- Filter Month ---
#
months = dfs.sort_values("MOIS")["MOIS"].unique()
selected_month = st.sidebar.selectbox(
    "📅 Choisir le mois",
    months,
    index=len(months) - 1  # default = latest month
)
st.sidebar.header(f"**{selected_month}**", text_alignment="center")
st.sidebar.divider()
# ----------------------------------------------------------------------------
# --- Etat par MOIS ---
df_total_par_mois = (
    dfs
    .groupby(["MOIS_NUM", "MOIS"], as_index=False)
    .agg(
        versement=("VERSEMENT", "sum"),
        commandes=("T. COMMANDE", "sum"),
        charges=("CHARGE", "sum")
    )
    .sort_values("MOIS_NUM")
)
# --- Calculate Deltas ---
df_total_par_mois["delta_versement"] = df_total_par_mois["versement"].diff()
df_total_par_mois["delta_commandes"] = df_total_par_mois["commandes"].diff()
df_total_par_mois["delta_charges"] = df_total_par_mois["charges"].diff()

# Pourcentage
df_total_par_mois["delta_versement_pct"] = df_total_par_mois["versement"].pct_change() * 100
df_total_par_mois["delta_commandes_pct"] = df_total_par_mois["commandes"].pct_change() * 100
df_total_par_mois["delta_charges_pct"] = df_total_par_mois["charges"].pct_change() * 100

# --- Grand Total ---
df_grand_total = pd.DataFrame({
    "versement": [df_total_par_mois["versement"].sum()],
    "commandes": [df_total_par_mois["commandes"].sum()],
    "charges": [df_total_par_mois["charges"].sum()]
})

# ----------------
st.space()
st.subheader("📊 Totaux mensuels _VERSEMENT_ & _COMMANDES_", divider="grey", width="content")

# -- Display Grande Total --
for _, row in df_grand_total.iterrows():
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Versement", f"{row['versement']:,.0f} DA", border=True)
    col2.metric("📋 Commandes", f"{row['commandes']:,.0f} DA", border=True)
    col3.metric("💸 Charges", f"{row['charges']:,.0f} DA", border=True)
    st.divider()

# -- Display Total par MOIS --
for _, row in df_total_par_mois.iterrows():
    st.markdown(f"##### 📆 {row['MOIS']}")
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "💰 Versement",
        f"{row['versement']:,.0f} DA",
        # delta=f"{row['delta_versement']:,.0f} DA" if not pd.isna(row["delta_versement"]) else None,
        delta=f"{row['delta_versement_pct']:.1f}%" if not pd.isna(row["delta_versement_pct"]) else None,
        border=True,
    )
    #
    col2.metric(
        "📋 Commandes",
        f"{row['commandes']:,.0f} DA",
        # delta=f"{row['delta_commandes']:,.0f} DA" if not pd.isna(row["delta_commandes"]) else None,
        delta=f"{row['delta_commandes_pct']:.1f}%" if not pd.isna(row["delta_commandes_pct"]) else None,
        border=True,
    )
    #
    col3.metric(
        "💸 Charges",
        f"{row['charges']:,.0f} DA",
        # delta=f"{row['delta_charges']:,.0f} DA" if not pd.isna(row["delta_charges"]) else None,
        delta=f"{row['delta_charges_pct']:.1f}%" if not pd.isna(row["delta_charges_pct"]) else None,
        border=True,
    )
    st.divider()
