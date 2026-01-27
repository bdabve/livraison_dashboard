#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# author        : el3arbi bdabve@gmail.com
# created       :
# desc          :
# ----------------------------------------------------------------------------
import streamlit as st


def two_chart_columns(root, chart, chart_2):
    chartColumn, chart2Column = root.columns(2)
    chartColumn.plotly_chart(chart, width="stretch")
    chart2Column.plotly_chart(chart_2, width="stretch")


def table_chart_column(root, df, chart):
    # Create two columns, One for table and one for figure
    table_column, chart_column = root.columns(2)
    with table_column:
        st.space("medium")
        st.dataframe(df, hide_index=True)
    chart_column.plotly_chart(chart, width="stretch")


def display_totals(root, totals):
    """
    Display Total in metrics in 2 columns
    :totals: row in; for _, row in df.iterrows
    """
    col1, col2 = root.columns(2)
    col1.metric("💰 Livraison", f"{totals['livraison']:,.0f} DA", border=True)
    col2.metric("📈 Bénéfice", f"{totals['benefice']:,.0f} DA", border=True)
    root.divider()


def display_prevendeur_totals(root, row):
    """
    Display Prevendeur totals in metric with 3 columns
    """
    col1, col2 = root.columns(2)
    col1.metric(
        "💰 Livraison", f"{row['livraison']:,.0f} DA",
        delta=f"{row['livraison_prev']:,.0f} DA",
        # delta=f"{row['delta_livraison_pct']:.1f}%" if not row['delta_livraison_pct'] is None else None,
        border=True
    )
    col2.metric(
        "📈 Bénéfice", f"{row['benefice']:,.0f} DA",
        delta=f"{row['benefice_prev']:,.0f} DA",
        border=True
    )
    root.divider()
