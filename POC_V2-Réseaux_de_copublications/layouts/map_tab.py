from dash import dcc, html


def map_tab_layout():
    return html.Div(
        [
            html.Br(),
            dcc.Graph(id="map"),
        ]
    )
