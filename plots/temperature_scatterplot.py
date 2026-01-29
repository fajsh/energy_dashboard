# importing libraries
import plotly.graph_objects as go
import pandas as pd
import numpy as np
# importing colour for the axes from utils/colors
from utils.colors import ACHSE

# Scatter plot
def temp_scatter_single(
    df: pd.DataFrame,
    y_col: str,
    y_label: str,
    color_points: str,
    color_trend: str | None = None,
    color_outliers: str | None = None,
    outlier: str = "high",
    width=None,
    height=390,
    compact=True,
) -> go.Figure:
    x = df["Mittlere Tagestemperatur"]
    y = df[y_col]

    # colour conditions
    if color_trend is None:
        color_trend = color_points
    if color_outliers is None:
        color_outliers = color_points

    # Outliers
    if outlier == "high":
        outlier_mask = y > y.quantile(0.95)
    else:
        outlier_mask = y < y.quantile(0.05)

    # Trend line
    coef = np.polyfit(x, y, 1)
    x_trend = np.linspace(x.min(), x.max(), 50)
    y_trend = np.polyval(coef, x_trend)

    fig = go.Figure()

    # Scatter dots (trace 0)
    fig.add_trace(
        go.Scatter(
            x=x[~outlier_mask],
            y=y[~outlier_mask],
            mode="markers",
            name=y_label,
            marker=dict(
                color=color_points,
                size=9,
                line=dict(width=1, color="white"),
            ),
            hovertemplate=(
                "Temp: %{x:.1f} °C<br>"
                + f"{y_label}: %{{y:.0f}}"
                + "<extra></extra>"
            ),
            opacity=1.0,
        )
    )

    # Trendline (trace 1)
    fig.add_trace(
        go.Scatter(
            x=x_trend,
            y=y_trend,
            mode="lines",
            name="Trend",
            line=dict(color=color_trend, width=2),
        )
    )

    # Outliers (trace 2)
    fig.add_trace(
        go.Scatter(
            x=x[outlier_mask],
            y=y[outlier_mask],
            mode="markers",
            name="Outliers",
            marker=dict(
                symbol="circle-open",
                size=12,
                color=color_outliers,
                line=dict(width=2, color=color_outliers),
            ),
            opacity=1.0,
        )
    )

    # X axis
    fig.update_xaxes(
        title_text="Average Daily Temperatures (°C) - Basel/Bern/Lausanne/Zurich",
        zeroline=False,
        showgrid=False,
        linecolor=ACHSE,
        linewidth=2,
        title_font=dict(size=12, color=ACHSE),
        tickfont=dict(color=ACHSE),
    )

    # Y axis
    fig.update_yaxes(
        title_text=y_label,
        showgrid=False,
        linecolor=ACHSE,
        linewidth=2,
        title_font=dict(size=11, color=ACHSE),
        tickfont=dict(color=ACHSE),
    )

    # Layout
    fig.update_layout(
        template="simple_white",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        autosize=False,
        showlegend=False,
        height=height,
        width=width,
        margin=dict(l=55, r=15, t=10, b=30) if compact else dict(l=90, r=25, t=40, b=45),
    )

    return fig