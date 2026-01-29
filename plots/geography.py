import calendar
import json
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from branca.colormap import LinearColormap
from folium.features import GeoJsonTooltip
from jinja2 import Template
from streamlit_folium import st_folium

_COLORMAP_TEMPLATE_BOTTOMLEFT = Template(
    """
    {% macro script(this, kwargs) %}
        var {{this.get_name()}} = {};

        {%if this.color_range %}
        {{this.get_name()}}.color = d3.scale.threshold()
                  .domain({{this.color_domain}})
                  .range({{this.color_range}});
        {%else%}
        {{this.get_name()}}.color = d3.scale.threshold()
                  .domain([{{ this.color_domain[0] }}, {{ this.color_domain[-1] }}])
                  .range(['{{ this.fill_color }}', '{{ this.fill_color }}']);
        {%endif%}

        {{this.get_name()}}.x = d3.scale.linear()
                  .domain([{{ this.color_domain[0] }}, {{ this.color_domain[-1] }}])
                  .range([0, {{ this.width }} - 50]);

        {{this.get_name()}}.legend = L.control({position: 'bottomleft'});
        {{this.get_name()}}.legend.onAdd = function (map) {var div = L.DomUtil.create('div', 'legend'); return div};
        {{this.get_name()}}.legend.addTo({{this._parent.get_name()}});

        {{this.get_name()}}.xAxis = d3.svg.axis()
            .scale({{this.get_name()}}.x)
            .orient("top")
            .tickSize(1)
            .tickValues([{{ this.color_domain[0] }}, {{ this.color_domain[-1] }}]);

        {{this.get_name()}}.svg = d3.select(".legend.leaflet-control").append("svg")
            .attr("id", 'legend')
            .attr("width", {{ this.width }})
            .attr("height", {{ this.height }});

        {{this.get_name()}}.g = {{this.get_name()}}.svg.append("g")
            .attr("class", "key")
            .attr("fill", {{ this.text_color | tojson }})
            .attr("transform", "translate(25,16)");

        {{this.get_name()}}.g.selectAll("rect")
            .data({{this.get_name()}}.color.range().map(function(d, i) {
              return {
                x0: i ? {{this.get_name()}}.x({{this.get_name()}}.color.domain()[i - 1]) : {{this.get_name()}}.x.range()[0],
                x1: i < {{this.get_name()}}.color.domain().length ? {{this.get_name()}}.x({{this.get_name()}}.color.domain()[i]) : {{this.get_name()}}.x.range()[1],
                z: d
              };
            }))
          .enter().append("rect")
            .attr("height", {{ this.height }} - 30)
            .attr("x", function(d) { return d.x0; })
            .attr("width", function(d) { return d.x1 - d.x0; })
            .style("fill", function(d) { return d.z; });

        {{this.get_name()}}.g.call({{this.get_name()}}.xAxis).append("text")
            .attr("class", "caption")
            .attr("y", 21)
            .attr("fill", {{ this.text_color | tojson }})
            .text({{ this.caption|tojson }});
    {% endmacro %}
    """
)


@st.cache_data
def _load_timeseries(path, sheet_name):
    return pd.read_excel(path, sheet_name=sheet_name, skiprows=[1])


def _extract_canton_codes(column_name, metric):
    if "\n" in column_name:
        column_name = column_name.split("\n", 1)[0].strip()

    singular = f"{metric} Kanton "
    plural = f"{metric} Kantone "

    if column_name.startswith(singular):
        return [column_name.replace(singular, "").strip()]
    if column_name.startswith(plural):
        tail = column_name.replace(plural, "").strip()
        return [code.strip() for code in tail.split(",") if code.strip()]
    return []


def _build_canton_totals(df, metric, split_mode):
    totals = {}

    candidate_cols = [
        col for col in df.columns
        if isinstance(col, str) and col.startswith(f"{metric} Kanton")
    ]
    candidate_cols += [
        col for col in df.columns
        if isinstance(col, str) and col.startswith(f"{metric} Kantone")
    ]

    for col in candidate_cols:
        codes = _extract_canton_codes(col, metric)
        if not codes:
            continue

        value = pd.to_numeric(df[col], errors="coerce").sum()
        if split_mode == "equal" and len(codes) > 1:
            value = value / len(codes)

        for code in codes:
            totals[code] = totals.get(code, 0) + value

    return pd.DataFrame({"Kanton": sorted(totals), "Wert": [totals[k] for k in sorted(totals)]})


