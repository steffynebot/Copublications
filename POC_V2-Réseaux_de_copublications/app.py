from dash import Dash, Output, Input
import dash_bootstrap_components as dbc

from data import load_data
from style import THEME
from layouts import create_layout
from callbacks import register_callbacks



def create_app():
    df = load_data()

    external_scripts = [
        "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js",
    ]

    app = Dash(
        __name__,
        external_stylesheets=[THEME],
        external_scripts=external_scripts,suppress_callback_exceptions=True,
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    )
    app.title = "Copublications Inria"

    app.layout = create_layout(df)

    # ✅ Callbacks Python
    register_callbacks(app, df)

    # Callback client pour le mode sombre
    app.clientside_callback(
        """
        function(n) {
            if (!n) {
                document.body.classList.remove("dark-mode");
                return "🌙";
            }
            if (n % 2 === 1) {
                document.body.classList.add("dark-mode");
                return "☀️";
            } else {
                document.body.classList.remove("dark-mode");
                return "🌙";
            }
        }
        """,
        Output("toggle-dark", "children"),
        Input("toggle-dark", "n_clicks"),
    )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
