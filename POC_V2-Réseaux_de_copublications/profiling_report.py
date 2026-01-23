import pandas as pd
from pathlib import Path


CSV_PATH = Path(
    r"C:\Users\abapst\nb_python\copublication_italie\ITALIE\plotly2\Copublis_Internationales_Inria_nov_2025_complet.csv"
)


def load_csv_safely(path: Path) -> pd.DataFrame:
    print(f"🔍 Lecture du fichier : {path}")
    try:
        df = pd.read_csv(
            path,
            encoding="utf-8",
            sep=",",
            engine="python",
            on_bad_lines="skip",
        )
        print("✅ Chargé en UTF-8")
    except Exception as e:
        print(f"⚠️ Échec UTF-8 : {e}\n➡️ tentative avec latin-1…")
        df = pd.read_csv(
            path,
            encoding="latin1",
            sep=",",
            engine="python",
            on_bad_lines="skip",
        )
        print("✅ Chargé en latin-1")

    return df


def profile_dataframe(df: pd.DataFrame) -> None:
    print("\n=========== 1. APERÇU GÉNÉRAL ===========")
    print(f"Lignes : {df.shape[0]:,}")
    print(f"Colonnes : {df.shape[1]}")
    print("\nColonnes :")
    print(list(df.columns))

    print("\nTypes :")
    print(df.dtypes)

    print("\nMémoire utilisée :")
    print(df.memory_usage(deep=True).sum() / 1024**2, "Mo")

    print("\n=========== 2. VALEURS MANQUANTES (%) ===========")
    missing = df.isna().mean().sort_values(ascending=False) * 100
    print(missing.round(2))

    print("\n=========== 3. APERÇU DES VALEURS ===========")
    for col in df.columns:
        print(f"\n--- {col} ---")
        print("  Type :", df[col].dtype)
        print("  Nb valeurs uniques :", df[col].nunique())
        print("  Aperçu :", df[col].dropna().unique()[:5])

    print("\n=========== 4. DOUBLONS ===========")
    full_dups = df.duplicated().sum()
    print(f"Doublons exacts (toutes colonnes) : {full_dups}")

    if "HalID" in df.columns:
        hal_dups = df["HalID"].duplicated().sum()
        print(f"Doublons sur HalID : {hal_dups}")
    else:
        print("⚠️ Colonne 'HalID' absente, impossible de tester les doublons sur HalID.")

    print("\n=========== 5. RANGES NUMÉRIQUES ===========")
    num_cols = df.select_dtypes(include=["number"]).columns
    for col in num_cols:
        print(f"\n--- {col} ---")
        print("  Min :", df[col].min())
        print("  Max :", df[col].max())

    print("\n=========== 6. SUGGESTIONS D’OPTIMISATION ===========")
    suggestions = []

    # Colonnes candidates au type category
    cat_candidates = [
        "Centre",
        "Equipe",
        "Ville",
        "Pays",
        "Organisme_copubliant",
        "UE/Non_UE",
    ]
    for c in cat_candidates:
        if c in df.columns:
            suggestions.append(f"→ Passer '{c}' en 'category' (beaucoup de répétitions).")

    # Colonnes textuelles très lourdes
    for col in ["Adresse", "Resume"]:
        if col in df.columns:
            suggestions.append(
                f"→ Colonne '{col}' très verbeuse : à exclure d’un dataset allégé pour le dashboard."
            )

    # Redondance structure / Centre
    if "Centre" in df.columns and "structure" in df.columns:
        if set(df["Centre"].dropna().unique()) == set(df["structure"].dropna().unique()):
            suggestions.append("→ 'structure' semble dupliquer 'Centre' : colonne redondante.")

    if "Latitude" in df.columns and "Longitude" in df.columns and "Ville" in df.columns:
        # Ville connue mais coords manquantes
        mask = df["Ville"].notna() & (df["Latitude"].isna() | df["Longitude"].isna())
        nb_geocode = mask.sum()
        if nb_geocode > 0:
            suggestions.append(
                f"→ {nb_geocode} lignes ont une Ville mais pas de Latitude/Longitude : candidates pour géocodage."
            )

    if suggestions:
        for s in suggestions:
            print(s)
    else:
        print("Aucune suggestion particulière détectée.")

    print("\n=========== 7. CONSEIL DASH ===========")
    print(
        "Pour de meilleures performances Dash :\n"
        "  1) Nettoyer le CSV puis le sauvegarder en Parquet (.parquet)\n"
        "  2) Convertir les colonnes catégorielles en 'category'\n"
        "  3) Pré-calculer certains groupby si besoin."
    )


def main():
    df = load_csv_safely(CSV_PATH)

    # Nettoyage léger typé
    for col in ["Année", "Latitude", "Longitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    profile_dataframe(df)


if __name__ == "__main__":
    main()
