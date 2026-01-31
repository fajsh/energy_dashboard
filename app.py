import streamlit as st

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


st.set_page_config(
    page_title="Energy Dashboard 2025",
    layout="wide"
)

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
div[data-testid="stCheckbox"] label{
  padding: 0 !important;
  margin: 0 !important;
  min-height: 0 !important;
  line-height: 1.0 !important;
}
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

apply_compact_layout()
init_state()
render_header()

# Load data
df_monthly = load_monthly_sums()
df_cleaned = load_cleaned_dataset()

scale = st.session_state.get("plot_scale", 0.9)
prod_height = int(190 * scale)
time_height = int(200 * scale)
heat_height = prod_height
heat_container_height = int(138 * scale)
map_width = int(400 * scale)
map_height = int(220 * scale)
temp_height = int(390 * 0.80)
temp_plot_width = int(620 * 0.80)

# ─────────────────────────────────────────────
# TOP ROW
# ─────────────────────────────────────────────
with st.container(border=True):
    render_energy_kpis(df_cleaned)

# ─────────────────────────────────────────────
# BELOW KPI ROW
# ─────────────────────────────────────────────
kpi_left, kpi_right = st.columns([1.6, 1.2], gap="small")

with kpi_left:
    with st.container(border=True):
        st.markdown("##### Regional Analysis")
        plot_kantonskarte()

with kpi_right:
    with st.container(border=True):
        st.markdown("##### Temperature impact on energy consumption and river flow")

        tab_cons, tab_rhine = st.tabs(["National Consumption", "Rhine River Flow"])

        # Tab 1: Landesverbrauch vs Temperature
        with tab_cons:
            st.markdown(
                """
                <div style="text-align: center; font-size: 1rem; color: #6b6b6b; white-space:nowrap;">
                    Higher temperatures are associated with lower energy consumption.
                </div>
                """,
                unsafe_allow_html=True
            )
            # st.caption("Higher temperatures are associated with lower energy consumption.")
            # spacer to visually center the chart
            spacer, plot_col, ctrl_col = st.columns([0.12, 3.0, 1.1], gap="small")

            with ctrl_col:
                st.markdown("<div style='height: 8rem;'></div>", unsafe_allow_html=True)
                st.markdown("**Controls**")
                show_trend_cons = st.checkbox("Trendline", value=True, key="cons_trend")
                show_out_cons = st.checkbox("Outliers", value=False, key="cons_out")

            with plot_col:
                fig_cons = temp_scatter_single(
                    df_cleaned,
                    y_col="Landesverbrauch",
                    y_label="National Consumption (GWh)",
                    color_points=LANDESVERBRAUCH, # scatter dots
                    color_trend=LANDESVERBRAUCH, # trendline
                    color_outliers="#EBC79E", # outlier ring color
                    outlier="high",
                    height=temp_height,
                    width=temp_plot_width,
                    compact=True,
                )
                # trace order: 0 scatter dots, 1 trend, 2 outliers
                fig_cons.data[1].visible = show_trend_cons
                fig_cons.data[2].visible = show_out_cons

                st.markdown("<div style='height: 1.05rem;'></div>", unsafe_allow_html=True)
                # container width of plotly is turned off
                st.plotly_chart(fig_cons, use_container_width=False)

        # Tab 2: Rhine flow vs Temperature
        with tab_rhine:
            st.markdown(
                """
                <div style="text-align: center; font-size: 1rem; color: #6b6b6b; white-space:nowrap;">
                    Higher temperatures are associated with a slight increase in river flow.
                </div>
                """,
                unsafe_allow_html=True
            )
            # st.caption("Higher temperatures are associated with a slight increase in river flow.")
            spacer, plot_col, ctrl_col = st.columns([0.12, 3.0, 1.1], gap="small")

            with ctrl_col:
                st.markdown("<div style='height: 8rem;'></div>", unsafe_allow_html=True)
                st.markdown("**Controls**")
                show_trend_rhine = st.checkbox("Trendline", value=True, key="rhine_trend")
                show_out_rhine = st.checkbox("Outliers", value=False, key="rhine_out")

            with plot_col:
                fig_rhine = temp_scatter_single(
                    df_cleaned,
                    y_col="Wasserführung Rhein",
                    y_label="Rhine River Flow (m³/s)",
                    color_points=WASSERFUEHRUNG, # scatter dots
                    color_trend=WASSERFUEHRUNG, # trendline
                    color_outliers="#68875D", # outlier ring color
                    outlier="low",
                    height=temp_height,
                    width=temp_plot_width,
                    compact=True,
                )
                fig_rhine.data[1].visible = show_trend_rhine
                fig_rhine.data[2].visible = show_out_rhine

                st.markdown("<div style='height: 1.05rem;'></div>", unsafe_allow_html=True)
                st.plotly_chart(fig_rhine, use_container_width=False)

# ─────────────────────────────────────────────
# MIDDLE ROW
# ─────────────────────────────────────────────
mid_left, mid_right = st.columns([1.6, 1.7], gap="small")

with mid_left:
    with st.container(border=True):
        st.markdown("##### Production")

        selected_month = st.selectbox(
            "Choose month",
            options=["Total"] + sorted(df_monthly["Monat"].unique().tolist()),
            index=0,
            key="prod_month",
        )

        bar_col, donut_col = st.columns([1.4, 1])

        with bar_col:
            production_plots(
                df_monthly,
                height=prod_height,
                selected_month=selected_month,
                show_bar=True,
                show_donut=False,
            )

        with donut_col:
            production_plots(
                df_monthly,
                height=prod_height,
                selected_month=selected_month,
                show_bar=False,
                show_donut=True,
            )

with mid_right:
    with st.container(border=True):
        st.markdown("##### Import, Export and Consumption")
        st.markdown(
            f"<div class='heatmap-card' style='min-height:{heat_container_height}px;'>",
            unsafe_allow_html=True,
        )
        plot_heatmap_import_export(df_cleaned, height=heat_height)
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# BOTTOM ROW
# ─────────────────────────────────────────────
bottom_left, bottom_right = st.columns([3, 1.2], gap="small")

with bottom_left:
    with st.container(border=True):
        st.markdown("##### Time Series and Energy Flow Metrics")
        plot_time_series(df_cleaned, height=time_height)

with bottom_left:
    with st.container(border=False):
        st.markdown("")