import pandas as pd
import sqlite3
import logging
from pathlib import Path

# ==============================================================================
# Configuration
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# Chemins
BASE          = Path(r"C:\Users\NIAMBELE Siata\Desktop\MSPR2")
RAW_ELECTORAL = BASE / "01_raw" / "electoral"
RAW_SOCIO     = BASE / "01_raw" / "socioeco"
RAW_SSMSI     = RAW_SOCIO / "ssmsi"
STAGING_ELEC  = BASE / "02_staging" / "electoral"
STAGING_SOCIO = BASE / "02_staging" / "socioeco"
DB_PATH       = BASE / "03_database" / "mspr2.db"

# Handler fichier log
log_path = BASE / "pipeline.log"
file_handler = logging.FileHandler(log_path, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
logging.getLogger().addHandler(file_handler)
log.info(f"Log fichier : {log_path}")

# Constantes
CODE_DEPT_RHONE  = "69"
ANNEES_SECURITE  = [2017, 2022, 2024]

ELECTIONS_CIBLES = [
    "2014_euro_t1",
    "2019_euro_t1",
    "2024_euro_t1",
    "2017_legi_t1",
    "2022_legi_t1",
    "2024_legi_t1",
    "2017_pres_t1",
    "2022_pres_t1",
]

MAPPING_NUANCES = {
    "EXG"  : ("Extreme gauche",                        "Extreme gauche"),
    "LEXG" : ("Extreme gauche",                        "Extreme gauche"),
    "DXG"  : ("Divers extreme gauche",                 "Extreme gauche"),
    "COM"  : ("Parti Communiste Francais",             "Gauche radicale"),
    "LCOM" : ("Parti Communiste Francais",             "Gauche radicale"),
    "FI"   : ("La France Insoumise",                   "Gauche radicale"),
    "LFI"  : ("La France Insoumise",                   "Gauche radicale"),
    "LFG"  : ("Front de Gauche / NUPES",               "Gauche radicale"),
    "NUP"  : ("NUPES",                                 "Gauche radicale"),
    "DVG"  : ("Divers gauche",                         "Gauche"),
    "LDVG" : ("Divers gauche",                         "Gauche"),
    "UG"   : ("Union de la gauche",                    "Gauche"),
    "LUG"  : ("Union de la gauche",                    "Gauche"),
    "RDG"  : ("Rassemblement de la gauche",            "Gauche"),
    "SOC"  : ("Parti Socialiste",                      "Gauche"),
    "LSOC" : ("Parti Socialiste",                      "Gauche"),
    "ECO"  : ("Europe Ecologie Les Verts",             "Ecologie"),
    "LECO" : ("Europe Ecologie Les Verts",             "Ecologie"),
    "ENS"  : ("Ensemble (Renaissance / LREM)",         "Centre"),
    "LENS" : ("Ensemble (Renaissance / LREM)",         "Centre"),
    "REM"  : ("La Republique En Marche",               "Centre"),
    "DSV"  : ("Divers centre",                         "Centre"),
    "MDM"  : ("Mouvement Democrate",                   "Centre"),
    "UDI"  : ("Union des Democrates et Independants",  "Centre"),
    "LUC"  : ("Union du centre",                       "Centre"),
    "DIV"  : ("Divers",                                "Divers"),
    "LDIV" : ("Divers",                                "Divers"),
    "DVD"  : ("Divers droite",                         "Droite"),
    "LDVD" : ("Divers droite",                         "Droite"),
    "DVC"  : ("Divers droite",                         "Droite"),
    "LR"   : ("Les Republicains",                      "Droite"),
    "LLR"  : ("Les Republicains",                      "Droite"),
    "UMP"  : ("Union pour un Mouvement Populaire",     "Droite"),
    "LUMP" : ("Union pour un Mouvement Populaire",     "Droite"),
    "DLF"  : ("Debout la France",                      "Droite souverainiste"),
    "LDLF" : ("Debout la France",                      "Droite souverainiste"),
    "FN"   : ("Rassemblement National",                "Extreme droite"),
    "LFN"  : ("Rassemblement National",                "Extreme droite"),
    "RN"   : ("Rassemblement National",                "Extreme droite"),
    "LRN"  : ("Rassemblement National",                "Extreme droite"),
    "REC"  : ("Reconquete",                            "Extreme droite"),
    "LREC" : ("Reconquete",                            "Extreme droite"),
    "EXD"  : ("Extreme droite",                        "Extreme droite"),
    "LEXD" : ("Extreme droite",                        "Extreme droite"),
    "UXD"  : ("Union de l extreme droite",             "Extreme droite"),
    "LVEC" : ("Divers extreme droite",                 "Extreme droite"),
    "REG"  : ("Regionaliste",                          "Divers"),
    "LREG" : ("Regionaliste",                          "Divers"),
}

MAPPING_CANDIDATS_PRES = {
    "ARTHAUD"       : ("EXG", "Lutte Ouvriere",                "Extreme gauche"),
    "POUTOU"        : ("EXG", "Nouveau Parti Anticapitaliste", "Extreme gauche"),
    "MÉLENCHON"     : ("FI",  "La France Insoumise",          "Gauche radicale"),
    "MELENCHON"     : ("FI",  "La France Insoumise",          "Gauche radicale"),
    "HAMON"         : ("SOC", "Parti Socialiste",             "Gauche"),
    "MACRON"        : ("ENS", "En Marche / Renaissance",      "Centre"),
    "FILLON"        : ("LR",  "Les Republicains",             "Droite"),
    "DUPONT-AIGNAN" : ("DLF", "Debout la France",             "Droite souverainiste"),
    "LEPEN"         : ("RN",  "Rassemblement National",       "Extreme droite"),
    "LE PEN"        : ("RN",  "Rassemblement National",       "Extreme droite"),
    "ASSELINEAU"    : ("EXD", "Union Populaire Republicaine", "Droite souverainiste"),
    "CHEMINADE"     : ("DIV", "Solidarite et Progres",        "Divers"),
    "LASSALLE"      : ("DIV", "Resistons",                    "Divers"),
    "ROUSSEL"       : ("COM", "Parti Communiste Francais",    "Gauche radicale"),
    "JADOT"         : ("ECO", "Europe Ecologie Les Verts",    "Ecologie"),
    "HIDALGO"       : ("SOC", "Parti Socialiste",             "Gauche"),
    "PECRESSE"      : ("LR",  "Les Republicains",             "Droite"),
    "PÉCRESSE"      : ("LR",  "Les Republicains",             "Droite"),
    "ZEMMOUR"       : ("EXD", "Reconquete",                   "Extreme droite"),
    "TAUBIRA"       : ("DVG", "Divers gauche",                "Gauche"),
}

MAPPING_LISTES_2019 = {
    "LUTTE OUVRIÈRE"              : ("LEXG", "Lutte Ouvriere",                "Extreme gauche"),
    "RÉVOLUTIONNAIRE"             : ("LEXG", "Extreme gauche",                "Extreme gauche"),
    "LA FRANCE INSOUMISE"         : ("LFI",  "La France Insoumise",           "Gauche radicale"),
    "POUR L'EUROPE DES GENS"      : ("LFG",  "Front de Gauche / NUPES",       "Gauche radicale"),
    "EUROPE AU SERVICE PEUPLES"   : ("LFG",  "Front de Gauche / NUPES",       "Gauche radicale"),
    "ENVIE D'EUROPE"              : ("LSOC", "Parti Socialiste",              "Gauche"),
    "À VOIX ÉGALES"               : ("LDVG", "Divers gauche",                 "Gauche"),
    "PRENEZ LE POUVOIR"           : ("LDVG", "Divers gauche",                 "Gauche"),
    "LISTE CITOYENNE"             : ("LDVG", "Divers gauche",                 "Gauche"),
    "INITIATIVE CITOYENNE"        : ("LDVG", "Divers gauche",                 "Gauche"),
    "EUROPE ÉCOLOGIE"             : ("LECO", "Europe Ecologie Les Verts",     "Ecologie"),
    "URGENCE ÉCOLOGIE"            : ("LECO", "Europe Ecologie Les Verts",     "Ecologie"),
    "DÉCROISSANCE 2019"           : ("LECO", "Decroissance",                  "Ecologie"),
    "PARTI ANIMALISTE"            : ("LECO", "Parti Animaliste",              "Ecologie"),
    "RENAISSANCE"                 : ("LENS", "Ensemble (Renaissance / LREM)", "Centre"),
    "LES EUROPÉENS"               : ("LENS", "Ensemble (Renaissance / LREM)", "Centre"),
    "PARTI FED. EUROPÉEN"         : ("LDIV", "Divers",                        "Divers"),
    "ÉVOLUTION CITOYENNE"         : ("LDIV", "Divers",                        "Divers"),
    "NEUTRE ET ACTIF"             : ("LDIV", "Divers",                        "Divers"),
    "DÉMOCRATIE REPRÉSENTATIVE"   : ("LDIV", "Divers",                        "Divers"),
    "ESPERANTO"                   : ("LDIV", "Divers",                        "Divers"),
    "PACE"                        : ("LDIV", "Divers",                        "Divers"),
    "ALLONS ENFANTS"              : ("LDIV", "Divers",                        "Divers"),
    "ALLIANCE JAUNE"              : ("LDIV", "Gilets Jaunes",                 "Divers"),
    "LES OUBLIES DE L'EUROPE"     : ("LDIV", "Divers",                        "Divers"),
    "PARTI PIRATE"                : ("LDIV", "Divers",                        "Divers"),
    "UNION DROITE-CENTRE"         : ("LDVD", "Divers droite",                 "Droite"),
    "UDLEF"                       : ("LDVD", "Divers droite",                 "Droite"),
    "DEBOUT LA FRANCE"            : ("LDLF", "Debout la France",              "Droite souverainiste"),
    "ENSEMBLE POUR LE FREXIT"     : ("LDLF", "Souverainiste",                 "Droite souverainiste"),
    "ENSEMBLE PATRIOTES"          : ("LDLF", "Patriotes",                     "Droite souverainiste"),
    "LISTE DE LA RECONQUÊTE"      : ("LREC", "Reconquete",                    "Extreme droite"),
    "UNE FRANCE ROYALE"           : ("LEXD", "Extreme droite",                "Extreme droite"),
    "LA LIGNE CLAIRE"             : ("LEXD", "Extreme droite",                "Extreme droite"),
}

FICHIERS_SECURITE = {
    "cambriolages"             : RAW_SSMSI / "ssmsi_cambriolages.csv",
    "destructions"             : RAW_SSMSI / "ssmsi_destructions.csv",
    "escroqueries"             : RAW_SSMSI / "ssmsi_escroqueries.csv",
    "trafic_stupefiants"       : RAW_SSMSI / "ssmsi_trafic_stupefiants.csv",
    "usage_stupefiants"        : RAW_SSMSI / "ssmsi_usage_stupefiants.csv",
    "violences_hors_famille"   : RAW_SSMSI / "ssmsi_violences_hors_famille.csv",
    "violences_intrafamiliales": RAW_SSMSI / "ssmsi_violences_intrafamiliales.csv",
    "violences_sexuelles"      : RAW_SSMSI / "ssmsi_violences_sexuelles.csv",
    "vols_accessoires"         : RAW_SSMSI / "ssmsi_vols_accessoires.csv",
    "vols_avec_armes"          : RAW_SSMSI / "ssmsi_vols_avec_armes.csv",
    "vols_dans_vehicules"      : RAW_SSMSI / "ssmsi_vols_dans_vehicules.csv",
    "vols_sans_armes"          : RAW_SSMSI / "ssmsi_vols_sans_armes.csv",
    "vols_sans_violence"       : RAW_SSMSI / "ssmsi_vols_sans_violence.csv",
    "vols_vehicule"            : RAW_SSMSI / "ssmsi_vols_vehicule.csv",
}

# Alignement temporel : election cible -> millesimes socioeco a utiliser
ALIGNEMENT_TEMPOREL = {
    "2017_legi_t1" : {"pop": "2016", "revenu": "2017", "immigration": "2017", "securite": 2017},
    "2017_pres_t1" : {"pop": "2016", "revenu": "2017", "immigration": "2017", "securite": 2017},
    "2022_legi_t1" : {"pop": "2022", "revenu": "2021", "immigration": "2022", "securite": 2022},
    "2022_pres_t1" : {"pop": "2022", "revenu": "2021", "immigration": "2022", "securite": 2022},
    "2024_legi_t1" : {"pop": "2022", "revenu": "2021", "immigration": "2022", "securite": 2024},
}

# Europeennes precedentes par election cible
EURO_PRECEDENTES = {
    "2017_legi_t1" : "2014_euro_t1",
    "2017_pres_t1" : "2014_euro_t1",
    "2022_legi_t1" : "2019_euro_t1",
    "2022_pres_t1" : "2019_euro_t1",
    "2024_legi_t1" : "2024_euro_t1",
}

FAMILLES_POLITIQUES = [
    "Extreme gauche",
    "Gauche radicale",
    "Gauche",
    "Ecologie",
    "Centre",
    "Droite",
    "Droite souverainiste",
    "Extreme droite",
    "Divers",
]


# ==============================================================================
# Fonctions utilitaires
# ==============================================================================

def sauvegarder_sqlite(tables: dict, db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    for nom_table, df in tables.items():
        df_sql = df.copy()
        for col in df_sql.select_dtypes(include="Int64").columns:
            df_sql[col] = df_sql[col].astype(object).where(df_sql[col].notna(), None)
        df_sql.to_sql(nom_table, conn, if_exists="replace", index=False)
        if "code_commune" in df_sql.columns:
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{nom_table}_com "
                f"ON {nom_table} (code_commune)"
            )
        if "id_election" in df_sql.columns:
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{nom_table}_elec "
                f"ON {nom_table} (id_election)"
            )
        log.info(f"  Table '{nom_table}' : {len(df_sql):,} lignes")
    conn.commit()
    conn.close()


