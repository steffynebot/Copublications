import dash_bootstrap_components as dbc

# === PALETTE DATALAKE / INRIA ===
# Cyan
CYAN_1 = "#00a5cc"
CYAN_2 = "#4dc0db"
CYAN_3 = "#80d2e7"
CYAN_4 = "#ccedf6"

# Bleu
BLUE_1 = "#1067a3"
BLUE_2 = "#5896bf"
BLUE_3 = "#87b2d2"
BLUE_4 = "#cfe1ed"

# Indigo
INDIGO_1 = "#27348b"
INDIGO_2 = "#6870ae"
INDIGO_3 = "#939ac6"
INDIGO_4 = "#d4d7e8"

# Violet
PURPLE_1 = "#5d4b9a"
PURPLE_2 = "#8e81b9"
PURPLE_3 = "#afa4cc"
PURPLE_4 = "#dfdbec"

# Magenta
MAGENTA_1 = "#a60f79"
MAGENTA_2 = "#c157a1"
MAGENTA_3 = "#d288bd"
MAGENTA_4 = "#eccfe5"

# Rouge
RED_1 = "#c9191e"
RED_2 = "#d95e61"
RED_3 = "#e58c8e"
RED_4 = "#f5d1d1"

# === COULEURS PRINCIPALES ===
PRIMARY = INDIGO_1
PRIMARY_LIGHT = CYAN_2
ACCENT = MAGENTA_1
DARK = BLUE_1
WHITE = "#ffffff"
BG = CYAN_4

# === ÉCHELLES CONTINUES POUR BARS ===
CYAN_SCALE = [CYAN_4, CYAN_1]
BLUE_SCALE = [BLUE_4, BLUE_1]
PURPLE_SCALE = [PURPLE_4, PURPLE_1]
MAGENTA_SCALE = [MAGENTA_4, MAGENTA_1]
RED_SCALE = [RED_4, RED_1]

# === SEQUENCES QUALITATIVES ===
CYAN_SEQ = [CYAN_1, CYAN_2, CYAN_3, CYAN_4]
BLUE_SEQ = [BLUE_1, BLUE_2, BLUE_3, BLUE_4]
PURPLE_SEQ = [PURPLE_1, PURPLE_2, PURPLE_3, PURPLE_4]
MAGENTA_SEQ = [MAGENTA_1, MAGENTA_2, MAGENTA_3, MAGENTA_4]
RED_SEQ = [RED_1, RED_2, RED_3, RED_4]

# Theme Bootstrap
THEME = dbc.themes.BOOTSTRAP

# Palette qualitative façon carte mondiale
QUAL_PALETTE = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
]

# === TEMPLATE PLOTLY ===
GRAPH_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=dict(
            family="Open Sans, Arial, sans-serif",
            color=PRIMARY,   # ❗ une seule couleur, pas une liste
            size=13,
        ),
        title=dict(
            x=0.5,
            xanchor="center",
            font=dict(
                size=20,
                color=PRIMARY,
                family="Open Sans, Arial, sans-serif",
            ),
        ),
        margin=dict(l=10, r=10, t=45, b=40),
        hoverlabel=dict(
            bgcolor=WHITE,
            font_size=12,
            font_family="Open Sans, Arial, sans-serif",
        ),
    )
)
