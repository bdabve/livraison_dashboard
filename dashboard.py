#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# author        : el3arbi bdabve@gmail.com
# created       :
# desc          :
# ----------------------------------------------------------------------------

import pandas as pd
# import plotly.express as px
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

    # Remove rows without a valid DATE (e.g. subtotal / footer rows)
    clean_df = df[df["DATE"].notna()]
    clean_df = clean_df.fillna(0)
    return clean_df


df = load_data_from_excel()

# --- Side Bar
st.sidebar.header('Filter Here:')

livreur = st.sidebar.multiselect(
    'Select the Livreur:',
    options=df['LIVREUR'].unique(),
    default=df['LIVREUR'].unique()
)

# customer_type = st.sidebar.multiselect(
    # 'Select the Customer Type:',
    # options=df['Customer_type'].unique(),
    # default=df['Customer_type'].unique()
# )

# gender_info = st.sidebar.multiselect(
    # 'Select the Gender:',
    # options=df['Gender'].unique(),
    # default=df['Gender'].unique()
# )

df_selection = df.query('LIVREUR == @livreur')

# TOP
import utils
etat_excel = utils.etat_excel_like_db(df_selection)

accompte_column, credit_column, versement_column, charge_column = st.columns(4)

with accompte_column:
    st.subheader('ACCOMPTE:')
    st.subheader(f" $ {etat_excel['ACCOMPTE']:,}")

with credit_column:
    st.subheader('CREDIT:')
    st.subheader(f'$ {etat_excel["CREDIT"]:,}')

with versement_column:
    st.subheader('VERS. CREDIT:')
    st.subheader(f'$ {etat_excel["VERS. CREDIT"]:,}')

with charge_column:
    st.subheader('CHARGES:')
    st.subheader(f'$ {etat_excel["CHARGES"]:,}')

st.markdown('---')

# Display the daily report
fields = ["T. COMMANDE", "T.LOGICIEL", "VERSEMENT", "CHARGE", "DIFF"]
etat_journalier = utils.etat_journalier(df, fields)
print(etat_journalier)
st.subheader("Etat Journalier")
st.dataframe(etat_journalier, column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")})

st.markdown('---')

# Display the dataframe
st.dataframe(df, column_config={"DATE": st.column_config.DateColumn("DATE", format="DD-MM-YYYY")})

# Display the plot
# sales_by_product_line = (df_selection.groupby(by=['Product line']).sum(numeric_only=True)[['Total']].sort_values(by="Total"))

# fig_product_sales = px.bar(
    # sales_by_product_line,
    # x='Total',
    # y=sales_by_product_line.index,
    # orientation='h',
    # title='<b>Sales By Product Line.</b>',
    # color_discrete_sequence=['#0083B8'] * len(sales_by_product_line),
    # template='plotly_white',
# )
# remove bg color for plot
# fig_product_sales.update_layout(
    # plot_bgcolor='rgba(0,0,0,0)',
    # xaxis=(dict(showgrid=False))
# )

# Sales by hour
# sales_by_hour = df_selection.groupby(by=['hour']).sum(numeric_only=True)[['Total']]

# fig_hourly_sales = px.bar(
    # sales_by_hour,
    # x=sales_by_hour.index,
    # y='Total',
    # title='<b>Sales By Hour.</b>',
    # color_discrete_sequence=['#0083B8'] * len(sales_by_product_line),
    # template='plotly_white',
# )

# fig_hourly_sales.update_layout(
    # xaxis=dict(tickmode='linear'),
    # plot_bgcolor='rgba(0,0,0,0)',
    # yaxis=(dict(showgrid=False))
# )

# Display the charts in 2 columns
# left_column, right_column = st.columns(2)
# left_column.plotly_chart(fig_hourly_sales, use_container_width=True)
# right_column.plotly_chart(fig_product_sales, use_container_width=True)

# hide some stylesheet
hide_st_style = '''
<style>
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
</style>
'''
st.markdown(hide_st_style, unsafe_allow_html=True)
