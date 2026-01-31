import streamlit as st

# PAGE CONFIG
st.set_page_config(
    page_title="Energy Dashboard 2025",
    layout="wide"
)

from data.load_data import load_monthly_sums, load_cleaned_dataset
from layout.header import render_header
from layout.layout_utils import apply_compact_layout
from plots.kpi import plot_kpis
from plots.timeseries import plot_time_series
from plots.heatmap import plot_heatmap_import_export
from plots.production import production_plots
from plots.temperature_scatterplot import temp_scatter_single
from plots.geography import plot_kantonskarte
from state.session_state import init_state
from plots.kpi_with_icons import render_energy_kpis
from utils.colors import LANDESVERBRAUCH, WASSERFUEHRUNG

# BACKGROUND COLORS
css = """
.st-key-container1{
    background: #FFFFFF;
}
.st-key-container2{
    background: #FFFFFF;
}
.st-key-container3{
    background: #FFFFFF;
}
.st-key-container4{
    background: #FFFFFF;
}
.st-key-container5{
    background: #FFFFFF;
}
.st-key-container6{
    background: #FFFFFF;
}
"""
st.html(f"<style>{css}</style>")

# GLOBAL STYLES
st.markdown(
    """
<style>
/* Remove top white space */
.block-container {
    padding-top: 0.5rem !important;
}

/* Compact checkboxes */
div[data-testid="stCheckbox"]{
  transform: scale(0.92);
  transform-origin: left center;
  margin: 0 !important;
  padding: 0 !important;
}

/* Remove built-in padding/min-height that creates tall rows */
div[data-testid="stCheckbox"] label{
  padding: 0 !important;
  margin: 0 !important;
  min-height: 0 !important;
  line-height: 1.0 !important;
}
/* If Streamlit adds vertical spacing between elements in a block */
div[data-testid="stVerticalBlock"]{
  gap: 0.35rem !important;
}

/* Tabs: active label + underline */
div[data-testid="stTabs"] button[aria-selected="true"]{
  color: #C24B45 !important;
  font-weight: 700 !important;
}
div[data-testid="stTabs"] button[aria-selected="true"]::after{
  background-color: #C24B45 !important;
}

/* Tabs: inactive */
div[data-testid="stTabs"] button[aria-selected="false"]{
  color: #2E2E2E !important;
}

/* Checkbox: checked color (browser-supported) */
div[data-testid="stCheckbox"] input[type="checkbox"]{
  accent-color: #C24B45 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# INITIALIZE APP
apply_compact_layout()
init_state()
render_header()

# LOAD DATA
df_monthly = load_monthly_sums()
df_cleaned = load_cleaned_dataset()

scale = st.session_state.get("plot_scale", 0.9)
prod_height = int(190 * scale)
time_height = int(200 * scale)
heat_height = prod_height
heat_container_height = int(138 * scale)
map_width = int(400 * scale)
map_height = int(220 * scale)
temp_height = int(390 * scale)
temp_plot_width = int(620 * scale)

# KPI ROW
with st.container(key="container1", border=True):
    render_energy_kpis(df_cleaned)

# REST ROW
col1, col2 = st.columns([1.6, 1.2], gap="small")

# COLUMN LEFT
with col1:
    # Regional Analysis
    with st.container(key="container2", border=True):
        st.markdown("##### Regional Analysis")
        plot_kantonskarte()

    # Temperature Scatter Plots
    with st.container(key="container3", border=True):
        st.markdown("##### Temperature impact on energy consumption and river flow")

        tab_cons, tab_rhine = st.tabs(["National Consumption", "Rhine River Flow"])

        # Tab 1: Landesverbrauch vs Temperature
        with tab_cons:
            st.markdown(
                """
                <div style="text-align: center; font-size: 1.15rem; color: #6b6b6b; white-space:nowrap;">
                    Higher temperatures are associated with lower energy consumption.
                </div>
                """,
                unsafe_allow_html=True
            )
            spacer, plot_col, ctrl_col = st.columns([0.19, 3.0, 1.1], gap="small")

            # Controls column
            with ctrl_col:
                st.markdown("<div style='height: 8rem;'></div>", unsafe_allow_html=True)
                st.markdown("**Controls**")
                show_trend_cons = st.checkbox("Trendline", value=True, key="cons_trend")
                show_out_cons = st.checkbox("Outliers", value=False, key="cons_out")

            # Plot column
            with plot_col:
                fig_cons = temp_scatter_single(
                    df_cleaned,
                    y_col="Landesverbrauch",
                    y_label="National Consumption (GWh)",
                    color_points=LANDESVERBRAUCH,
                    color_trend=LANDESVERBRAUCH,
                    color_outliers="#EBC79E",
                    outlier="high",
                    height=temp_height,
                    width=temp_plot_width,
                    compact=True,
                )
                fig_cons.data[1].visible = show_trend_cons
                fig_cons.data[2].visible = show_out_cons

                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
                st.plotly_chart(fig_cons, use_container_width=False)

        # Tab 2: Rhine flow vs Temperature
        with tab_rhine:
            st.markdown(
                """
                <div style="text-align: center; font-size: 1.15rem; color: #6b6b6b; white-space:nowrap;">
                    Higher temperatures are associated with a slight increase in river flow.
                </div>
                """,
                unsafe_allow_html=True
            )
            spacer, plot_col, ctrl_col = st.columns([0.12, 3.0, 1.1], gap="small")

            # Controls column
            with ctrl_col:
                st.markdown("<div style='height: 8rem;'></div>", unsafe_allow_html=True)
                st.markdown("**Controls**")
                show_trend_rhine = st.checkbox("Trendline", value=True, key="rhine_trend")
                show_out_rhine = st.checkbox("Outliers", value=False, key="rhine_out")

            # Plot column
            with plot_col:
                fig_rhine = temp_scatter_single(
                    df_cleaned,
                    y_col="Wasserführung Rhein",
                    y_label="Rhine River Flow (m³/s)",
                    color_points=WASSERFUEHRUNG,
                    color_trend=WASSERFUEHRUNG,
                    color_outliers="#68875D",
                    outlier="low",
                    height=temp_height,
                    width=temp_plot_width,
                    compact=True,
                )
                fig_rhine.data[1].visible = show_trend_rhine
                fig_rhine.data[2].visible = show_out_rhine

                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
                st.plotly_chart(fig_rhine, use_container_width=False)

# COLUMN RIGHT
with col2:
    # Production
    with st.container(key="container4", border=True):
        st.markdown("##### Production")
        selected_month = st.selectbox(
            "Month",
            label_visibility='collapsed',
            options=["Total"] + sorted(df_monthly["Monat"].unique().tolist()),
            index=0,
            key="prod_month",
        )

        production_plots(
            df_monthly,
            height=prod_height,
            selected_month=selected_month,
            show_bar=True,
            show_donut=False,
        )
        production_plots(
            df_monthly,
            height=prod_height,
            selected_month=selected_month,
            show_bar=False,
            show_donut=True,
        )

    # Import, Export and Consumption
    with st.container(key="container5", border=True):
        st.markdown("##### Import, Export and Consumption")
        plot_heatmap_import_export(df_cleaned, height=heat_height)
        st.markdown("</div>", unsafe_allow_html=True)

    # Time Series
    with st.container(key="container6", border=True):
        st.markdown("##### Time Series and Energy Flow Metrics")
        plot_time_series(df_cleaned, height=time_height)
