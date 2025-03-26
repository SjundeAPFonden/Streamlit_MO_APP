import streamlit as st
import plotly.express as px
import pandas as pd
import pickle
from snowflake.snowpark.context import get_active_session

filter_date = "VALUATION_DATE_FULL"


#----------början på sliderfunktion------------------------
def date_slider(df, date_column, label="Select Date Range", key="date_slider"):
    """
    Creates a Streamlit date slider for selecting a date range.

    :param df: DataFrame containing a date column.
    :param date_column: The name of the date column to filter on.
    :param label: Label for the sidebar header.
    :param key: Unique Streamlit key for the slider.
    :return: Tuple containing (start_date, end_date).
    """
    st.sidebar.header(label)

    # Ensure the column exists
    if date_column not in df.columns:
        st.error(f"Column '{date_column}' not found in DataFrame.")
        st.stop()

    # Ensure the column is in datetime format
    df[date_column] = pd.to_datetime(df[date_column])

    # Create the slider
    start_date, end_date = st.sidebar.slider(
        f"Choose Start and End Date for {date_column}",
        min_value=df[date_column].min().date(),
        max_value=df[date_column].max().date(),
        value=(df[date_column].min().date(), df[date_column].max().date()),
        format="YYYY-MM-DD",
        key=key
    )
    return start_date, end_date, date_column
#---------Slut på slider funktion-------------------

#----------Start multiselectfunktion----------------------

# Funktion för Multi-Select dvs filter
def multi_select_sidebar(df, column, label, key):
    """
    Creates a Streamlit multiselect widget for selecting unique values from a specified column.

    :param df: DataFrame containing the data.
    :param column: Column name to filter on.
    :param label: Sidebar header label.
    :param key: Unique Streamlit key to avoid widget conflicts.
    :return: List of selected values.
    """
    st.sidebar.header(label)

    # Extract unique values from the column
    available_options = df[column].unique().tolist()

    # Multi-select widget
    selected_options = st.sidebar.multiselect(
        f"Choose {label}",
        options=available_options,
        default=available_options,  # Default to selecting ALL options
        key=key
    )

    return column, label, selected_options
#----------Slut multiselectfunktion----------------------

#---------Start groupby function för df_filtered till alla grafer-------------
def groupby_dataframe(df, group_cols, y_col, agg_func="sum"):
    """
    Groups and aggregates a DataFrame dynamically.

    :param df: DataFrame to process.
    :param group_cols: List of column names to group by (e.g., ["VALUATION_DATE_FULL", "MODEL_PORTFOLIO_NAME"]).
    :param y_col: Column name to aggregate (e.g., "MV").
    :param agg_func: Aggregation function (default: "sum").
    :return: Aggregated DataFrame and list of grouping columns.
    """
    return y_col, df.groupby(group_cols, as_index=False).agg({y_col: agg_func}), group_cols #första delen säger vad man ska guppera på (alltid datum) + i anropet definierade kolumner
#---------Slut groupby function för df_filtered till alla grafer-------------

#----------------start funktion för linjegraf----------------------
def func_plot_line_chart(df, x_col, y_col, group_col, title):
    """
    Creates and displays a line chart using Plotly with dynamic labels and grouping.

    :param df: The DataFrame containing the data.
    :param x_col: The column to use for the x-axis (e.g., date column).
    :param y_col: The column to use for the y-axis (e.g., "MV").
    :param group_col: The column to group by (e.g., Portfolio, Security Type, etc.).
    :param title: The title of the chart.
    """

    #  Create the Plotly figure
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        color=group_col,  #  Only one group column now
        line_group=group_col,  #  Ensure correct line separation
        title=title,  #  Title is now dynamic from function call
        labels={x_col: x_col, y_col: y_col, group_col: group_col},  #  Dynamic labels
        render_mode="svg"
    )

    #  Improve visibility with markers
    fig.update_traces(mode="lines+markers")

    #  Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True) #inom () gör grafen bredare
#----------------slut funktion för linjegraf----------------------
#-----------------start bar-chart-----------------------------
def func_plot_bar_chart(df, x_col, y_col, group_col, end_date, title):
    """
    Creates and displays a stacked bar chart with total value shown only on the last date.

    :param df: The DataFrame containing the data.
    :param x_col: The column to use for the x-axis (e.g., date column).
    :param y_col: The column to use for the y-axis (e.g., "MV").
    :param group_col: The column to group bars by (e.g., Portfolio, Security Type, etc.).
    :param end_date: The latest selected date for which the total MV should be displayed.
    :param title: The title of the chart.
    """

    #  Create a stacked bar chart
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=group_col,
        title=title,
        labels={x_col: "Date", y_col: "Market Value", group_col: group_col},
        barmode="stack",  #  Stack bars on top of each other
        text=df[y_col].astype(str)  #  Converts MV values to text for display
    )

    #  Filter the dataset for the latest selected `end_date`
    latest_df = df[df[x_col] == pd.Timestamp(end_date)]

    #  Calculate the total MV only for `end_date`
    total_mv = latest_df[y_col].sum()

        #  Add annotation with total MV on top of the last stacked bar
    fig.add_annotation(
            x=end_date,  #  X-axis: latest date
            y=total_mv,  #  Y-axis: total MV for latest date
            text=f"Total: {total_mv:,.0f}",  #  Format total MV
            showarrow=False,
            font=dict(size=14, color="black", family="Arial"),
            yshift=10  #  Move label slightly above the bar
        )

    #  Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

#-----------------slut bar-chart-----------------------------