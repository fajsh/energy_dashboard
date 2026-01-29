import calendar

import altair as alt
import pandas as pd
import streamlit as st
from matplotlib import cm, colors


def build_heatmap_import_export_fig(df_cleaned, height=320):
    df = df_cleaned.copy()
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    df = df.dropna(subset=["Datum"])

    monthly = (
        df.groupby(df["Datum"].dt.month)[["Einfuhr", "Ausfuhr"]]
        .sum()
        .reset_index()
        .rename(columns={"Datum": "Monat"})
    )

    month_labels = [calendar.month_abbr[i] for i in range(1, 13)]
    monthly = monthly.set_index("Monat")
    monthly = monthly.reindex(range(1, 13)).fillna(0)

    data = monthly.rename(
        columns={
            "Einfuhr": "Import",
            "Ausfuhr": "Export",
        }
    ).T
    data.columns = month_labels

    # Remove empty months to avoid large blank areas
    nonzero_months = data.abs().sum(axis=0) > 0
    if nonzero_months.any():
        data = data.loc[:, nonzero_months]
        month_labels = [m for m, keep in zip(month_labels, nonzero_months) if keep]

    df_long = (
        data.reset_index()
        .melt(id_vars="index", var_name="Month", value_name="GWh")
        .rename(columns={"index": "Category"})
    )

    def _linspace(start, end, n):
        if n <= 1:
            return [start]
        step = (end - start) / (n - 1)
        return [start + step * i for i in range(n)]

    coolwarm = cm.get_cmap("coolwarm")
    n_colors = 11
    blue_vals = _linspace(0.0, 0.45, n_colors)
    red_vals = _linspace(0.55, 1.0, n_colors)
    blue_palette = [colors.to_hex(coolwarm(v)) for v in blue_vals]
    red_palette = [colors.to_hex(coolwarm(v)) for v in red_vals]

    def _color_for_row(row):
        category = row["Category"]
        value = row["GWh"]
        palette = blue_palette if category == "Export" else red_palette
        values = df_long.loc[df_long["Category"] == category, "GWh"]
        vmin, vmax = values.min(), values.max()
        if vmax == vmin:
            return palette[-1]
        idx = int(round((value - vmin) / (vmax - vmin) * (len(palette) - 1)))
        return palette[max(0, min(idx, len(palette) - 1))]

    df_long["Color"] = df_long.apply(_color_for_row, axis=1)

    categories = df_long["Category"].unique().tolist()
    months = df_long["Month"].unique().tolist()
    max_rows = max(len(categories), 1)
    max_cols = max(len(months), 1)
    cell_size = max(12, int(height / max_rows))

    base = alt.Chart(df_long).mark_rect(cornerRadius=2).encode(
        x=alt.X("Month:O", title="Month", sort=month_labels),
        y=alt.Y("Category:O", title="Category", sort=categories),
        color=alt.Color("Color:N", scale=None, legend=None),
        tooltip=["Category", "Month", "GWh"],
    )

    text = alt.Chart(df_long).mark_text(fontSize=11, color="#000000").encode(
        x=alt.X("Month:O", sort=month_labels),
        y=alt.Y("Category:O", sort=categories),
        text=alt.Text("GWh:Q", format=".0f"),
    )

    return (
        alt.layer(base, text)
        .properties(
            width=cell_size * max_cols,
            height=cell_size * max_rows,
        )
        .configure_view(strokeWidth=0, fill="transparent")
        .configure(background="transparent")
        .configure_axis(labelColor="#000000", titleColor="#000000", labelPadding=4, titlePadding=6)
    )


def plot_heatmap_import_export(df_cleaned, height=320):
    chart = build_heatmap_import_export_fig(df_cleaned, height=height)
    st.altair_chart(chart, use_container_width=True)