def _guess_feature_key(geojson_obj):
    feature = geojson_obj.get("features", [{}])[0]
    props = feature.get("properties", {})
    for key in ("NAME", "name", "KANTON", "kanton", "abbr", "code", "id"):
        if key in props:
            return f"properties.{key}"
    if "id" in feature:
        return "id"
    return None


def _map_codes_to_names(df):
    code_to_name = {
        "AG": "Aargau",
        "AI": "Appenzell Innerrhoden",
        "AR": "Appenzell Ausserrhoden",
        "BE": "Bern",
        "BL": "Basel-Landschaft",
        "BS": "Basel-Stadt",
        "FR": "Fribourg",
        "GE": "Gen\u00e8ve",
        "GL": "Glarus",
        "GR": "Graub\u00fcnden",
        "JU": "Jura",
        "LU": "Luzern",
        "NE": "Neuch\u00e2tel",
        "NW": "Nidwalden",
        "OW": "Obwalden",
        "SG": "St. Gallen",
        "SH": "Schaffhausen",
        "SO": "Solothurn",
        "SZ": "Schwyz",
        "TG": "Thurgau",
        "TI": "Ticino",
        "UR": "Uri",
        "VD": "Vaud",
        "VS": "Valais",
        "ZG": "Zug",
        "ZH": "Z\u00fcrich",
    }

    df = df.copy()
    df["Kanton"] = df["Kanton"].map(code_to_name).fillna(df["Kanton"])
    return df


def _get_timestamp_column(df):
    for key in ("Zeitstempel", "Datum", "Date", "Timestamp"):
        if key in df.columns:
            return key
    first = df.columns[0] if len(df.columns) else None
    if isinstance(first, str) and first.startswith("Unnamed"):
        return first
    return None


def _merge_geojson_by_property(geojson_obj, feature_key):
    if not feature_key or not feature_key.startswith("properties."):
        return geojson_obj

    prop_key = feature_key.split(".", 1)[1]
    merged = {}

    for feat in geojson_obj.get("features", []):
        props = feat.get("properties", {})
        name = props.get(prop_key)
        if not name:
            continue

        geom = feat.get("geometry", {})
        geom_type = geom.get("type")
        coords = geom.get("coordinates", [])
        if geom_type == "Polygon":
            polygons = [coords]
        elif geom_type == "MultiPolygon":
            polygons = coords
        else:
            continue

        entry = merged.setdefault(
            name,
            {
                "type": "Feature",
                "properties": {prop_key: name},
                "geometry": {"type": "MultiPolygon", "coordinates": []},
            },
        )
        entry["geometry"]["coordinates"].extend(polygons)

    return {"type": "FeatureCollection", "features": list(merged.values())}


def get_kantonskarte_month_options(
    data_path="data/raw/EnergieUebersichtCH-2025-2.xlsx",
    sheet_name="Zeitreihen0h15",
):
    data_file = Path(data_path)
    if not data_file.exists():
        return ["Total"]

    df = _load_timeseries(str(data_file), sheet_name)
    ts_col = _get_timestamp_column(df)
    if not ts_col:
        return ["Total"]

    df[ts_col] = pd.to_datetime(df[ts_col], dayfirst=True, errors="coerce")
    month_numbers = (
        df[ts_col]
        .dropna()
        .dt.month
        .unique()
    )
    month_numbers = sorted(int(m) for m in month_numbers if pd.notna(m))
    month_options = [calendar.month_name[m] for m in month_numbers if 1 <= m <= 12]
    return ["Total"] + month_options


