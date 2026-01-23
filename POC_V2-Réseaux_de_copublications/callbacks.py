import base64
import io
import numpy as np
import pandas as pd
import dash
from dash import Output, Input, State, no_update, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import networkx as nx
from dash.exceptions import PreventUpdate
import json
import math


from data import filter_df
from style import (
    GRAPH_TEMPLATE,
    PRIMARY,
    PRIMARY_LIGHT,
    ACCENT,
    DARK,
    CYAN_SCALE,
    QUAL_PALETTE,
)


# ============================================================
#  Coordonnées des centres Inria
# ============================================================
CENTER_COORDS = {
    "Bordeaux": (44.8378, -0.5792),
    "Sophia": (43.6160, 7.0500),
    "Sophia Antipolis": (43.6160, 7.0500),
    "Grenoble": (45.1885, 5.7245),
    "Lille": (50.6292, 3.0573),
    "Rennes": (48.1173, -1.6778),
    "Saclay": (48.7323, 2.1710),
    "Paris": (48.8566, 2.3522),
    "Lyon": (45.7640, 4.8357),
    "Nancy": (48.6921, 6.1844),
    "Montpellier": (43.6108, 3.8767),
}


# ============================================================
#  Fonctions utilitaires pour les arcs courbés + glow
# ============================================================
def curved_arc(lat1, lon1, lat2, lon2, curvature=0.20, steps=22):
    lat_c = (lat1 + lat2) / 2 + (lat2 - lat1) * curvature
    lon_c = (lon1 + lon2) / 2 - (lon2 - lon1) * curvature

    t = np.linspace(0, 1, steps)
    lat_curve = (1 - t) ** 2 * lat1 + 2 * (1 - t) * t * lat_c + t**2 * lat2
    lon_curve = (1 - t) ** 2 * lon1 + 2 * (1 - t) * t * lon_c + t**2 * lon2

    return lat_curve, lon_curve


def add_glow_arc(fig, lat_curve, lon_curve, rgb="39,52,139"):
    glow_layers = [
        (10, f"rgba({rgb}, 0.04)"),
        (8, f"rgba({rgb}, 0.07)"),
        (6, f"rgba({rgb}, 0.10)"),
    ]

    for width, color in glow_layers:
        fig.add_trace(
            go.Scattermapbox(
                lat=lat_curve,
                lon=lon_curve,
                mode="lines",
                line=dict(width=width, color=color),
                hoverinfo="skip",
                showlegend=False,
            )
        )


