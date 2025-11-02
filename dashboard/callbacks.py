"""Interactive callbacks for Dash app."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
from dash import Input, Output


def register(app) -> None:
    @app.callback(
        Output("rainfall-chart", "figure"),
        Output("risk-map", "figure"),
        Output("recommendations", "children"),
        Input("basin-dropdown", "value"),
        Input("horizon-slider", "value"),
    )
    def update_dashboard(basin: str, horizon: int):  # type: ignore
        times = pd.date_range(datetime.utcnow(), periods=horizon, freq="H")
        rainfall = np.clip(np.sin(np.linspace(0, 3, num=horizon)) * 20, a_min=0, a_max=None)
        df = pd.DataFrame({"time": times, "rainfall": rainfall})

        rainfall_fig = px.line(df, x="time", y="rainfall", title=f"Forecast Rainfall for {basin}")

        risk_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": idx, "risk": risk},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [idx, idx],
                                [idx + 0.1, idx],
                                [idx + 0.1, idx + 0.1],
                                [idx, idx + 0.1],
                                [idx, idx],
                            ]
                        ],
                    },
                }
                for idx, risk in enumerate([0.2, 0.5, 0.8])
            ],
        }
        risk_df = pd.DataFrame({"id": list(range(3)), "risk": [0.2, 0.5, 0.8]})
        risk_fig = px.choropleth(
            risk_df,
            geojson=risk_geojson,
            locations="id",
            color="risk",
            color_continuous_scale="OrRd",
            range_color=(0, 1),
            featureidkey="properties.id",
        )
        risk_fig.update_geos(fitbounds="locations", visible=False)

        recommendations = [
            "- Low-risk areas: share precautionary tips",
            "- Medium-risk areas: prepare shelters",
            "- High-risk areas: plan evacuations",
        ]
        markdown = "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(recommendations)])

        return rainfall_fig, risk_fig, markdown
