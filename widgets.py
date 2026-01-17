#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# author        : el3arbi bdabve@gmail.com
# created       :
# desc          :
# ----------------------------------------------------------------------------
import streamlit as st


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
