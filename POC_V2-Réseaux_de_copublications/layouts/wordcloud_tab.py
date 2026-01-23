from dash import html, dcc
import dash_bootstrap_components as dbc

def wordcloud_tab_layout():
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    "À propos du graphique",
                                    className="fw-semibold small text-uppercase",
                                    style={
                                        "backgroundColor": "transparent",
                                        "borderBottom": "none",
                                        "padding": "0.5rem 0.75rem 0 0.75rem",
                                    },
                                ),
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "Nuage de mots constitué à partir des mots-clés déclarés par les déposants dans HAL pour les publications.",
                                            className="mb-2",
                                        ),
                                        html.P(
                                            "Attention : ce nuage ne reflète que les 50% de copublications qui ont des mots-clés.",
                                            className="mb-0",
                                            style={"fontWeight": "600"},
                                        ),
                                    ],
                                    className="small",
                                    style={"padding": "0.75rem"},
                                ),
                            ],
                            className="shadow-sm mb-3",
                            style={"borderRadius": "18px"},
                        ),
                        md=12,
                    )
                ]
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Img(
                                    id="wordcloud",
                                    style={"width": "70%", "borderRadius": "10px"},
                                ),
                                style={"padding": "0.75rem"},
                            ),
                            className="shadow-sm",
                            style={"borderRadius": "18px"},
                        ),
                        md=12,
                    )
                ]
            ),
        ],
        fluid=True,
        className="mt-2",
    )