# ============================================================
#  REGISTER CALLBACKS
# ============================================================
def register_callbacks(app, df_base):
    
    # ---------- 0a — Titre dynamique du rapport ----------
    @app.callback(
        Output("report-title", "children"),
        [
            Input("centre", "value"),
            Input("equipe", "value"),
            Input("pays", "value"),
            Input("ville", "value"),
            Input("org", "value"),
            Input("annee", "value"),
        ],
    )
    def update_report_title(centres, equipes, pays, villes, orgs, annees):
        # Centres
        if centres:
            if len(centres) == 1:
                txt_centre = f"centre Inria {centres[0]}"
            else:
                txt_centre = "centres Inria " + ", ".join(centres)
        else:
            txt_centre = "tous les centres Inria"

        # Équipes
        if equipes:
            if len(equipes) == 1:
                txt_eq = f"équipe {equipes[0]}"
            else:
                txt_eq = "équipes " + ", ".join(equipes)
        else:
            txt_eq = "toutes les équipes"

        # Villes
        if villes:
            if len(villes) == 1:
                txt_ville = f"ville {villes[0]}"
            else:
                txt_ville = "villes " + ", ".join(villes)
        else:
            txt_ville = "toutes les villes"

        # Pays
        if pays:
            if len(pays) == 1:
                txt_pays = f"pays {pays[0]}"
            else:
                txt_pays = "pays " + ", ".join(pays)
        else:
            txt_pays = "tous les pays"

        # Années
        if annees:
            try:
                an_min = min(annees)
                an_max = max(annees)
                if an_min == an_max:
                    txt_periode = f"année {an_min}"
                else:
                    txt_periode = f"période {an_min}–{an_max}"
            except Exception:
                txt_periode = "période sélectionnée"
        else:
            txt_periode = "toutes les années"

        return (
            f"Copublications internationales – {txt_centre}, "
            f"{txt_eq}, {txt_ville}, {txt_pays} ({txt_periode})"
        )    

    # ========================================================
    # 0 — SIDEBAR
    # ========================================================
    @app.callback(
        Output("sidebar", "is_open"),
        Input("sidebar-toggle", "n_clicks"),
        State("sidebar", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_sidebar(n_clicks, is_open):
        return not is_open if n_clicks else is_open

    # ========================================================
    # 0bis — Upload CSV → store-data
    # ========================================================
    @app.callback(
        Output("store-data", "data"),
        Input("upload-data", "contents"),
        prevent_initial_call=True,
    )
    def update_uploaded_data(contents):
        if contents is None:
            return no_update

        content_type, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)

        try:
            df_new = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        except Exception:
            # Si problème de parsing, on ne change rien
            return no_update

        return df_new.to_dict("records")

    # ========================================================
    # 1 — KPI + GRAPH PRINCIPAUX + CARTE + FLOW MAP
    # ========================================================
    @app.callback(
        [
            Output("kpi-zone", "children"),
            Output("bar_annee", "figure"),
            Output("top_pays", "figure"),
            Output("top_villes", "figure"),
            Output("top_orgs", "figure"),
            Output("map", "figure"),
            Output("flow_map", "figure"),
        ],
        [
            Input("centre", "value"),
            Input("equipe", "value"),
            Input("pays", "value"),
            Input("ville", "value"),
            Input("org", "value"),
            Input("annee", "value"),            Input("store-data", "data"),
        ],
    )
    def update_main(centres, equipes, pays, villes, orgs, annees, stored_data):

        # Choix du dataframe : CSV uploadé ou df initial
        if stored_data is not None:
            df = pd.DataFrame(stored_data)
        else:
            df = df_base

        dff = filter_df(df, centres, equipes, pays, villes, orgs, annees)

        # ======================== KPI ========================
        def kpi_card(label, value, color):
            return dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(label, className="small text-muted"),
                            html.H3(
                                value,
                                className="fw-bold mb-0",
                                style={"color": color},
                            ),
                        ]
                    ),
                    className="shadow-sm",
                    style={"borderRadius": "14px", "border": f"1px solid {color}20"},
                ),
                md=4,
                sm=6,
                xs=12,
            )

        kpi_global = dbc.Row(
            [
                kpi_card("Publications", dff["HalID"].nunique(), PRIMARY),
                kpi_card("Villes", dff["Ville"].nunique(), PRIMARY_LIGHT),
                kpi_card("Pays", dff["Pays"].nunique(), ACCENT),
                kpi_card("Équipes", dff["Equipe"].nunique(), PRIMARY_LIGHT),
                kpi_card("Auteurs Inria", dff["Auteurs_FR"].nunique(), PRIMARY),
                kpi_card("Copubliants", dff["Auteurs_copubliants"].nunique(), PRIMARY_LIGHT),
                
            ],
            className="g-2",
        )

        centre_counts = (
            dff.groupby("Centre")["HalID"]
            .nunique()
            .sort_values(ascending=False)
        )

        centre_badges = [
            dbc.Badge(
                f"{c}: {n}",
                pill=True,
                className="me-1 mb-1",
                style={
                    "backgroundColor": QUAL_PALETTE[i % len(QUAL_PALETTE)],
                    "color": "white",
                    "fontSize": "0.8rem",
                },
            )
            for i, (c, n) in enumerate(centre_counts.items())
        ]

        kpi_centres_block = html.Div(
            [
                html.Div(
                    "Publications par centre",
                    className="fw-bold small text-muted mb-1",
                ),
                html.Div(centre_badges, className="d-flex flex-wrap"),
            ]
        )

        kpis = html.Div([kpi_global, html.Hr(), kpi_centres_block])

        # ==================== BARRES PAR ANNÉE ====================
        pubs_by_year = (
            dff.groupby("Année")["HalID"]
            .nunique()
            .reset_index(name="Publications")
        )

        fig_year = px.bar(
            pubs_by_year,
            x="Année",
            y="Publications",
            color="Année",
            color_discrete_sequence=QUAL_PALETTE,
        )
        fig_year.update_layout(
            template=GRAPH_TEMPLATE,
            showlegend=False,
            margin=dict(l=10, r=10, t=60, b=40),
        )

        # ========== Utilitaire barres arrondies (Top X) ==========
        def top_bar_rounded(df_group, label, legend_below: bool = False):
            """Top 10 en donut (mêmes couleurs)"""
            if df_group.empty:
                return go.Figure().update_layout(
                    template=GRAPH_TEMPLATE,
                    title=None,
                    showlegend=True,
                    margin=dict(l=10, r=10, t=10, b=10),
                )

            df_top = (
                df_group.sort_values("Publications", ascending=True)
                .tail(10)
                .reset_index(drop=True)
            )

            # Couleurs (même palette que le reste)
            colors = [QUAL_PALETTE[i % len(QUAL_PALETTE)] for i in range(len(df_top))]

            fig = go.Figure(
                go.Pie(
                    labels=df_top[label],
                    values=df_top["Publications"],
                    hole=0.55,
                    sort=False,
                    direction="clockwise",
                    marker=dict(colors=colors),
                    textinfo="percent",
                    hovertemplate=f"{label} : %{{label}}<br>Publications : %{{value}}<extra></extra>",
                    showlegend=True,
                )
            )

            fig.update_layout(
                template=GRAPH_TEMPLATE,
                title=None,  # le titre est géré par la CardHeader
                showlegend=True,
                margin=dict(l=10, r=10, t=10, b=10),
            )

            # Placement de la légende
            if legend_below:
                fig.update_layout(
                    legend=dict(
                        orientation="h",
                        x=0.5,
                        xanchor="center",
                        y=-0.15,
                        yanchor="top",
                        font=dict(size=9),
                    ),
                    margin=dict(l=10, r=10, t=10, b=90),
                )
            else:
                fig.update_layout(
                    legend=dict(
                        orientation="v",
                        y=0.5,
                        yanchor="middle",
                        x=1.02,
                        xanchor="left",
                    )
                )

            return fig

        fig_pays = top_bar_rounded(
            dff.groupby("Pays")["HalID"].nunique().reset_index(name="Publications"),
            "Pays",
        )

        fig_villes = top_bar_rounded(
            dff.groupby("Ville")["HalID"].nunique().reset_index(name="Publications"),
            "Ville",
        )

        fig_orgs = top_bar_rounded(
            dff.groupby("Organisme_copubliant")["HalID"]
            .nunique()
            .reset_index(name="Publications"),
            "Organisme_copubliant",
            legend_below=True,
        )

        # ====================== CARTE MONDIALE ======================
        map_df = (
            dff.dropna(subset=["Latitude", "Longitude"])
            .groupby(["Ville", "Pays", "Latitude", "Longitude"])["HalID"]
            .nunique()
            .reset_index(name="Publications")
        )
                # Limite pour garder la carte fluide
        MAX_MAP_POINTS = 600
        map_df = map_df.sort_values("Publications", ascending=False).head(MAX_MAP_POINTS)


        # --- Si aucune donnée ---
        if map_df.empty:
            fig_map = go.Figure().update_layout(
                template=GRAPH_TEMPLATE,
                title="Carte mondiale des copublications (aucune donnée)",
                height=400,
                margin=dict(l=0, r=0, t=50, b=0),
            )

        else:
            fig_map = px.scatter_mapbox(
                map_df,
                lat="Latitude",
                lon="Longitude",
                size="Publications",
                size_max=50,
                color="Pays",
                hover_name="Ville",
                hover_data={"Pays": True, "Publications": True},
                zoom=1,
                title="Carte mondiale des copublications",
                
            )

            fig_map.update_layout(
                mapbox=dict(
                    style="open-street-map",
                    center=dict(lat=25, lon=5),   # centre FIXE
                    zoom=1,                       # zoom FIXE
                ),
                height=400,                       # hauteur FIXE
                margin=dict(l=0, r=0, t=50, b=0),
                autosize=False,
                uirevision="LOCK",                # ne pas re-zoomer quand les filtres changent
                legend=dict(
                    orientation="v",              # légende verticale
                    x=1.02,                       # à droite du graphe
                    xanchor="left",
                    y=1,
                    yanchor="top",
                    font=dict(size=10),
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="rgba(0,0,0,0.1)",
                    borderwidth=0.5,
                ),
            )

        
