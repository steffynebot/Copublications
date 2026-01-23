import pandas as pd

CSV_PATH = r"C:\Users\abapst\nb_python\copublication_italie\ITALIE\plotly2\Copublis_dashboard.csv"


def load_data():
    """Lecture robuste du CSV + nettoyage colonnes et valeurs + harmonisation noms."""
    df = None
    last_err = None

    # Encodages et séparateurs courants
    encodings = ["utf-8-sig", "utf-8", "latin1"]
    seps = [",", ";"]

    # -------- Lecture robuste --------
    for enc in encodings:
        for sep in seps:
            try:
                df_try = pd.read_csv(
                    CSV_PATH,
                    encoding=enc,
                    sep=sep,
                    engine="python",
                    on_bad_lines="skip",
                    dtype=str,
                )

                # Si le parsing a créé 1 seule colonne (souvent mauvais sep), on réessaie
                if df_try is not None and df_try.shape[1] >= 2:
                    df = df_try
                    break
            except Exception as e:
                last_err = e
                df = None
        if df is not None:
            break

    if df is None:
        raise RuntimeError(f"Impossible de lire le CSV. Dernière erreur: {last_err}")

    # -------- Nettoyage des NOMS de colonnes (BOM + espaces) --------
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=False)  # BOM éventuel
        .str.strip()
    )

    # -------- Harmonisation des noms (nouveau CSV -> ancien code) --------
    rename_map = {
        # noms avec espaces
        "Auteurs FR": "Auteurs_FR",
        "Auteurs copubliants": "Auteurs_copubliants",
        "Organisme copubliant": "Organisme_copubliant",
        "UE/Non UE": "UE/Non_UE",
        "ID Aurehal": "ID_Aurehal",

        # variantes d'encodage cassé
        "Ann�e": "Année",
        "Domaines consolid�s": "Domaines consolidés",
    }
    df = df.rename(columns=rename_map)

    # Debug (tu peux supprimer ensuite)
    print("COLUMNS:", [repr(c) for c in df.columns.tolist()])

    # -------- Nettoyage des VALEURS texte (strip) --------
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype(str).str.strip()

    # -------- Latitude / Longitude : virgule -> point --------
    for col in ["Latitude", "Longitude"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .replace({"": None, "nan": None, "None": None})
            )

    # -------- Conversions numériques sécurisées --------
    for col in ["Année", "Latitude", "Longitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Debug utile pour tes cartes (tu peux supprimer ensuite)
    if "Latitude" in df.columns and "Longitude" in df.columns:
        nb_geo = len(df[["Latitude", "Longitude"]].dropna())
        print("NB lignes avec coords:", nb_geo)

    return df


# ---------------- Filtrage ----------------
def filter_df(df, centres, equipes, pays, villes, organismes, annees):
    dff = df.copy()

    if centres and "Centre" in dff.columns:
        dff = dff[dff["Centre"].isin(centres)]
    if equipes and "Equipe" in dff.columns:
        dff = dff[dff["Equipe"].isin(equipes)]
    if pays and "Pays" in dff.columns:
        dff = dff[dff["Pays"].isin(pays)]
    if villes and "Ville" in dff.columns:
        dff = dff[dff["Ville"].isin(villes)]
    if organismes and "Organisme_copubliant" in dff.columns:
        dff = dff[dff["Organisme_copubliant"].isin(organismes)]
    if annees and "Année" in dff.columns:
        dff = dff[dff["Année"].isin(annees)]

    return dff