def build_kantonskarte_map(
    data_path="data/raw/EnergieUebersichtCH-2025-2.xlsx",
    geojson_path="data/geo/swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.geojson",
    sheet_name="Zeitreihen0h15",
    metric_label="Produktion",
    split_mode="equal",
    feature_key="properties.NAME",
    selected_month="Total",
):
    data_file = Path(data_path)
    if not data_file.exists():
        return None, f"Daten nicht gefunden: {data_file.as_posix()}"

    geo_file = Path(geojson_path)
    if not geo_file.exists():
        return None, f"GeoJSON fehlt: {geo_file.as_posix()}"

    df = _load_timeseries(str(data_file), sheet_name)
    ts_col = _get_timestamp_column(df)
    if ts_col:
        df[ts_col] = pd.to_datetime(df[ts_col], dayfirst=True, errors="coerce")
        if selected_month and selected_month != "Total":
            try:
                month_index = list(calendar.month_name).index(selected_month)
            except ValueError:
                month_index = None
            if month_index:
                df = df[df[ts_col].dt.month == month_index]

    totals = _build_canton_totals(df, metric_label, split_mode)
    totals = _map_codes_to_names(totals)

    with geo_file.open("r", encoding="utf-8") as handle:
        geojson_obj = json.load(handle)

    feature_key = feature_key or _guess_feature_key(geojson_obj)
    if not feature_key or not feature_key.startswith("properties."):
        return None, "GeoJSON-Feature-Key nicht erkannt."

    geojson_obj = _merge_geojson_by_property(geojson_obj, feature_key)

    prop_key = feature_key.split(".", 1)[1]
    geo_names = {f.get("properties", {}).get(prop_key) for f in geojson_obj.get("features", [])}
    data_names = set(totals["Kanton"].unique())
    missing = sorted(n for n in data_names if n not in geo_names)
    warning = None
    if missing:
        warning = "Kantone im Datensatz fehlen im GeoJSON: " + ", ".join(missing)

    value_map = {row["Kanton"]: row["Wert"] for _, row in totals.iterrows()}
    display_map = {k: f"{value_map[k]:,.0f}".replace(",", "'") for k in value_map}
    for feat in geojson_obj.get("features", []):
        name = feat.get("properties", {}).get(prop_key)
        if name in display_map:
            feat["properties"]["Wert_kwh"] = display_map[name]

    map_center = [46.8, 8.3]
    m = folium.Map(location=map_center, zoom_start=7, tiles=None)

    palette = [
        "#EFF6EF",
        "#D4E5D2",
        "#B8D4B5",
        "#9CC398",
        "#85B581",
        "#64A15E",
        "#52844D",
        "#40673C",
        "#2E4A2B",
        "#1C2D1A",
        "#0A1009",
    ]
    colormap = LinearColormap(
        palette,
        vmin=totals["Wert"].min(),
        vmax=totals["Wert"].max(),
    )
    colormap._template = _COLORMAP_TEMPLATE_BOTTOMLEFT
    colormap.caption = f"{metric_label} (kWh)"
    colormap.add_to(m)

    def style_function(feature):
        name = feature.get("properties", {}).get(prop_key)
        value = value_map.get(name)
        fill = colormap(value) if value is not None else "#f2f2f2"
        return {
            "fillColor": fill,
            "color": "#555555",
            "weight": 0.7,
            "fillOpacity": 0.85,
        }

    tooltip = GeoJsonTooltip(
        fields=[prop_key, "Wert_kwh"],
        aliases=["Kanton:", f"{metric_label} (kWh):"],
        localize=True,
        sticky=False,
    )
    folium.GeoJson(geojson_obj, style_function=style_function, tooltip=tooltip).add_to(m)
    return m, warning


def plot_kantonskarte(
    data_path="data/raw/EnergieUebersichtCH-2025-2.xlsx",
    geojson_path="data/geo/swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.geojson",
    sheet_name="Zeitreihen0h15",
    metric_label="Produktion",
    split_mode="equal",
    feature_key="properties.NAME",
    height=340,
):
    if metric_label is None:
        metric_label = st.selectbox("Kennzahl", ["Produktion", "Verbrauch"], index=0)

    month_options = get_kantonskarte_month_options(data_path=data_path, sheet_name=sheet_name)

    selected_month = st.selectbox(
        "",
        month_options,
        index=0,
        label_visibility="collapsed",
    )


    m, warning = build_kantonskarte_map(
        data_path=data_path,
        geojson_path=geojson_path,
        sheet_name=sheet_name,
        metric_label=metric_label,
        split_mode=split_mode,
        feature_key=feature_key,
        selected_month=selected_month,
    )
    if not m:
        st.info("Karte konnte nicht geladen werden.")
        return
    if warning:
        st.warning(warning)

    st_folium(m, use_container_width=True, height=height)