# ======================== FLOW MAP =========================
        # ======================== FLOW MAP (PERF) =========================
        # - Multi-centres
        # - Couleur différente par centre
        # - 1 trace de lignes par centre (au lieu de 100+ traces)
        # - pas de glow (énorme gain)
        # - arcs moins denses (steps réduits dans curved_arc)

        def hex_to_rgb(hex_color: str):
            h = hex_color.lstrip("#")
            if len(h) == 3:
                h = "".join([c * 2 for c in h])
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        fig_flow = go.Figure().update_layout(template=GRAPH_TEMPLATE, title=None)

        # Centres à afficher
        if centres and len(centres) > 0:
            centres_sel = [str(c) for c in centres if c is not None and str(c).strip() != ""]
        else:
            centres_sel = sorted(dff["Centre"].dropna().astype(str).unique().tolist())

        # Garde-fous perf
        MAX_CENTRES_FLOW = 6
        MAX_DEST_PER_CENTRE = 60
        centres_sel = centres_sel[:MAX_CENTRES_FLOW]

        if centres_sel:
            centre_color_map = {
                c: QUAL_PALETTE[i % len(QUAL_PALETTE)]
                for i, c in enumerate(centres_sel)
            }

            origins = []

            for centre_sel in centres_sel:
                flow_raw = dff[dff["Centre"].astype(str) == centre_sel].dropna(subset=["Latitude", "Longitude"])
                if flow_raw.empty:
                    continue

                flow_df = (
                    flow_raw.groupby(["Ville", "Pays", "Latitude", "Longitude"])
                    .agg(
                        Publications=("HalID", "nunique"),
                        UE_flag=("UE/Non_UE", lambda x: "UE" if (x == "UE").sum() >= (x != "UE").sum() else "Non_UE"),
                    )
                    .reset_index()
                    .sort_values("Publications", ascending=False)
                    .head(MAX_DEST_PER_CENTRE)
                )
                if flow_df.empty:
                    continue

                # Origine
                if centre_sel in CENTER_COORDS:
                    origin_lat, origin_lon = CENTER_COORDS[centre_sel]
                else:
                    origin_lat = float(flow_df["Latitude"].mean())
                    origin_lon = float(flow_df["Longitude"].mean())

                origins.append((origin_lat, origin_lon))

                max_pub = float(flow_df["Publications"].max()) or 1.0
                centre_hex = centre_color_map[centre_sel]
                r, g, b = hex_to_rgb(centre_hex)
                centre_rgb = f"{r},{g},{b}"

                # --- 1 seule trace lignes pour ce centre ---
                lats, lons, texts = [], [], []

                for _, row in flow_df.iterrows():
                    pub = float(row["Publications"])
                    is_ue = (row["UE_flag"] == "UE")

                    # UE plus visible que Non-UE
                    alpha = 0.85 if is_ue else 0.45

                    lat_curve, lon_curve = curved_arc(
                        origin_lat, origin_lon,
                        row["Latitude"], row["Longitude"]
                    )

                    # concatène les points + séparateur None
                    lats += list(lat_curve) + [None]
                    lons += list(lon_curve) + [None]

                    # texte hover (répété pour que plotly l'ait partout)
                    txt = f"{centre_sel} → {row['Ville']} – {row['Pays']} ({int(pub)} pubs)"
                    texts += [txt] * (len(lat_curve) + 1)

                # Largeur fixe => perf (sinon il faudrait plusieurs traces)
                fig_flow.add_trace(
                    go.Scattermapbox(
                        lat=lats,
                        lon=lons,
                        mode="lines",
                        line=dict(width=2.5, color=f"rgba({centre_rgb},0.70)"),
                        hoverinfo="text",
                        text=texts,
                        showlegend=False,
                    )
                )

                # Marqueur centre (légende = 1 par centre)
                fig_flow.add_trace(
                    go.Scattermapbox(
                        lat=[origin_lat],
                        lon=[origin_lon],
                        mode="markers+text",
                        marker=dict(size=18, color=centre_hex),
                        text=[centre_sel],
                        textposition="bottom right",
                        name=centre_sel,
                        showlegend=True,
                        hovertemplate="Centre : %{text}<extra></extra>",
                    )
                )

            # Centrage global
            if origins:
                center_lat = sum(o[0] for o in origins) / len(origins)
                center_lon = sum(o[1] for o in origins) / len(origins)
            else:
                center_lat, center_lon = 25, 5

            fig_flow.update_layout(
                template=GRAPH_TEMPLATE,
                title=None,
                mapbox=dict(
                    style="open-street-map",
                    center=dict(lat=center_lat, lon=center_lon),
                    zoom=1,
                ),
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(
                    orientation="h",
                    x=0.5,
                    xanchor="center",
                    y=-0.12,
                    yanchor="top",
                    font=dict(size=10),
                ),
            )


        return (
            kpis,
            fig_year,
            fig_pays,
            fig_villes,
            fig_orgs,
            fig_map,
            fig_flow,
        )

    # ========================================================
    # 2 — WORDCLOUD
    # ========================================================
    @app.callback(
        Output("wordcloud", "src"),
        [
            Input("centre", "value"),
            Input("equipe", "value"),
            Input("pays", "value"),
            Input("ville", "value"),
            Input("org", "value"),
            Input("annee", "value"),
            Input("tabs", "value"),
            Input("store-data", "data"),
        ],
    )
    def update_wordcloud(centres, equipes, pays, villes, orgs, annees, tab, stored_data):
        if tab != "tab-wordcloud":
            return no_update

        df = pd.DataFrame(stored_data) if stored_data is not None else df_base
        dff = filter_df(df, centres, equipes, pays, villes, orgs, annees)

        mots_series = dff["Mots-cles"].dropna().astype(str)
        if mots_series.empty:
            return ""

        sample = mots_series.sample(
            min(len(mots_series), 2000), random_state=42
        )
        text = " ".join(sample)

        wc = WordCloud(
            width=900,
            height=400,
            background_color="white",
            colormap="tab10",
        ).generate(text)

        buf = io.BytesIO()
        wc.to_image().save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


    # ========================================================
    # ========================================================
    # 3 — RÉSEAU : centres / auteurs Inria / auteurs étrangers
    #     + duplication figure pour modal "plein écran interne"
    # ========================================================
    @app.callback(
        [
            Output("network", "figure"),
            Output("network-fullscreen", "figure"),
        ],
        [
            Input("centre", "value"),
            Input("equipe", "value"),
            Input("pays", "value"),
            Input("ville", "value"),
            Input("org", "value"),
            Input("annee", "value"),
            Input("tabs", "value"),
            Input("store-data", "data"),
            Input("network-max-pubs", "value"),
            Input("network-max-nodes", "value"),  # gardé pour compat, non utilisé
        ],
    )
    def update_network(
        centres,
        equipes,
        pays,
        villes,
        orgs,
        annees,
        tab,
        stored_data,
        max_pubs,
        max_nodes,
    ):
        # On ne dessine le réseau que dans l'onglet dédié
        if tab != "tab-network":
            return no_update, no_update

        # dataframe source (upload ou df de base)
        df = pd.DataFrame(stored_data) if stored_data is not None else df_base

        # Filtres globaux
        dff = filter_df(df, centres, equipes, pays, villes, orgs, annees)

        if dff.empty or "HalID" not in dff.columns:
            fig_empty = go.Figure()
            fig_empty.update_layout(
                template=GRAPH_TEMPLATE,
                title="Réseau de copublications (aucune donnée pour les filtres actuels)",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                hovermode="closest",
                margin=dict(l=10, r=10, t=60, b=10),
            )
            return fig_empty, fig_empty

        # ---------------- Limitation nb de publications ----------------
        halids = dff["HalID"].dropna().unique().tolist()
        if max_pubs is None:
            max_pubs = 1500
        if len(halids) > max_pubs:
            halids_keep = pd.Series(halids).sample(max_pubs, random_state=42).tolist()
            dff_small = dff[dff["HalID"].isin(halids_keep)].copy()
        else:
            dff_small = dff.copy()

        # ------------ préparation des statistiques centres / auteurs ------------
        centres_stats = {}   # id_centre -> stats
        fr_stats = {}        # id_auteur_fr -> stats
        foreign_stats = {}   # id_auteur_etr -> stats
        edge_weights = {}    # (src, tgt) -> nb de copubs

        for _, row in dff_small.iterrows():
            centre_name = str(row.get("Centre", "") or "Centre Inria")
            centre_id = f"centre::{centre_name}"

            halid = row.get("HalID")
            country = str(row.get("Pays", "") or "Pays inconnu")
            org = str(row.get("Organisme_copubliant", "") or "").strip()

            # -- initialisation stats centre --
            c_stats = centres_stats.setdefault(
                centre_id,
                {
                    "type": "centre",
                    "label": centre_name,
                    "pubs": set(),
                    "fr_authors": set(),
                    "foreign_authors": set(),
                    "countries": set(),
                    "orgs": set(),
                },
            )
            if pd.notna(halid):
                c_stats["pubs"].add(halid)
            if country:
                c_stats["countries"].add(country)
            if org:
                c_stats["orgs"].add(org)

            fr_list = [a.strip() for a in str(row.get("Auteurs_FR", "")).split(";") if a.strip()]
            co_list = [a.strip() for a in str(row.get("Auteurs_copubliants", "")).split(";") if a.strip()]

            # -- auteurs Inria --
            for a in fr_list:
                fr_id = f"fr::{a}"
                st_fr = fr_stats.setdefault(
                    fr_id,
                    {"type": "fr", "label": a, "pubs": set(), "countries": set()},
                )
                if pd.notna(halid):
                    st_fr["pubs"].add(halid)
                if country:
                    st_fr["countries"].add(country)

                c_stats["fr_authors"].add(fr_id)

                key_cf = (centre_id, fr_id)
                edge_weights[key_cf] = edge_weights.get(key_cf, 0) + 1

            # -- auteurs étrangers --
            for b in co_list:
                foreign_id = f"foreign::{b}"
                st_fg = foreign_stats.setdefault(
                    foreign_id,
                    {"type": "foreign", "label": b, "pubs": set(), "country": country},
                )
                if pd.notna(halid):
                    st_fg["pubs"].add(halid)
                if country:
                    st_fg["country"] = country

                c_stats["foreign_authors"].add(foreign_id)

                # liens auteur Inria ↔ auteur étranger
                for a in fr_list:
                    fr_id = f"fr::{a}"
                    key_ff = (fr_id, foreign_id)
                    edge_weights[key_ff] = edge_weights.get(key_ff, 0) + 1

        # ------------- conversion des sets en nombres -------------
        for _, st in centres_stats.items():
            st["pubs"] = len(st["pubs"])
            st["nb_fr"] = len(st["fr_authors"])
            st["nb_foreign"] = len(st["foreign_authors"])
            st["nb_countries"] = len(st["countries"])
            st["nb_orgs"] = len(st["orgs"])

        for st in fr_stats.values():
            st["pubs"] = len(st["pubs"])
            st["nb_countries"] = len(st["countries"])

        for st in foreign_stats.values():
            st["pubs"] = len(st["pubs"])

        # ---------------- Tous les nœuds : centres + auteurs ----------------
        node_attrs = {}
        node_attrs.update(centres_stats)
        node_attrs.update(fr_stats)
        node_attrs.update(foreign_stats)

        filtered_edges = {
            (u, v): w
            for (u, v), w in edge_weights.items()
            if u in node_attrs and v in node_attrs
        }

        # ------------- construction du graphe NetworkX -------------
        G = nx.Graph()
        for nid, attr in node_attrs.items():
            G.add_node(nid, **attr)
        for (u, v), w in filtered_edges.items():
            G.add_edge(u, v, weight=w)

        if G.number_of_nodes() == 0:
            fig_empty = go.Figure().update_layout(
                template=GRAPH_TEMPLATE,
                title="Réseau de copublications (trop filtré / aucune donnée)",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                hovermode="closest",
            )
            return fig_empty, fig_empty

        # --------- layout ressort 2D avec anti-chevauchement ----------
        k = 0.45 + 0.02 * math.log(G.number_of_nodes() + 1)
        pos = nx.spring_layout(G, k=k, iterations=80, seed=42)

        coords = np.array(list(pos.values()))
        max_abs = np.abs(coords).max()
        if max_abs > 0:
            coords = coords / max_abs

        rng = np.random.RandomState(42)
        coords = coords + 0.01 * rng.normal(size=coords.shape)

        n_nodes = len(coords)
        if n_nodes <= 1500:
            d_min = 0.03
            for _ in range(5):
                for i in range(n_nodes):
                    for j in range(i + 1, n_nodes):
                        diff = coords[i] - coords[j]
                        dist = np.linalg.norm(diff)
                        if 0 < dist < d_min:
                            push = (d_min - dist) / dist * 0.5 * diff
                            coords[i] += push
                            coords[j] -= push

        max_abs = np.abs(coords).max()
        if max_abs > 0:
            coords = coords / max_abs

        for nid, c in zip(pos.keys(), coords):
            pos[nid] = c

        # ------------- Traces des arêtes (gris clair, pas vert) -------------
        edge_x, edge_y = [], []
        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        edge_trace = go.Scattergl(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=0.8, color="rgba(160,160,160,0.45)"),
            hoverinfo="none",
            showlegend=False,
        )

        # ------------- Couleurs centres -------------
        centre_names = sorted({a["label"] for a in node_attrs.values() if a["type"] == "centre"})
        centre_color_map = {
            name: QUAL_PALETTE[i % len(QUAL_PALETTE)]
            for i, name in enumerate(centre_names)
        }

        # ------------- Préparer coordonnées + tailles + hover strings -------------
        centre_x, centre_y, centre_size, centre_outline, centre_label, centre_hover = [], [], [], [], [], []
        fr_x, fr_y, fr_size, fr_label, fr_hover = [], [], [], [], []
        fg_x, fg_y, fg_size, fg_label, fg_hover = [], [], [], [], []

        for nid, attrs in node_attrs.items():
            x, y = pos[nid]
            ntype = attrs["type"]

            if ntype == "centre":
                centre_x.append(x)
                centre_y.append(y)
                centre_label.append(attrs["label"])
                centre_outline.append(centre_color_map.get(attrs["label"], "#E91E63"))
                centre_size.append(24 + 5 * math.sqrt(max(attrs["pubs"], 1)))

                centre_hover.append(
                    f"<b>Centre</b> : {attrs['label']}<br>"
                    f"Publications : {attrs['pubs']}<br>"
                    f"Auteurs Inria : {attrs['nb_fr']}<br>"
                    f"Auteurs copubliants : {attrs['nb_foreign']}<br>"
                    f"Pays : {attrs['nb_countries']}<br>"
                    f"Organismes : {attrs['nb_orgs']}"
                )

            elif ntype == "fr":
                fr_x.append(x)
                fr_y.append(y)
                fr_label.append(attrs["label"])
                fr_size.append(10 + 3 * math.sqrt(max(attrs["pubs"], 1)))

                fr_hover.append(
                    f"<b>Auteur Inria</b><br>"
                    f"Nom : {attrs['label']}<br>"
                    f"# pubs : {attrs['pubs']}<br>"
                    f"# pays partenaires : {attrs.get('nb_countries', 0)}"
                )

            elif ntype == "foreign":
                fg_x.append(x)
                fg_y.append(y)
                fg_label.append(attrs["label"])
                fg_size.append(8 + 2.5 * math.sqrt(max(attrs["pubs"], 1)))

                fg_hover.append(
                    f"<b>Auteur étranger</b><br>"
                    f"Nom : {attrs['label']}<br>"
                    f"Pays principal : {attrs.get('country', 'Pays inconnu')}<br>"
                    f"# pubs : {attrs['pubs']}"
                )

        # ------------- Centres : ronds blancs contour coloré + nom centré -------------
        centre_trace = go.Scattergl(
            x=centre_x,
            y=centre_y,
            mode="markers+text",
            name="Centres",
            marker=dict(
                size=centre_size,
                color="white",
                line=dict(width=3, color=centre_outline),
                opacity=0.98,
            ),
            text=centre_label,
            textposition="middle center",
            textfont=dict(size=9, color="#111111"),
            customdata=centre_hover,
            hovertemplate="%{customdata}<extra></extra>",
        )

        # ------------- Auteurs Inria : verts (taille ∝ pubs) -------------
        fr_trace = go.Scattergl(
            x=fr_x,
            y=fr_y,
            mode="markers",
            name="Auteurs Inria",
            marker=dict(
                size=fr_size,
                color="rgba(0,150,136,0.95)",
                line=dict(width=0.8, color="rgba(0,0,0,0.55)"),
                opacity=0.9,
            ),
            customdata=fr_hover,
            hovertemplate="%{customdata}<extra></extra>",
        )

        # ------------- Auteurs étrangers : noirs (taille ∝ pubs) -------------
        fg_trace = go.Scattergl(
            x=fg_x,
            y=fg_y,
            mode="markers",
            name="Auteurs étrangers",
            marker=dict(
                size=fg_size,
                color="rgba(30,30,30,0.95)",
                line=dict(width=0.8, color="rgba(250,250,250,0.7)"),
                opacity=0.9,
            ),
            customdata=fg_hover,
            hovertemplate="%{customdata}<extra></extra>",
        )

        # Labels auteurs (optionnels)
        fr_labels_trace = go.Scattergl(
            x=fr_x, y=fr_y,
            mode="text",
            text=fr_label,
            textfont=dict(size=7, color="rgba(80,80,80,0.85)"),
            hoverinfo="skip",
            showlegend=False,
        )
        fg_labels_trace = go.Scattergl(
            x=fg_x, y=fg_y,
            mode="text",
            text=fg_label,
            textfont=dict(size=7, color="rgba(120,120,120,0.8)"),
            hoverinfo="skip",
            showlegend=False,
        )

        fig_net = go.Figure(
            data=[
                edge_trace,
                centre_trace,
                fr_trace,
                fg_trace,
                fr_labels_trace,
                fg_labels_trace,
            ]
        )

        fig_net.update_layout(
            template=GRAPH_TEMPLATE,
            title="Réseau de copublications",
            showlegend=True,
            legend=dict(
                orientation="v",
                x=0.01,
                y=0.99,
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1,
                font=dict(size=10),
            ),
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
            margin=dict(l=10, r=10, t=60, b=10),
            hovermode="closest",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
        )
        fig_net.layout.hovermode = "closest"

        # Même figure dans la vue "plein écran"
        return fig_net, fig_net


    # ========================================================
    # 3bis — MODAL plein écran (fenêtre flottante)
    # ========================================================
    @app.callback(
        Output("network-fullscreen-modal", "style"),
        [
            Input("btn-network-fullscreen-open", "n_clicks"),
            Input("btn-network-fullscreen-close", "n_clicks"),
        ],
        State("network-fullscreen-modal", "style"),
        prevent_initial_call=True,
    )
    def toggle_network_fullscreen(open_clicks, close_clicks, current_style):
        import dash  # (évite d'ajouter un import global si tu préfères)

        ctx = dash.callback_context
        if not ctx.triggered:
            return current_style

        trigger = ctx.triggered[0]["prop_id"].split(".")[0]

        style_open = {
            "display": "block",
            "position": "fixed",
            "inset": "0",
            "background": "rgba(0,0,0,0.35)",
            "zIndex": "9999",
            "padding": "24px",
        }
        style_closed = {**style_open, "display": "none"}

        if trigger == "btn-network-fullscreen-open":
            return style_open
        if trigger == "btn-network-fullscreen-close":
            return style_closed

        return current_style


    # ========================================================
    # 4 — Onglet "Évolution des copublications"
    # ========================================================
    @app.callback(
        [
            Output("sunburst_collab", "figure"),
            Output("team_timeline", "figure"),
            Output("sankey_collab", "figure"),
            Output("radar_centre", "figure"),
            Output("story_evol", "children"),
        ],
        [
            Input("centre", "value"),
            Input("equipe", "value"),
            Input("pays", "value"),
            Input("ville", "value"),
            Input("org", "value"),
            Input("annee", "value"),
            Input("tabs", "value"),
            Input("store-data", "data"),
        ],
    )
    def update_evolution(
        centres, equipes, pays, villes, orgs, annees, tab, stored_data
    ):
        # On ne calcule l'onglet que lorsqu'il est actif
        if tab != "tab-evolution":
            return no_update, no_update, no_update, no_update, no_update

        # Choix du dataframe (CSV chargé ou df initial)
        df = pd.DataFrame(stored_data) if stored_data is not None else df_base
        dff = filter_df(df, centres, equipes, pays, villes, orgs, annees)

        # ---------- 0) Cas sans données ----------
        if dff.empty:
            empty_fig = go.Figure().update_layout(
                template=GRAPH_TEMPLATE,
                title="Aucune donnée pour les filtres actuels",
            )
            story_div = html.Div(
                [
                    html.H5(
                        "Résumé des copublications",
                        className="mb-2",
                        style={"color": PRIMARY},
                    ),
                    html.P(
                        "Aucune copublication n’est disponible pour les filtres sélectionnés.",
                        className="mb-1",
                    ),
                ],
                style={
                    "backgroundColor": "#f8fbff",
                    "borderRadius": "12px",
                    "border": f"1px solid {PRIMARY_LIGHT}30",
                },
            )
            return empty_fig, empty_fig, empty_fig, empty_fig, story_div

        # =========================================================================
        # 1) SUNBURST Centre → Équipe → Organisme
        # =========================================================================
        if all(col in dff.columns for col in ["Centre", "Equipe", "Organisme_copubliant"]):
            sun_df = (
                dff.groupby(["Centre", "Equipe", "Organisme_copubliant"])["HalID"]
                .nunique()
                .reset_index(name="Publications")
            )

            fig_sunburst = px.sunburst(
                sun_df,
                path=["Centre", "Equipe", "Organisme_copubliant"],
                values="Publications",
                color="Centre",
                color_discrete_sequence=QUAL_PALETTE,
                title="Centre → Équipe → Organisme",
            )
            fig_sunburst.update_layout(template=GRAPH_TEMPLATE)
        else:
            fig_sunburst = go.Figure().update_layout(
                template=GRAPH_TEMPLATE,
                title="Hiérarchie collaborations (colonnes manquantes)",
            )

        # =========================================================================
        # 2) TEAM TIMELINE : évolution des copublications par équipe
        # =========================================================================
        if all(col in dff.columns for col in ["Année", "Equipe"]):
            team_df = (
                dff.groupby(["Année", "Equipe"])["HalID"]
                .nunique()
                .reset_index(name="Publications")
            )

            fig_team = px.line(
                team_df,
                x="Année",
                y="Publications",
                color="Equipe",
                markers=True,
                color_discrete_sequence=QUAL_PALETTE,
                title="Évolution des copublications par équipe",
            )
            fig_team.update_layout(
                template=GRAPH_TEMPLATE,
                hovermode="x unified",
            )
        else:
            fig_team = go.Figure().update_layout(
                template=GRAPH_TEMPLATE,
                title="Évolution par équipe (colonnes manquantes)",
            )

        # =========================================================================
        # 3) SANKEY Centre → Pays → Organisme
        # =========================================================================
        if all(col in dff.columns for col in ["Centre", "Pays", "Organisme_copubliant"]):
            sankey_df = (
                dff.groupby(["Centre", "Pays", "Organisme_copubliant"])["HalID"]
                .nunique()
                .reset_index(name="Publications")
                .sort_values("Publications", ascending=False)
                .head(80)
            )

            labels = []
            node_index = {}

            def get_index(label):
                if label not in node_index:
                    node_index[label] = len(node_index)
                    labels.append(label)
                return node_index[label]

            sources, targets, values = [], [], []

            for _, row in sankey_df.iterrows():
                c = get_index(f"Centre : {row['Centre']}")
                p = get_index(f"Pays : {row['Pays']}")
                o = get_index(f"Org : {row['Organisme_copubliant']}")
                v = row["Publications"]

                sources.append(c)
                targets.append(p)
                values.append(v)

                sources.append(p)
                targets.append(o)
                values.append(v)

            fig_sankey = go.Figure(
                data=[
                    go.Sankey(
                        node=dict(
                            pad=15,
                            thickness=15,
                            line=dict(color="black", width=0.3),
                            label=labels,
                            color=[
                                QUAL_PALETTE[i % len(QUAL_PALETTE)]
                                for i in range(len(labels))
                            ],
                        ),
                        link=dict(
                            source=sources,
                            target=targets,
                            value=values,
                            color="rgba(39,52,139,0.2)",
                        ),
                    )
                ]
            )
            fig_sankey.update_layout(
                template=GRAPH_TEMPLATE,
                title="Flux Centre → Pays → Organisme",
            )
        else:
            fig_sankey = go.Figure().update_layout(
                template=GRAPH_TEMPLATE,
                title="Flux Centre → Pays → Organisme (colonnes manquantes)",
            )

        # =========================================================================
        # 4) RADAR MULTI-CENTRES PAR DOMAINES
        # =========================================================================
        if "Centre" in dff.columns and "Domaine(s)" in dff.columns:
            # On ne garde que les lignes avec centre + domaine
            dom_df = (
                dff.dropna(subset=["Centre", "Domaine(s)"])
                .groupby(["Centre", "Domaine(s)"])["HalID"]
                .nunique()
                .reset_index(name="Publications")
            )

            if dom_df.empty:
                fig_radar = go.Figure().update_layout(
                    template=GRAPH_TEMPLATE,
                    title="Profil par domaine (aucune donnée domaine)",
                )
            else:
                # Centres à tracer : ceux filtrés s'il y en a, sinon les principaux
                if centres:
                    centres_to_plot = [
                        c for c in centres if c in dom_df["Centre"].unique()
                    ]
                else:
                    centres_to_plot = (
                        dom_df.groupby("Centre")["Publications"]
                        .sum()
                        .sort_values(ascending=False)
                        .head(5)
                        .index.tolist()
                    )

                # Si rien (centres filtrés pas présents), on prend les top
                if not centres_to_plot:
                    centres_to_plot = (
                        dom_df.groupby("Centre")["Publications"]
                        .sum()
                        .sort_values(ascending=False)
                        .head(5)
                        .index.tolist()
                    )

                # Top domaines (axes du radar)
                top_dom = (
                    dom_df.groupby("Domaine(s)")["Publications"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(6)
                    .index.tolist()
                )

                categories = top_dom
                categories_closed = categories + categories[:1]

                fig_radar = go.Figure()

                # Une trace par centre → superposition des polygones
                for i, centre in enumerate(centres_to_plot):
                    sub = dom_df[dom_df["Centre"] == centre]
                    vals = []
                    for dom in categories:
                        vals.append(
                            sub.loc[sub["Domaine(s)"] == dom, "Publications"].sum()
                        )
                    vals_closed = vals + vals[:1]

                    fig_radar.add_trace(
                        go.Scatterpolar(
                            r=vals_closed,
                            theta=categories_closed,
                            fill="toself",
                            name=centre,
                            line=dict(color=QUAL_PALETTE[i % len(QUAL_PALETTE)]),
                            opacity=0.55,
                        )
                    )

                fig_radar.update_layout(
                    template=GRAPH_TEMPLATE,
                    title=(
                        "Profil par domaine – centres : "
                        + ", ".join(centres_to_plot)
                    ),
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            tickfont=dict(size=10),
                        )
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                    ),
                )
        else:
            fig_radar = go.Figure().update_layout(
                template=GRAPH_TEMPLATE,
                title="Profil par domaine (colonnes Centre / Domaine(s) manquantes)",
            )

        # =========================================================================
        # 5) STORY MODE (résumé textuel)
        # =========================================================================
        total_pubs = dff["HalID"].nunique() if "HalID" in dff.columns else len(dff)
        nb_pays = dff["Pays"].nunique() if "Pays" in dff.columns else 0
        nb_orgs = (
            dff["Organisme_copubliant"].nunique()
            if "Organisme_copubliant" in dff.columns
            else 0
        )
        years = (
            dff["Année"].dropna().astype(int)
            if "Année" in dff.columns
            else pd.Series([], dtype=int)
        )
        if len(years) > 0:
            an_min, an_max = int(years.min()), int(years.max())
            periode = f"{an_min}–{an_max}"
        else:
            periode = "période inconnue"

        # Centres principaux pour le texte
        centres_present = (
            dff["Centre"].dropna().unique().tolist()
            if "Centre" in dff.columns
            else []
        )
        if centres and centres_present:
            centres_story = [c for c in centres if c in centres_present]
        else:
            centres_story = centres_present

        if len(centres_story) == 0:
            centres_txt = "les centres Inria impliqués"
        elif len(centres_story) == 1:
            centres_txt = f"le centre {centres_story[0]}"
        else:
            centres_txt = "les centres " + ", ".join(centres_story)

        story_children = [
            html.H5(
                "Résumé des copublications",
                className="mb-2",
                style={"color": PRIMARY},
            ),
            html.P(
                f"Sur la période {periode}, les filtres actuels représentent "
                f"{total_pubs} copublications impliquant {nb_pays} pays "
                f"et {nb_orgs} organismes partenaires.",
                className="mb-1",
            ),
            html.P(
                f"Les profils par domaine et les flux décrits ci-dessus mettent en évidence le rôle de {centres_txt}.",
                className="mb-0",
            ),
        ]

        story_div = html.Div(
            story_children,
            style={
                "backgroundColor": "#f8fbff",
                "borderRadius": "12px",
                "border": f"1px solid {PRIMARY_LIGHT}30",
            },
        )

        return fig_sunburst, fig_team, fig_sankey, fig_radar, story_div
