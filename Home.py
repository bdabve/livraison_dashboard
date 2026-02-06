import streamlit as st

st.set_page_config(page_title="Livraison Dashboard", page_icon=":bar_chart:", layout="wide")
st.title(":bar_chart: _Livraison Dashboard_", text_alignment="center")
st.space()
# -------------------------------
# TODO:
# - The database that handle By MONTH This database work as statistics;
#   so the comercial and livreur doesnt take a big concederation on ID this for more depth database
#
# - Structure
# -----------
#   Month,
#   Vente,
#   Bénéfice, (TrizBenefice to work with ----)
#   Commande(Commercial),
#   Versement(Livreur),
#   Charges,
#   Accompte,
#   Crédit,
#   Versement Crédit,
#   Diff,
#   Total générale
#   --------------
# Accomptes, Crédits, Versement Crédit, Diff
