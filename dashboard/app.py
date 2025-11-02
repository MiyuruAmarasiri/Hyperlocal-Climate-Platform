"""Plotly Dash application."""

from __future__ import annotations

import os
import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, dcc, html
import plotly.express as px
import pandas as pd

from dashboard import callbacks


def create_dash_app(server=None) -> Dash:
    """Initialise the Dash UI, optionally binding to an existing Flask server."""

    dash_server = server if server is not None else True
    app = dash.Dash(
        __name__,
        server=dash_server,
        external_stylesheets=[dbc.themes.SANDSTONE],
    )
    app.layout = dbc.Container(
        [
            html.H2("Hyperlocal Climate Risk Dashboard"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Select Basin"),
                            dcc.Dropdown(
                                id="basin-dropdown",
                                options=[{"label": f"Basin {i}", "value": f"basin-{i}"} for i in range(1, 4)],
                                value="basin-1",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label("Forecast Horizon (hours)"),
                            dcc.Slider(id="horizon-slider", min=6, max=168, step=6, value=48),
                        ],
                        md=8,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="rainfall-chart"), md=6),
                    dbc.Col(dcc.Graph(id="risk-map"), md=6),
                ]
            ),
            dbc.Row(dbc.Col(dcc.Markdown(id="recommendations"))),
        ],
        fluid=True,
        className="p-4",
    )
    callbacks.register(app)
    return app


if __name__ == "__main__":
    app = create_dash_app()
    host = os.getenv("DASH_HOST", "127.0.0.1")
    port = int(os.getenv("DASH_PORT", "8050"))
    app.run(debug=True, host=host, port=port)
