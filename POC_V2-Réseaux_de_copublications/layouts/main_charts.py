from dash import dcc, html
import dash_bootstrap_components as dbc


def main_tab_layout(df):
    """
    Mise en page de l'onglet 'Vue principale'

    - Ligne 1 : explication gauche + barres années + explication droite
    - Ligne 2 : Top 10 pays / Top 10 villes / Top 10 organismes
    - Ligne 3 : explication flux / flow map avec filtre centre local
    """

    # Centres disponibles pour le dropdown du flux
    centres_options = []
    if "Centre" in df.columns:
        centres_uniques = (
            df["Centre"]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
        )
        centres_options = [{"label": c, "value": c} for c in centres_uniques]

    # ---- Fabrique de cartes graphiques classiques ----
    def card_graph(graph_id: str, title: str) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    title,
                    className="fw-semibold small text-uppercase",
                    style={
                        "backgroundColor": "transparent",
                        "borderBottom": "none",
                        "padding": "0.5rem 0.75rem 0 0.75rem",
                    },
                ),
                dbc.CardBody(
                    dcc.Graph(
                        id=graph_id,
                        style={"height": "340px"},
                        config={"displayModeBar": True, "scrollZoom": True, "displaylogo": False, "modeBarButtonsToAdd": ["zoomInMapbox", "zoomOutMapbox", "resetViewMapbox"]},
                    ),
                    className="main-graph-card",
                    style={"padding": "0.25rem"},
                ),
            ],
            className="shadow-sm mb-3",
            style={"borderRadius": "18px", "height": "100%"},
        )

    # ---- Carte texte simple (explications) ----
    def card_text(title: str, children) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    title,
                    className="fw-semibold small text-uppercase",
                    style={
                        "backgroundColor": "transparent",
                        "borderBottom": "none",
                        "padding": "0.5rem 0.75rem 0 0.75rem",
                    },
                ),
                dbc.CardBody(
                    children,
                    className="small",
                    style={"padding": "0.75rem"},
                ),
            ],
            className="shadow-sm mb-3",
            style={"borderRadius": "18px", "height": "100%"},
        )

    # ---- Carte spéciale pour le flux (dropdown + graph) ----
    flow_card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div(
                    "Flux de copublications par centre",
                    className="fw-semibold small text-uppercase",
                    style={"color": "black"},
                ),
                style={
                    "backgroundColor": "transparent",
                    "borderBottom": "none",
                    "padding": "0.5rem 0.75rem 0.25rem 0.75rem",
                },
            ),
            dbc.CardBody(
                dcc.Graph(
                    id="flow_map",
                    style={"height": "340px"},
                    config={"displayModeBar": True, "scrollZoom": True, "displaylogo": False, "modeBarButtonsToAdd": ["zoomInMapbox", "zoomOutMapbox", "resetViewMapbox"]},
                ),
                className="main-graph-card",
                style={"padding": "0.25rem"},
            ),
        ],
        className="shadow-sm mb-3",
        style={"borderRadius": "18px", "height": "100%"},
    )

    return dbc.Container(
        [
            # ---------- Ligne 1 : explications + barres années ----------
            dbc.Row(
                [
                    # Explication gauche
                    dbc.Col(
                        card_text(
                            "À propos du graphique",
                            [
                                html.P(
                                    "Ce graphique montre l'évolution du nombre de "
                                    "copublications par année dans le périmètre "
                                    "défini par les filtres.",
                                    className="mb-2",
                                ),
                                html.P(
                                    "Utilisez ce visuel pour repérer les années "
                                    "fortes, les tendances de croissance ou de "
                                    "stagnation.",
                                    className="mb-0",
                                ),
                            ],
                        ),
                        md=4,
                        sm=12,
                    ),
                    # Graphique central
                    dbc.Col(
                        card_graph(
                            "bar_annee",
                            "Nombre de publications par année",
                        ),
                        md=8,
                        sm=12,
                    ),
                ],
                className="mb-3",
            ),

            # ---------- Ligne 2 : 3 Top 10 sur la même ligne ----------
            dbc.Row(
                [
                    dbc.Col(
                        card_graph(
                            "top_pays",
                            "Top 10 des pays",
                        ),
                        md=4,
                        sm=12,
                    ),
                    dbc.Col(
                        card_graph(
                            "top_villes",
                            "Top 10 des villes",
                        ),
                        md=4,
                        sm=12,
                    ),
                    dbc.Col(
                        card_graph(
                            "top_orgs",
                            "Top 10 des organismes copubliants",
                        ),
                        md=4,
                        sm=12,
                    ),
                ],
                className="mb-3",
            ),

            # ---------- Ligne 3 : explication flux + flow map ----------
            dbc.Row(
                [
                    dbc.Col(
                        card_text(
                            "Comprendre le flux de copublications",
                            [
                                html.P(
                                    "Ce graphique représente les flux de "
                                    "copublications entre un centre Inria et les "
                                    "villes / pays partenaires.",
                                    className="mb-2",
                                ),
                                html.P(
                                    "Chaque arc correspond à un ensemble de "
                                    "copublications. L'épaisseur de l'arc est "
                                    "proportionnelle au nombre de publications.",
                                    className="mb-2",
                                ),
                                html.P(
                                    "Vous pouvez sélectionner un centre spécifique "
                                    "dans le menu déroulant ou utiliser les filtres "
                                    "globaux en haut de page.",
                                    className="mb-0",
                                ),
                            ],
                        ),
                        md=4,
                        sm=12,
                    ),
                    dbc.Col(
                        flow_card,
                        md=8,
                        sm=12,
                    ),
                ],
                className="mb-3",
            ),
        ],
        fluid=True,
        className="mt-2",
    )
