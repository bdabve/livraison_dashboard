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
