from dash import html, dcc
import dash_bootstrap_components as dbc

from .filters_kpi import filters_row
from .main_charts import main_tab_layout
from .wordcloud_tab import wordcloud_tab_layout
from .network_tab import network_tab_layout
from style import PRIMARY, PRIMARY_LIGHT, BG


def create_layout(df):

    # --------- Contenu principal (wrappé pour l'export PDF) ---------
    main_content = html.Div(
        id="page-wrapper",  # utilisé par html2canvas pour l'export PDF
        children=[
            dbc.Container(
                fluid=True,
                style={"marginLeft": "0"},
                children=[
                    # =============== PAGE 1 : TITRE + INTRO =================
                    html.Div(
                        style={"position": "relative"},
                        children=[
                            html.H1(
                                "COPUBLICATIONS INRIA",
                                className="text-center my-3 fw-bold",
                                style={"color": PRIMARY},
                            ),

                            # Titre dynamique du rapport (mis à jour par callback)
                            html.H2(
                                id="report-title",
                                className="text-center mb-3",
                                style={
                                    "fontSize": "1.2rem",
                                    "fontWeight": "500",
                                    "color": PRIMARY,
                                },
                            ),

                            # Bouton mode sombre (en haut à droite)
                            html.Div(
                                dbc.Button(
                                    "🌙 Mode sombre",
                                    id="toggle-dark",
                                    n_clicks=0,
                                    color="secondary",
                                    className="mb-3",
                                    style={
                                        "borderRadius": "12px",
                                        "fontWeight": "bold",
                                    },
                                ),
                                style={
                                    "position": "absolute",
                                    "top": "8px",
                                    "right": "20px",
                                },
                            ),
                        ],
                    ),

                    # Store pour les données dynamiques (CSV)
                    dcc.Store(id="store-data"),

                    # ================== CARTE DES FILTRES ================== #
                    dbc.Card(
                        dbc.CardBody(filters_row(df)),
                        className="mb-3 shadow-sm",
                        style={
                            "borderRadius": "18px",
                            "backgroundColor": "white",
                        },
                    ),

                    # =========== LIGNE CARTE MONDIALE + KPI (page 2 logique) =========== #
                    dbc.Row(
                        id="section-map-kpi",  # pour la logique "page 2"
                        children=[
                            # Colonne Carte mondiale
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        dcc.Graph(
                                            id="map",
                                            style={
                                                "height": "420px",
                                                "minHeight": "420px",
                                                "overflow": "hidden",
                                            },
                                            config={
                                                "responsive": True,
                                                "displaylogo": False,
                                                "displayModeBar": True,
                                                "scrollZoom": True,
                                                "displaylogo": False,
                                                "modeBarButtonsToAdd": [
                                                    "zoomInMapbox",
                                                    "zoomOutMapbox",
                                                    "resetViewMapbox",
                                                ],
                                            },
                                        )
                                    ),
                                    className="mb-3 shadow-sm",
                                    style={"borderRadius": "18px","width": "100%", "height": "55vh", "minHeight": "340px"},
                                ),
                                md=8,
                                sm=12,
                            ),
                            # Colonne KPI
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        html.Div(id="kpi-zone")
                                    ),
                                    className="mb-3 shadow-sm",
                                    style={"borderRadius": "18px"},
                                ),
                                md=4,
                                sm=12,
                            ),
                        ],
                        className="mb-3",
                    ),

                    html.Hr(),

                    # ================== ONGLET PRINCIPAL + AUTRES ================== #
                    dcc.Tabs(
                        id="tabs",
                        value="tab-main",
                        className="custom-tabs",
                        children=[
                            # ---------- TAB 1 : Vue principale ---------- #
                            dcc.Tab(
                                label="Vue principale",
                                value="tab-main",
                                children=[
                                    html.Div(
                                        id="main-tab-container",
                                        children=main_tab_layout(df),
                                    )
                                ],
                                className="custom-tab",
                                selected_className="custom-tab--selected",
                            ),

                            # ---------- TAB 2 : Wordcloud ---------- #
                            dcc.Tab(
                                label="Wordcloud des mots-clés",
                                value="tab-wordcloud",
                                children=[
                                    html.Div(
                                        id="wordcloud-tab-container",
                                        children=wordcloud_tab_layout(),
                                    )
                                ],
                                className="custom-tab",
                                selected_className="custom-tab--selected",
                            ),

                            # ---------- TAB 3 : Réseau ---------- #
                            dcc.Tab(
                                label="Réseau de copublications",
                                value="tab-network",
                                children=[network_tab_layout()],
                                className="custom-tab",
                                selected_className="custom-tab--selected",
                            ),

                            # ---------- TAB 4 : Évolution des copublications ---------- #
                            dcc.Tab(
                                label="Évolution des copublications",
                                value="tab-evolution",
                                className="custom-tab",
                                selected_className="custom-tab--selected",
                                children=[
                                    html.Div(
                                        id="evolution-tab-container",
                                        children=[
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        "À propos de cette page",
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
                                                                "Les graphiques de cette page permettent l'analyse des copublications internationales, notamment après application des filtres en haut de page.",
                                                                className="mb-2",
                                                            ),
                                                            html.P(
                                                                "Ces visualisations deviennent réellement lisibles quand elles portent sur un nombre réduit de publications (pour un seul centre, une ou plusieurs équipes, etc.).",
                                                                className="mb-2",
                                                                style={"fontWeight": "600"},
                                                            ),
                                                            html.Hr(className="my-2"),
                                                            html.P(
                                                                "• Disque « Centre–équipe–organisme étranger » : en filtrant par pays, en cliquant sur un centre, on voit les équipes copubliant avec des organismes de ce pays. En cliquant sur une équipe, on voit les noms des organismes.",
                                                                className="mb-2",
                                                            ),
                                                            html.P(
                                                                "• Poids des domaines : cette toile donne la proportion de publications de chaque domaine. En filtrant sur un pays ou un organisme, on visualize le poids des domaines des copublications concernées.",
                                                                className="mb-2",
                                                            ),
                                                            html.P(
                                                                "• Évolution des copublications : fournit une évolution quantitative du nombre de copublications internationales par équipe. En utilisant un filtre pays ou organisme, on verra l'évolution des copublications de cette équipe avec le pays et/ou l'organisme choisis.",
                                                                className="mb-2",
                                                            ),
                                                            html.P(
                                                                "• Flux croisés : en appliquant un filtre pays, on observe les flux entre les centres, les pays et les organismes copubliants. En appliquant un filtre centre, on observe les flux entre ce(s) centre(s) et les pays et les organismes copubliants.",
                                                                className="mb-0",
                                                            ),
                                                        ],
                                                        className="small",
                                                        style={"padding": "0.75rem"},
                                                    ),
                                                ],
                                                className="shadow-sm mb-3",
                                                style={"borderRadius": "18px"},
                                            ),

    # Sunburst + Radar
    dbc.Row(
        [
            dbc.Col(dcc.Graph(id="sunburst_collab", config={"responsive": True, "displaylogo": False}, style={"width": "100%", "height": "55vh", "minHeight": "340px"}), md=6),
            dbc.Col(dcc.Graph(id="radar_centre", config={"responsive": True, "displaylogo": False}, style={"width": "100%", "height": "55vh", "minHeight": "340px"}), md=6),
        ],
        className="mb-3",
    ),

                                            # TeamTimeline + Sankey
                                            dbc.Row(
                                                [
                                                    dbc.Col(dcc.Graph(id="team_timeline", config={"responsive": True, "displaylogo": False}, style={"width": "100%", "height": "55vh", "minHeight": "340px"}), md=7),

                                                    dbc.Col(dcc.Graph(id="sankey_collab", config={"responsive": True, "displaylogo": False}, style={"width": "100%", "height": "55vh", "minHeight": "340px"}), md=5),
                                                ],
                                                className="mb-3",
                                            ),

                                            # Story / Résumé narratif
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.Div(
                                                            id="story_evol",
                                                            className="p-3 rounded shadow-sm",
                                                        ),
                                                        md=12,
                                                    )
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),

                    # ================== FOOTER (toutes pages) ================== #
                    html.Hr(className="mt-4"),
                    html.Footer(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        "Rapport copublications – Inria · Groupe Datalake",
                                        className="me-3",
                                    ),
                                    html.Img(
                                        src="/assets/logo_inria.png",
                                        style={
                                            "height": "32px",
                                            "verticalAlign": "middle",
                                            "opacity": 0.9,
                                        },
                                    ),
                                ],
                                className="d-flex align-items-center justify-content-center gap-3",
                            )
                        ],
                        className="text-center py-3 app-footer",
                    ),
                ],
            )
        ],
    )

    # ---------- Bouton sidebar flottant ----------
    sidebar_button = dbc.Button(
        "☰",
        id="sidebar-toggle",
        n_clicks=0,
        className="shadow-sm",
        style={
            "position": "fixed",
            "top": "20px",
            "left": "20px",
            "zIndex": 1100,
            "borderRadius": "50%",
            "width": "44px",
            "height": "44px",
            "padding": "0",
            "fontSize": "24px",
            "background": PRIMARY,
            "border": "none",
        },
    )

    # ---------- Sidebar rétractable (texte + bouton PDF + upload CSV) ----------
    sidebar = dbc.Offcanvas(
        [
            html.H4(
                "GROUPE DATALAKE",
                className="fw-bold mb-1",
                style={"color": "white"},
            ),
            html.Hr(style={"borderTop": "1px solid rgba(255,255,255,0.7)"}),

            html.Img(
                src="/assets/logo_data.png",
                style={
                    "width": "100%",
                    "margin": "10px 0",
                    "opacity": 0.9,
                    "borderRadius": "12px",
                },
            ),

            html.P(
                "À propos de nous",
                className="fw-bold mt-2 mb-1",
                style={"color": "white"},
            ),

            html.P(
                (
                    "Le groupe Datalake, créé en 2022 au sein de la Direction de la culture et de l'information scientifique d'Inria, travaille à  "
                    "rendre possible le croisement de données entre HAL et divers référentiels, et de développer des outils d’analyse pour "
                    "les acteurs scientifiques et décisionnaires. Il est constitué de 6 membres : data scientists, développeurs et documentalistes experts. "
                    "Le présent outil a été développé à la demande et en collaboration avec deux scientifiques membres du réseau Direction des relations internationales (DRI),  "
                    "Luigi Liquori (Sophia) et Maria Kazolea (Bordeaux). Il a ensuite été amélioré à la demande de la DRI."
                ),
                style={
                    "color": "rgba(255,255,255,0.9)",
                    "fontSize": "0.9rem",
                },
            ),

            html.Hr(
                style={
                    "borderTop": "1px solid rgba(255,255,255,0.7)",
                    "marginTop": "0.8rem",
                }
            ),

            html.P(
                "Andréa Nebot, Daniel Da Silva, Kumar Guha",
                style={
                    "color": "rgba(255,255,255,0.9)",
                    "fontSize": "0.9rem",
                },
            ),

            html.Hr(
                style={
                    "borderTop": "1px solid rgba(255,255,255,0.7)",
                    "marginTop": "0.8rem",
                }
            ),

            html.Button(
                "📄 Exporter en PDF",
                id="export-pdf",
                className="btn btn-light",
                style={
                    "borderRadius": "12px",
                    "marginTop": "10px",
                    "fontWeight": "bold",
                    "width": "100%",
                },
            ),

            # ---- Upload CSV (sous Export PDF) ----
            html.Div(
                dcc.Upload(
                    id="upload-data",
                    children=html.Button(
                        "📁 Export CSV",
                        id="btn-upload-csv",
                        className="btn btn-light",
                        style={
                            "borderRadius": "12px",
                            "marginTop": "10px",
                            "fontWeight": "bold",
                            "width": "100%",
                        },
                    ),
                    multiple=False,
                 ),
            ),
        ],
        id="sidebar",
        is_open=False,
        placement="start",
        style={
            "background": (
                f"linear-gradient(135deg, {PRIMARY} 0%, "
                f"{PRIMARY_LIGHT} 40%, {BG} 100%)"
            ),
            "color": "white",
            "width": "320px",
            "padding": "20px",
            "borderRadius": "0 24px 24px 0",
            "boxShadow": "4px 0 20px rgba(0,0,0,0.25)",
        },
    )

    return html.Div([sidebar_button, sidebar, main_content])