def sauvegarder_csv(exports: dict, staging_dir: Path):
    staging_dir.mkdir(parents=True, exist_ok=True)
    for nom_fichier, df in exports.items():
        chemin = staging_dir / nom_fichier
        df.to_csv(chemin, index=False, sep=";", encoding="utf-8-sig")
        log.info(f"  CSV : {chemin.name}  ({len(df):,} lignes)")


def mapper_presidentielles(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    masque_pres = df["type_election"] == "pres"
    for nom_candidat, (nuance, parti, famille) in MAPPING_CANDIDATS_PRES.items():
        masque_nom = masque_pres & df["nom"].str.upper().str.contains(nom_candidat, na=False)
        df.loc[masque_nom, "nuance"]            = nuance
        df.loc[masque_nom, "parti_politique"]   = parti
        df.loc[masque_nom, "famille_politique"] = famille
    encore_vides = df[masque_pres & df["nuance"].isna()]["nom"].value_counts()
    if len(encore_vides) > 0:
        log.warning(f"Candidats presidentiels sans nuance :\n{encore_vides.to_string()}")
    else:
        log.info("Toutes les nuances presidentielles sont renseignees.")
    return df


def mapper_listes_2019(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    masque_2019 = df["id_election"] == "2019_euro_t1"
    for nom_liste, (nuance, parti, famille) in MAPPING_LISTES_2019.items():
        masque_liste = masque_2019 & (df["nom"] == nom_liste)
        df.loc[masque_liste, "nuance"]            = nuance
        df.loc[masque_liste, "parti_politique"]   = parti
        df.loc[masque_liste, "famille_politique"] = famille
    encore_vides = df[masque_2019 & df["nuance"].isna()]["nom"].value_counts()
    if len(encore_vides) > 0:
        log.warning(f"Listes 2019 sans mapping :\n{encore_vides.to_string()}")
    else:
        log.info("Toutes les listes 2019 sont mappees.")
    return df


def imputer_mediane(df: pd.DataFrame, label: str) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if col == "code_commune":
            continue
        nb_nan = df[col].isna().sum()
        if nb_nan > 0:
            mediane = df[col].median()
            df[col] = df[col].fillna(mediane)
            log.info(f"  {label} | {col:<35} {nb_nan:>3} NaN imputes | mediane = {mediane:.2f}")
    return df


# ==============================================================================
# ETL Electoral
# ==============================================================================

def etl_electoral():
    log.info("=" * 60)
    log.info("DEBUT ETL ELECTORAL")
    log.info("=" * 60)

    # Chargement
    log.info("Chargement general_results.csv...")
    df_general = pd.read_csv(
        RAW_ELECTORAL / "general_results.csv",
        sep=";", dtype=str, low_memory=False, encoding="utf-8"
    )
    log.info(f"general_results : {len(df_general):,} lignes")

    log.info("Chargement candidats_results.csv...")
    df_candidats = pd.read_csv(
        RAW_ELECTORAL / "candidats_results.csv",
        sep=";", dtype=str, low_memory=False, encoding="utf-8"
    )
    log.info(f"candidats_results : {len(df_candidats):,} lignes")

    # Filtrage Rhone + elections cibles
    masque_g = (
        (df_general["code_departement"] == CODE_DEPT_RHONE) &
        (df_general["id_election"].isin(ELECTIONS_CIBLES))
    )
    df_general_rhone = df_general[masque_g].copy()

    masque_c = (
        (df_candidats["code_departement"] == CODE_DEPT_RHONE) &
        (df_candidats["id_election"].isin(ELECTIONS_CIBLES))
    )
    df_candidats_rhone = df_candidats[masque_c].copy()
    log.info(f"general filtre : {len(df_general_rhone):,} lignes")
    log.info(f"candidats filtre : {len(df_candidats_rhone):,} lignes")

    # Nettoyage general
    cols_entiers = ["inscrits", "abstentions", "votants", "blancs", "nuls", "exprimes"]
    cols_ratios  = [
        "ratio_abstentions_inscrits", "ratio_votants_inscrits",
        "ratio_blancs_inscrits", "ratio_blancs_votants",
        "ratio_nuls_inscrits", "ratio_nuls_votants",
        "ratio_exprimes_inscrits", "ratio_exprimes_votants"
    ]
    for col in cols_entiers:
        df_general_rhone[col] = pd.to_numeric(
            df_general_rhone[col], errors="coerce"
        ).astype("Int64")
    for col in cols_ratios:
        df_general_rhone[col] = pd.to_numeric(df_general_rhone[col], errors="coerce")

    df_general_rhone = df_general_rhone[
        df_general_rhone["inscrits"].notna() & (df_general_rhone["inscrits"] > 0)
    ].copy()

    df_general_rhone["libelle_departement"] = df_general_rhone["libelle_departement"].str.strip()
    df_general_rhone["libelle_commune"]     = df_general_rhone["libelle_commune"].str.strip()
    df_general_rhone["annee"]              = df_general_rhone["id_election"].str[:4].astype("Int64")
    df_general_rhone["type_election"]      = df_general_rhone["id_election"].str.extract(r"^\d{4}_([a-z]+)_")
    df_general_rhone["tour"]               = df_general_rhone["id_election"].str.extract(r"_t(\d)$").astype("Int64")
    df_general_rhone["taux_participation"] = (
        df_general_rhone["votants"] / df_general_rhone["inscrits"] * 100
    ).round(2)

    # Nettoyage candidats
    df_candidats_rhone["voix"] = pd.to_numeric(
        df_candidats_rhone["voix"], errors="coerce"
    ).astype("Int64")
    df_candidats_rhone["ratio_voix_inscrits"] = pd.to_numeric(
        df_candidats_rhone["ratio_voix_inscrits"], errors="coerce"
    )
    df_candidats_rhone["ratio_voix_exprimes"] = pd.to_numeric(
        df_candidats_rhone["ratio_voix_exprimes"], errors="coerce"
    )

    for col in ["nuance", "sexe", "nom", "prenom", "liste",
                "libelle_abrege_liste", "libelle_etendu_liste",
                "nom_tete_liste", "binome"]:
        if col in df_candidats_rhone.columns:
            df_candidats_rhone[col] = df_candidats_rhone[col].str.strip()

    df_candidats_rhone["nom"]           = df_candidats_rhone["nom"].str.upper()
    df_candidats_rhone["annee"]         = df_candidats_rhone["id_election"].str[:4].astype("Int64")
    df_candidats_rhone["type_election"] = df_candidats_rhone["id_election"].str.extract(r"^\d{4}_([a-z]+)_")
    df_candidats_rhone["tour"]          = df_candidats_rhone["id_election"].str.extract(r"_t(\d)$").astype("Int64")

    # Mapping nuances
    df_candidats_rhone["parti_politique"] = df_candidats_rhone["nuance"].map(
        {k: v[0] for k, v in MAPPING_NUANCES.items()}
    ).fillna("Inconnu")
    df_candidats_rhone["famille_politique"] = df_candidats_rhone["nuance"].map(
        {k: v[1] for k, v in MAPPING_NUANCES.items()}
    ).fillna("Inconnu")

    df_candidats_rhone = mapper_presidentielles(df_candidats_rhone)
    df_candidats_rhone = mapper_listes_2019(df_candidats_rhone)

    # Remplir nom avec libelle_abrege_liste pour europeennes sans nom individuel
    masque_euro_sans_nom = (
        (df_candidats_rhone["type_election"] == "euro") &
        (df_candidats_rhone["nom"].isna())
    )
    df_candidats_rhone.loc[masque_euro_sans_nom, "nom"] = (
        df_candidats_rhone.loc[masque_euro_sans_nom, "libelle_abrege_liste"]
    )

    # Suppression colonnes inutiles general
    for col in ["code_canton", "libelle_canton", "blancs",
                "ratio_blancs_inscrits", "ratio_blancs_votants", "taux_blancs_inscrits"]:
        if col in df_general_rhone.columns:
            df_general_rhone = df_general_rhone.drop(columns=[col])

    masque_euro = df_general_rhone["type_election"] == "euro"
    for col in ["code_circonscription", "libelle_circonscription"]:
        if col in df_general_rhone.columns:
            df_general_rhone.loc[masque_euro, col] = None

    for col in ["ratio_nuls_votants", "ratio_exprimes_votants"]:
        if col in df_general_rhone.columns:
            df_general_rhone[col] = df_general_rhone[col].fillna(0)

    # Agregation general communes
    cles_gen   = ["id_election", "annee", "type_election", "tour",
                  "code_departement", "libelle_departement",
                  "code_commune", "libelle_commune"]
    cols_somme = ["inscrits", "abstentions", "votants", "nuls", "exprimes"]

    df_general_communes = (
        df_general_rhone.groupby(cles_gen, dropna=False)[cols_somme]
        .sum(min_count=1).reset_index()
    )
    df_general_communes["taux_participation"]     = (df_general_communes["votants"]     / df_general_communes["inscrits"] * 100).round(2)
    df_general_communes["taux_abstention"]        = (df_general_communes["abstentions"] / df_general_communes["inscrits"] * 100).round(2)
    df_general_communes["taux_nuls_inscrits"]     = (df_general_communes["nuls"]        / df_general_communes["inscrits"] * 100).round(2)
    df_general_communes["taux_exprimes_inscrits"] = (df_general_communes["exprimes"]    / df_general_communes["inscrits"] * 100).round(2)

    # Agregation candidats communes
    cles_cand = ["id_election", "annee", "type_election", "tour",
                 "code_departement", "code_commune", "no_panneau",
                 "nuance", "parti_politique", "famille_politique",
                 "nom", "libelle_abrege_liste"]

    df_candidats_communes = (
        df_candidats_rhone.groupby(cles_cand, dropna=False)["voix"]
        .sum(min_count=1).reset_index()
    )

    totaux = df_general_communes[["id_election", "code_commune", "inscrits", "exprimes"]].copy()
    df_candidats_communes = df_candidats_communes.merge(
        totaux, on=["id_election", "code_commune"], how="left"
    )
    df_candidats_communes["ratio_voix_inscrits"] = (
        df_candidats_communes["voix"] / df_candidats_communes["inscrits"] * 100
    ).round(2)
    df_candidats_communes["ratio_voix_exprimes"] = (
        df_candidats_communes["voix"] / df_candidats_communes["exprimes"] * 100
    ).round(2)
    df_candidats_communes = df_candidats_communes.drop(columns=["inscrits", "exprimes"])

    # Remplir nom europeennes dans communes
    masque_euro_sans_nom_com = (
        (df_candidats_communes["type_election"] == "euro") &
        (df_candidats_communes["nom"].isna())
    )
    df_candidats_communes.loc[masque_euro_sans_nom_com, "nom"] = (
        df_candidats_communes.loc[masque_euro_sans_nom_com, "libelle_abrege_liste"]
    )
    df_candidats_communes = mapper_listes_2019(df_candidats_communes)

    libelles = df_general_communes[["code_commune", "libelle_commune"]].drop_duplicates()
    df_candidats_communes = df_candidats_communes.merge(
        libelles, on="code_commune", how="left"
    )

    # Table export finale
    COLS_FINALES = [
        "id_election", "annee", "type_election", "tour",
        "code_commune", "libelle_commune", "nom",
        "nuance", "parti_politique", "famille_politique",
        "voix", "ratio_voix_inscrits", "ratio_voix_exprimes",
    ]
    df_export = (
        df_candidats_communes[COLS_FINALES]
        .sort_values(["id_election", "code_commune", "nom"])
        .reset_index(drop=True)
    )

    # Sauvegarde CSV
    log.info("Sauvegarde electoral CSV...")
    export_dir = STAGING_ELEC / "par_election"
    export_dir.mkdir(parents=True, exist_ok=True)

    sauvegarder_csv({
        "rhone_general_bureaux.csv"    : df_general_rhone,
        "rhone_general_communes.csv"   : df_general_communes,
        "rhone_candidats_bureaux.csv"  : df_candidats_rhone,
        "rhone_candidats_communes.csv" : df_candidats_communes,
        "rhone_export_final.csv"       : df_export,
    }, STAGING_ELEC)

    for id_election in sorted(df_export["id_election"].unique()):
        df_slice = df_export[df_export["id_election"] == id_election].copy()
        df_slice.to_csv(
            export_dir / f"rhone_{id_election}.csv",
            index=False, sep=";", encoding="utf-8-sig"
        )
        log.info(f"  rhone_{id_election}.csv ({len(df_slice):,} lignes)")

    # Sauvegarde SQLite
    log.info("Sauvegarde electoral SQLite...")
    sauvegarder_sqlite({
        "general_bureaux"    : df_general_rhone,
        "general_communes"   : df_general_communes,
        "candidats_bureaux"  : df_candidats_rhone,
        "candidats_communes" : df_candidats_communes,
        "export_final"       : df_export,
    }, DB_PATH)

    log.info("ETL ELECTORAL TERMINE")
    return df_general_communes, df_export, df_candidats_communes


# ==============================================================================
# ETL Socioeconomique
# ==============================================================================

def etl_socioeco():
    log.info("=" * 60)
    log.info("DEBUT ETL SOCIOECONOMIQUE")
    log.info("=" * 60)

    # Securite
    log.info("Chargement fichiers securite...")
    morceaux = []
    for type_delit, chemin in FICHIERS_SECURITE.items():
        df = pd.read_csv(chemin, dtype={"Code commune": str})
        masque = (
            df["Code commune"].str.startswith(CODE_DEPT_RHONE) &
            df["Année"].isin(ANNEES_SECURITE)
        )
        df = df[masque].copy()
        nb_na = df["Nombre diffusé"].isna().sum()
        df["Nombre diffusé"] = df["Nombre diffusé"].fillna(0)
        df = df.rename(columns={
            "Code commune"  : "code_commune",
            "Nom commune"   : "libelle_commune",
            "Année"         : "annee",
            "Nombre diffusé": "nombre",
        })[["code_commune", "libelle_commune", "annee", "nombre"]]
        df["type_delit"] = type_delit
        morceaux.append(df)
        log.info(f"  {type_delit:<30} {len(df):>5} lignes | {nb_na} NA remplaces par 0")

    df_securite = (
        pd.concat(morceaux, ignore_index=True)
        .groupby(["code_commune", "libelle_commune", "annee"])["nombre"]
        .sum().reset_index()
        .rename(columns={"nombre": "total_delits"})
    )
    df_securite["annee"] = df_securite["annee"].astype(int)
    log.info(f"Securite : {len(df_securite):,} lignes")

    # Population avec millesimes 2016 et 2022
    log.info("Chargement population...")
    df_pop_raw = pd.read_csv(
        RAW_SOCIO / "population.CSV",
        sep=";", dtype={"CODGEO": str}, low_memory=False
    )
    df_pop_raw = df_pop_raw[df_pop_raw["CODGEO"].str.startswith(CODE_DEPT_RHONE)].copy()
    cols_pop = {
        "CODGEO"    : "code_commune",
        "P22_POP"   : "population_2022",
        "P16_POP"   : "population_2016",
        "P22_LOG"   : "nb_logements_2022",
        "P16_LOG"   : "nb_logements_2016",
        "P22_RP"    : "nb_residences_principales_2022",
        "P16_RP"    : "nb_residences_principales_2016",
        "P22_LOGVAC": "nb_logements_vacants_2022",
        "P16_LOGVAC": "nb_logements_vacants_2016",
        "SUPERF"    : "superficie_km2",
    }
    cols_pop_p = {k: v for k, v in cols_pop.items() if k in df_pop_raw.columns}
    df_pop = df_pop_raw[list(cols_pop_p.keys())].rename(columns=cols_pop_p).copy()
    for col in df_pop.columns[1:]:
        df_pop[col] = pd.to_numeric(df_pop[col], errors="coerce")
    df_pop["densite_2022"] = (df_pop["population_2022"] / df_pop["superficie_km2"]).round(2)
    df_pop["densite_2016"] = (df_pop["population_2016"] / df_pop["superficie_km2"]).round(2)
    log.info(f"Population : {len(df_pop):,} communes")

    # Emploi
    log.info("Chargement emploi...")
    df_emploi_raw = pd.read_csv(
        RAW_SOCIO / "base-cc-emploi-pop-active-2022.CSV",
        sep=";", dtype={"CODGEO": str}, low_memory=False
    )
    df_emploi_raw = df_emploi_raw[
        df_emploi_raw["CODGEO"].str.startswith(CODE_DEPT_RHONE)
    ].copy()
    cols_emp = {
        "CODGEO"         : "code_commune",
        "P22_ACT1564"    : "actifs_2022",
        "P22_CHOM1564"   : "chomeurs_2022",
        "P22_ACTOCC1564" : "actifs_occupes_2022",
        "P22_INACT1564"  : "inactifs_2022",
    }
    cols_emp_p = {k: v for k, v in cols_emp.items() if k in df_emploi_raw.columns}
    df_emploi = df_emploi_raw[list(cols_emp_p.keys())].rename(columns=cols_emp_p).copy()
    for col in df_emploi.columns[1:]:
        df_emploi[col] = pd.to_numeric(df_emploi[col], errors="coerce")
    df_emploi["taux_chomage_2022"] = (
        df_emploi["chomeurs_2022"] / df_emploi["actifs_2022"] * 100
    ).round(2)
    log.info(f"Emploi : {len(df_emploi):,} communes")

    # Revenus 2017
    log.info("Chargement revenus 2017...")
    df_filo17_raw = pd.read_csv(
        RAW_SOCIO / "cc_filosofi_2017_COM.CSV",
        sep=";", dtype={"CODGEO": str}, low_memory=False
    )
    df_filo17_raw = df_filo17_raw[
        df_filo17_raw["CODGEO"].str.startswith(CODE_DEPT_RHONE)
    ].copy()
    cols_f17 = {
        "CODGEO" : "code_commune",
        "MED17"  : "revenu_median_2017",
        "TP6017" : "taux_pauvrete_2017",
        "PCHO17" : "part_chomeurs_2017",
        "PIMP17" : "part_foyers_imposes_2017",
        "D117"   : "d1_revenu_2017",
        "D917"   : "d9_revenu_2017",
        "RD17"   : "ratio_interdecile_2017",
    }
    cols_f17_p = {k: v for k, v in cols_f17.items() if k in df_filo17_raw.columns}
    df_filo17 = df_filo17_raw[list(cols_f17_p.keys())].rename(columns=cols_f17_p).copy()
    for col in df_filo17.columns[1:]:
        df_filo17[col] = pd.to_numeric(df_filo17[col], errors="coerce")
    df_filo17 = imputer_mediane(df_filo17, "revenus_2017")
    log.info(f"Revenus 2017 : {len(df_filo17):,} communes")

    # Revenus 2021
    log.info("Chargement revenus 2021...")
    df_filo21_raw = pd.read_excel(
        RAW_SOCIO / "FILO2021_DISP_COM.xlsx",
        sheet_name="ENSEMBLE", engine="calamine",
        header=5, dtype=str
    )
    df_filo21_raw = df_filo21_raw[
        df_filo21_raw["CODGEO"].astype(str).str.startswith(CODE_DEPT_RHONE)
    ].copy()
    
    cols_f21 = {
    "CODGEO"   : "code_commune",
    "Q221"     : "revenu_median_2021",
    "D121"     : "d1_revenu_2021",
    "D921"     : "d9_revenu_2021",
    "RD"       : "ratio_interdecile_2021",   # ← nom sans millésime dans le fichier
    "PCHO21"   : "part_chomeurs_2021",
    "PIMPOT21" : "part_foyers_imposes_2021", # ← PIMPOT et non PIMP
    "NBMEN21"  : "nb_menages_2021",
    "NBPERS21" : "nb_personnes_menages_2021",
}
    cols_f21_p = {k: v for k, v in cols_f21.items() if k in df_filo21_raw.columns}
    df_filo21 = df_filo21_raw[list(cols_f21_p.keys())].rename(columns=cols_f21_p).copy()
    for col in df_filo21.columns[1:]:
        df_filo21[col] = pd.to_numeric(
            df_filo21[col].astype(str).str.replace(",", ".").str.strip().replace(
                "s", float("nan")
            ),
            errors="coerce"
        )
    df_filo21 = imputer_mediane(df_filo21, "revenus_2021")
    log.info(f"Revenus 2021 : {len(df_filo21):,} communes")

    # Immigration 2017
    log.info("Chargement immigration 2017...")
    df_imm17_raw = pd.read_csv(
        RAW_SOCIO / "BTT_TD_IMG1A_2017.CSV",
        sep=";", dtype=str, low_memory=False
    )
    df_imm17_raw = df_imm17_raw[
        (df_imm17_raw["NIVGEO"] == "COM") &
        (df_imm17_raw["CODGEO"].str.startswith(CODE_DEPT_RHONE))
    ].copy()
    df_imm17_raw["NB"] = pd.to_numeric(df_imm17_raw["NB"], errors="coerce").fillna(0)
    df_imm17 = (
        df_imm17_raw.groupby(["CODGEO", "IMMI"])["NB"]
        .sum().reset_index()
        .pivot(index="CODGEO", columns="IMMI", values="NB")
        .reset_index()
    )
    df_imm17.columns.name = None
    df_imm17 = df_imm17.rename(columns={
        "CODGEO": "code_commune",
        "1"     : "nb_immigres_2017",
        "2"     : "nb_non_immigres_2017",
    })
    df_imm17["nb_immigres_2017"]     = df_imm17["nb_immigres_2017"].round(0).astype("Int64")
    df_imm17["nb_non_immigres_2017"] = df_imm17["nb_non_immigres_2017"].round(0).astype("Int64")
    log.info(f"Immigration 2017 : {len(df_imm17):,} communes")

    # Immigration 2022
    log.info("Chargement immigration 2022...")
    df_imm22_raw = pd.read_excel(
        RAW_SOCIO / "TD_IMG1A_2022.xlsx",
        sheet_name="COM", engine="calamine",
        header=10, dtype={"CODGEO": str}
    )
    df_imm22_raw = df_imm22_raw[
        df_imm22_raw["CODGEO"].str.startswith(CODE_DEPT_RHONE)
    ].copy()
    cols_immi1 = [c for c in df_imm22_raw.columns if "IMMI1" in str(c)]
    cols_immi2 = [c for c in df_imm22_raw.columns if "IMMI2" in str(c)]
    for col in cols_immi1 + cols_immi2:
        df_imm22_raw[col] = pd.to_numeric(df_imm22_raw[col], errors="coerce").fillna(0)
    df_imm22 = pd.DataFrame({
        "code_commune"         : df_imm22_raw["CODGEO"],
        "nb_immigres_2022"     : df_imm22_raw[cols_immi1].sum(axis=1).round(0).astype("Int64"),
        "nb_non_immigres_2022" : df_imm22_raw[cols_immi2].sum(axis=1).round(0).astype("Int64"),
    })
    log.info(f"Immigration 2022 : {len(df_imm22):,} communes")

    # Sauvegarde CSV
    log.info("Sauvegarde socioeconomique CSV...")
    sauvegarder_csv({
        "rhone_securite.csv"        : df_securite,
        "rhone_population.csv"      : df_pop,
        "rhone_emploi.csv"          : df_emploi,
        "rhone_revenus_2017.csv"    : df_filo17,
        "rhone_revenus_2021.csv"    : df_filo21,
        "rhone_immigration_2017.csv": df_imm17,
        "rhone_immigration_2022.csv": df_imm22,
    }, STAGING_SOCIO)

    # Sauvegarde SQLite
    log.info("Sauvegarde socioeconomique SQLite...")
    sauvegarder_sqlite({
        "securite"        : df_securite,
        "population"      : df_pop,
        "emploi"          : df_emploi,
        "revenus_2017"    : df_filo17,
        "revenus_2021"    : df_filo21,
        "immigration_2017": df_imm17,
        "immigration_2022": df_imm22,
    }, DB_PATH)

    log.info("ETL SOCIOECONOMIQUE TERMINE")

    return (df_securite, df_pop, df_emploi,
            df_filo17, df_filo21, df_imm17, df_imm22)


# ==============================================================================
# Construction du master pour le ML
# ==============================================================================

def construire_master(
    df_general_communes, df_candidats_communes,
    df_securite, df_pop, df_emploi,
    df_filo17, df_filo21, df_imm17, df_imm22
):
    log.info("=" * 60)
    log.info("DEBUT CONSTRUCTION DU MASTER ML")
    log.info("=" * 60)

    elections_cibles = list(ALIGNEMENT_TEMPOREL.keys())
    morceaux_master  = []

    for id_election in elections_cibles:
        align    = ALIGNEMENT_TEMPOREL[id_election]
        id_euro  = EURO_PRECEDENTES[id_election]

        log.info(f"Construction master pour {id_election} (euro ref : {id_euro})...")

        # -- Variable cible : famille politique gagnante par commune
        df_elec = df_candidats_communes[
            df_candidats_communes["id_election"] == id_election
        ].copy()

        idx_max = df_elec.groupby("code_commune")["voix"].idxmax()
        df_cible = df_elec.loc[idx_max, ["code_commune", "libelle_commune",
                                          "famille_politique"]].copy()
        df_cible = df_cible.rename(columns={"famille_politique": "famille_gagnante"})

        # -- Features electorales : scores europeennes precedentes par famille
        df_euro = df_candidats_communes[
            df_candidats_communes["id_election"] == id_euro
        ].copy()

        # Score par famille et par commune (ratio des exprimes)
        df_euro_famille = (
            df_euro.groupby(["code_commune", "famille_politique"])["voix"]
            .sum().reset_index()
        )
        total_exprimes_euro = (
            df_euro.groupby("code_commune")["voix"]
            .sum().reset_index()
            .rename(columns={"voix": "total_voix_euro"})
        )
        df_euro_famille = df_euro_famille.merge(
            total_exprimes_euro, on="code_commune", how="left"
        )
        df_euro_famille["ratio"] = (
            df_euro_famille["voix"] / df_euro_famille["total_voix_euro"] * 100
        ).round(2)

        # Pivot : une colonne par famille
        df_euro_pivot = df_euro_famille.pivot_table(
            index="code_commune",
            columns="famille_politique",
            values="ratio",
            aggfunc="sum"
        ).reset_index()
        df_euro_pivot.columns.name = None

        # Renommer les colonnes avec prefixe euro_
        rename_euro = {}
        for famille in FAMILLES_POLITIQUES:
            col_clean = famille.lower().replace(" ", "_").replace("é", "e").replace("è", "e")
            rename_euro[famille] = f"euro_{col_clean}_ratio"
        df_euro_pivot = df_euro_pivot.rename(columns=rename_euro)

        # Famille gagnante aux europeennes
        idx_euro_max = df_euro.groupby("code_commune")["voix"].idxmax()
        df_euro_gagnant = df_euro.loc[
            idx_euro_max, ["code_commune", "famille_politique"]
        ].copy().rename(columns={"famille_politique": "euro_famille_gagnante"})

        # Taux de participation aux europeennes
        df_part_euro = df_general_communes[
            df_general_communes["id_election"] == id_euro
        ][["code_commune", "taux_participation"]].copy()
        df_part_euro = df_part_euro.rename(
            columns={"taux_participation": "euro_taux_participation"}
        )

        # -- Features socioeconomiques selon alignement temporel
        millesime_pop  = align["pop"]
        millesime_rev  = align["revenu"]
        millesime_imm  = align["immigration"]
        annee_securite = align["securite"]

        # Population
        cols_pop_millesime = [
            "code_commune",
            f"population_{millesime_pop}",
            f"nb_logements_{millesime_pop}",
            f"nb_residences_principales_{millesime_pop}",
            f"nb_logements_vacants_{millesime_pop}",
            f"densite_{millesime_pop}",
            "superficie_km2",
        ]
        cols_pop_dispo = [c for c in cols_pop_millesime if c in df_pop.columns]
        df_pop_slice = df_pop[cols_pop_dispo].copy()
        rename_pop = {c: c.replace(f"_{millesime_pop}", "") for c in cols_pop_dispo if c != "code_commune"}
        df_pop_slice = df_pop_slice.rename(columns=rename_pop)

        # Emploi (toujours 2022)
        df_emploi_slice = df_emploi.copy()

        # Revenus
        if millesime_rev == "2017":
            df_rev = df_filo17.copy()
            rename_rev = {c: c.replace("_2017", "") for c in df_rev.columns if c != "code_commune"}
        else:
            df_rev = df_filo21.copy()
            rename_rev = {c: c.replace("_2021", "") for c in df_rev.columns if c != "code_commune"}
        df_rev = df_rev.rename(columns=rename_rev)

        # Immigration
        if millesime_imm == "2017":
            df_imm = df_imm17.copy()
            rename_imm = {c: c.replace("_2017", "") for c in df_imm.columns if c != "code_commune"}
        else:
            df_imm = df_imm22.copy()
            rename_imm = {c: c.replace("_2022", "") for c in df_imm.columns if c != "code_commune"}
        df_imm = df_imm.rename(columns=rename_imm)

        # Securite
        df_sec = df_securite[
            df_securite["annee"] == annee_securite
        ][["code_commune", "total_delits"]].copy()

        # -- Assemblage du master pour cette election
        df_master_elec = df_cible.copy()
        df_master_elec["id_election"] = id_election
        df_master_elec["annee"]       = int(id_election[:4])
        df_master_elec["type_election"] = id_election.split("_")[1]

        for df_join in [df_euro_pivot, df_euro_gagnant, df_part_euro,
                        df_pop_slice, df_emploi_slice, df_rev, df_imm, df_sec]:
            df_master_elec = df_master_elec.merge(
                df_join, on="code_commune", how="left"
            )

        # Remplir les colonnes euro manquantes par 0
        cols_euro_ratio = [c for c in df_master_elec.columns if c.startswith("euro_") and c.endswith("_ratio")]
        for col in cols_euro_ratio:
            df_master_elec[col] = df_master_elec[col].fillna(0)

        morceaux_master.append(df_master_elec)
        log.info(f"  {id_election} : {len(df_master_elec):,} communes")

    df_master = pd.concat(morceaux_master, ignore_index=True)

    # Ordre des colonnes
    cols_identite = ["id_election", "annee", "type_election",
                     "code_commune", "libelle_commune"]
    cols_cible    = ["famille_gagnante"]
    cols_euro     = [c for c in df_master.columns if c.startswith("euro_")]
    cols_socio    = [c for c in df_master.columns
                     if c not in cols_identite + cols_cible + cols_euro]

    df_master = df_master[cols_identite + cols_cible + cols_euro + cols_socio]

    log.info(f"Master final : {len(df_master):,} lignes | {df_master.shape[1]} colonnes")
    log.info(f"NaN restants :\n{df_master.isna().sum()[df_master.isna().sum() > 0].to_string()}")

    # Sauvegarde
    PROCESSED_DIR = BASE / "03_processed"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    chemin_master = PROCESSED_DIR / "master_ml.csv"
    df_master.to_csv(chemin_master, index=False, sep=";", encoding="utf-8-sig")
    log.info(f"Master sauvegarde : {chemin_master}")

    sauvegarder_sqlite({"master_ml": df_master}, DB_PATH)

    log.info("MASTER ML TERMINE")
    return df_master


# ==============================================================================
# Point d'entree
# ==============================================================================

if __name__ == "__main__":
    df_general_communes, df_export, df_candidats_communes = etl_electoral()
    (df_securite, df_pop, df_emploi,
     df_filo17, df_filo21, df_imm17, df_imm22) = etl_socioeco()

    df_master = construire_master(
        df_general_communes, df_candidats_communes,
        df_securite, df_pop, df_emploi,
        df_filo17, df_filo21, df_imm17, df_imm22
    )

    # Bilan final
    conn = sqlite3.connect(DB_PATH)
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table'", conn
    )
    log.info("=" * 60)
    log.info("BILAN FINAL - BASE mspr2.db")
    log.info("=" * 60)
    for table in tables["name"]:
        n = pd.read_sql(f"SELECT COUNT(*) as n FROM {table}", conn).iloc[0, 0]
        log.info(f"  {table:<25} {n:>10,} lignes")
    conn.close()

    log.info("PIPELINE COMPLET TERMINE")