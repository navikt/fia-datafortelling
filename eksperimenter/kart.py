import json

import geojson_rewind
import geopandas as gpd
import plotly.express as px

from src.utils.helper import annotate_ikke_offisiell_statistikk


def last_kart():
    filename = "kart/Kommuner-S.geojson"
    gdf = gpd.read_file(filename)

    return gdf.set_geometry(
        gpd.GeoDataFrame.from_features(
            json.loads(geojson_rewind.rewind(gdf.to_json(), rfc7946=False))["features"]
        ).geometry.values
    )


def plot_kart(data, kartdata, label, colormap="mint", width=800, height=800):
    fig = px.choropleth(
        data,
        geojson=kartdata,
        locations="kommunenummer",
        hover_name="kommunenavn",
        hover_data={
            label: True,
            "kommunenummer": False,
            "kommunenavn": False,
            "resultatområde": True,
            "fylkesnavn": True,
        },
        labels={
            "behovsvurdering": "Fullførte behovsvurderinger",
            "plan": "Opprettede planer",
            "evaluering": "Fullførte evalueringer",
        },
        featureidkey="properties.kommunenummer",
        color=label,
        color_continuous_scale=colormap,
        width=width,
        height=height,
    )

    fig.update_traces(marker_line_width=0)
    fig.update_geos(fitbounds="locations", visible=False, scope="europe")

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_showscale=False,
    )

    return annotate_ikke_offisiell_statistikk(fig)
