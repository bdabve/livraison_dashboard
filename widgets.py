#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# author        : el3arbi bdabve@gmail.com
# created       :
# desc          :
# ----------------------------------------------------------------------------
import streamlit as st


def two_chart_columns(chart, chart_2):
    chartColumn, chart2Column = st.columns(2)
    chartColumn.plotly_chart(chart, width="stretch")
    chart2Column.plotly_chart(chart_2, width="stretch")


def table_fig_columns(df, chart):
    # Create two columns, One for table and one for figure
    table_column, fig_column = st.columns(2)
    with table_column:
        st.space("large")
        st.dataframe(
            df,
            hide_index=True,
            width="stretch"
        )
    fig_column.plotly_chart(chart, width="stretch")


def display_totals(totals):
    col1, col2 = st.columns(2)
    col1.metric(
        label="🚚 Total Livraison",
        value=f"{totals['livraison']:,.0f} DA",
        border=True
    )

    col2.metric(
        label="💰 Total Bénéfice",
        value=f"{totals['benefice']:,.0f} DA",
        border=True
    )


def display_prevendeur_totals(row):
    """
    Display Prevendeur totals in metric with 3 columns
    """
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Livraison", f"{row['livraison']:,.0f} DA", border=True)
    col2.metric("📈 Bénéfice", f"{row['benefice']:,.0f} DA", border=True)
    st.divider()
