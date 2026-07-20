# dashboard.py
import streamlit as st
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import sqlite3
from pathlib import Path
from sklearn.metrics import confusion_matrix, classification_report, f1_score, accuracy_score
from sklearn.model_selection import learning_curve, StratifiedKFold

# ==============================================================================
# CONFIG
# ==============================================================================
st.set_page_config(
    page_title="Electio-Analytics — Rhône",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE        = Path(r"C:\Users\NIAMBELE Siata\Desktop\MSPR2")
MODELS_DIR  = BASE / "04_outputs" / "models"
MASTER_CSV  = BASE / "03_processed" / "master_ml.csv"
DB_PATH     = BASE / "03_database"  / "mspr2.db"

COULEURS = {
    "Centre"        : "#DDAA00",
    "Droite"        : "#4488CC",
    "Extreme droite": "#1A1A6E",
    "Gauche"        : "#FF6666",
    "Divers"        : "#AAAAAA",
}
REGROUP = {
    "Extreme gauche"      : "Gauche",
    "Gauche radicale"     : "Gauche",
    "Gauche"              : "Gauche",
    "Ecologie"            : "Gauche",
    "Centre"              : "Centre",
    "Droite"              : "Droite",
    "Droite souverainiste": "Droite",
    "Extreme droite"      : "Extreme droite",
    "Divers"              : "Divers",
    "Inconnu"             : "Divers",
}

# ==============================================================================
# CHARGEMENT
# ==============================================================================
@st.cache_resource
def load_models():
    return {
        "Random Forest"      : joblib.load(MODELS_DIR / "random_forest_combined.joblib"),
        "Gradient Boosting"  : joblib.load(MODELS_DIR / "gradient_boosting_combined.joblib"),
        "Logistic Regression": joblib.load(MODELS_DIR / "logistic_regression_combined.joblib"),
        "KNN"                : joblib.load(MODELS_DIR / "knn_combined.joblib"),
    }

@st.cache_data
def load_data():
    le_combined       = joblib.load(MODELS_DIR / "le_combined.joblib")
    X_combined        = joblib.load(MODELS_DIR / "X_combined.pkl")
    X_train_c         = joblib.load(MODELS_DIR / "X_train_c.pkl")
    X_test_c          = joblib.load(MODELS_DIR / "X_test_c.pkl")
    y_combined        = joblib.load(MODELS_DIR / "y_combined.pkl")
    y_train_c         = joblib.load(MODELS_DIR / "y_train_c.pkl")
    y_test_c          = joblib.load(MODELS_DIR / "y_test_c.pkl")
    df_bilan_combined = joblib.load(MODELS_DIR / "df_bilan_combined.pkl")
    df_bilan          = joblib.load(MODELS_DIR / "df_bilan.pkl")
    df_bilan_deltas   = joblib.load(MODELS_DIR / "df_bilan_deltas.pkl")
    df_master         = pd.read_csv(MASTER_CSV, sep=";", low_memory=False)
    df_master["famille_regroupee"] = df_master["famille_gagnante"].map(REGROUP).fillna("Divers")
    return (le_combined, X_combined, X_train_c, X_test_c,
            y_combined, y_train_c, y_test_c,
            df_bilan_combined, df_bilan, df_bilan_deltas, df_master)

modeles_combined = load_models()
(le_combined, X_combined, X_train_c, X_test_c,
 y_combined, y_train_c, y_test_c,
 df_bilan_combined, df_bilan, df_bilan_deltas, df_master) = load_data()

# ==============================================================================
# SIDEBAR
# ==============================================================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Flag_of_France.svg/320px-Flag_of_France.svg.png",
                 width=80)
st.sidebar.title("Electio-Analytics")
st.sidebar.caption("Rhône — Prédiction électorale ML")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigation", [
    " Accueil",
    " EDA",
    " Performances ML",
    " Analyse par modèle",
    " Comparaison versions",
    " Projection 2027",
])

# ==============================================================================
# PAGE 1 — ACCUEIL
# ==============================================================================
if page == " Accueil":
    st.title(" Electio-Analytics — Rhône")
    st.markdown("**Prédiction de la famille politique gagnante par commune** — Législatives 2024")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Communes", "266")
    col2.metric("Élections analysées", "5")
    col3.metric("Features", str(X_combined.shape[1]))
    col4.metric("Modèles entraînés", "4")

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Distribution cible — 2024")
        df_2024 = df_master[df_master["id_election"] == "2024_legi_t1"]
        counts  = df_2024["famille_regroupee"].value_counts()
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(counts.index, counts.values,
                      color=[COULEURS.get(f, "#AAAAAA") for f in counts.index],
                      edgecolor="white")
        for bar, val in zip(bars, counts.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(val), ha="center", fontweight="bold")
        ax.set_ylabel("Communes")
        ax.spines[["top","right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=20)
        st.pyplot(fig)
        plt.close()

    with col_b:
        st.subheader("Meilleurs F1 par version")
        df_all = pd.concat([
            df_bilan.assign(version="Master complet"),
            df_bilan_deltas.assign(version="Deltas seuls"),
            df_bilan_combined.assign(version="Master + Deltas"),
        ])
        best = df_all.groupby("version")["f1_weighted"].max().reindex(
            ["Master complet", "Deltas seuls", "Master + Deltas"]
        )
        fig, ax = plt.subplots(figsize=(6, 4))
        colors_v = ["#4488CC", "#FF6666", "#33AA44"]
        bars = ax.bar(best.index, best.values, color=colors_v, edgecolor="white", width=0.5)
        ax.set_ylim(0, 1.1)
        ax.set_ylabel("F1 weighted")
        ax.spines[["top","right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=15)
        for bar, val in zip(bars, best.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f"{val:.3f}", ha="center", fontweight="bold")
        st.pyplot(fig)
        plt.close()

    st.markdown("---")
    st.subheader("Tableau de bord — Version Master + Deltas")
    st.dataframe(df_bilan_combined.style.highlight_max(subset=["f1_weighted","accuracy"],
                                                        color="#d4edda"), use_container_width=True)

# ==============================================================================
# PAGE 2 — EDA
# ==============================================================================
elif page == " EDA":
    st.title(" Analyse exploratoire")

    tab1, tab2, tab3 = st.tabs(["Évolution politique", "Déséquilibre classes", "Valeurs manquantes"])

    with tab1:
        st.subheader("Évolution des familles politiques — Législatives")
        elections_legi = sorted(df_master[df_master["type_election"] == "legi"]["id_election"].unique())
        labels_legi    = [e.split("_")[0] for e in elections_legi]
        familles       = list(COULEURS.keys())
        linestyles     = ["-","--","-.",":",  (0,(5,2))]

        fig, ax = plt.subplots(figsize=(10, 5))
        for famille, ls in zip(familles, linestyles):
            vals = [(df_master[df_master["id_election"]==e]["famille_regroupee"]==famille).sum()
                    for e in elections_legi]
            ax.plot(labels_legi, vals, marker="o", linewidth=2.5, markersize=9,
                    color=COULEURS[famille], linestyle=ls, label=famille)
            for x_pos, y_pos in zip(labels_legi, vals):
                ax.annotate(str(y_pos), (x_pos, y_pos), textcoords="offset points",
                            xytext=(0, 10), ha="center", fontsize=9, fontweight="bold",
                            color=COULEURS[famille])
        ax.set_ylabel("Communes gagnées")
        ax.legend(loc="upper left")
        ax.grid(alpha=0.3)
        ax.spines[["top","right"]].set_visible(False)
        st.pyplot(fig)
        plt.close()

    with tab2:
        st.subheader("Déséquilibre des classes — 2024")
        df_2024   = df_master[df_master["id_election"] == "2024_legi_t1"]
        counts_24 = df_2024["famille_regroupee"].value_counts()
        total_24  = len(df_2024)
        baseline  = counts_24.max() / total_24 * 100

        col1, col2 = st.columns(2)
        col1.metric("Classe majoritaire", counts_24.index[0], f"{baseline:.1f}%")
        col2.metric("Baseline à battre", f"{baseline:.1f}%", "Seuil minimum du modèle")

        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(counts_24.index, [v/total_24*100 for v in counts_24.values],
                      color=[COULEURS.get(f, "#AAAAAA") for f in counts_24.index],
                      edgecolor="white")
        ax.axhline(y=baseline, color="red", linestyle="--", linewidth=1.5,
                   label=f"Baseline = {baseline:.1f}%")
        ax.set_ylabel("% communes")
        ax.legend()
        ax.spines[["top","right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=20)
        for bar, val in zip(bars, [v/total_24*100 for v in counts_24.values]):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f"{val:.1f}%", ha="center", fontweight="bold")
        st.pyplot(fig)
        plt.close()

    with tab3:
        st.subheader("Valeurs manquantes — master_ml.csv")
        nan_pct = (df_master.isna().sum() / len(df_master) * 100).round(1)
        nan_pct = nan_pct[nan_pct > 0].sort_values(ascending=True)
        bar_colors_nan = ["#E24B4A" if v > 50 else "#EF9F27" if v > 10 else "#639922"
                          for v in nan_pct.values]
        fig, ax = plt.subplots(figsize=(9, max(4, len(nan_pct) * 0.45)))
        ax.barh(nan_pct.index, nan_pct.values, color=bar_colors_nan, edgecolor="white", height=0.6)
        ax.axvline(x=50, color="red", linestyle="--", linewidth=1.5)
        ax.set_xlabel("% manquants")
        ax.spines[["top","right"]].set_visible(False)
        legend_patches = [
            mpatches.Patch(color="#E24B4A", label="Critique (>50%)"),
            mpatches.Patch(color="#EF9F27", label="Modéré (10-50%)"),
            mpatches.Patch(color="#639922", label="Faible (<10%)"),
        ]
        ax.legend(handles=legend_patches, fontsize=9)
        st.pyplot(fig)
        plt.close()

# ==============================================================================
# PAGE 3 — PERFORMANCES ML
# ==============================================================================
elif page == " Performances ML":
    st.title(" Performances des modèles")

    modele_selec = st.selectbox("Choisir un modèle", list(modeles_combined.keys()))
    pipeline     = modeles_combined[modele_selec]

    col1, col2, col3 = st.columns(3)
    y_pred = pipeline.predict(X_test_c)
    acc    = accuracy_score(y_test_c, y_pred)
    f1     = f1_score(y_test_c, y_pred, average="weighted", zero_division=0)
    row    = df_bilan_combined[df_bilan_combined["modele"] == modele_selec].iloc[0]
    col1.metric("Accuracy (test)", f"{acc:.3f}")
    col2.metric("F1 weighted (test)", f"{f1:.3f}")
    col3.metric("F1 weighted (CV)", f"{row['score_cv']:.3f}")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Matrice de confusion", "F1 par classe", "Courbe d'apprentissage"])

    with tab1:
        cm     = confusion_matrix(y_test_c, y_pred)
        cm_pct = cm.astype(float) / cm.sum(axis=1, keepdims=True) * 100
        classes = le_combined.classes_

        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(cm_pct, cmap="Blues", vmin=0, vmax=100)
        plt.colorbar(im, ax=ax, label="%")
        ax.set_xticks(range(len(classes)))
        ax.set_yticks(range(len(classes)))
        ax.set_xticklabels(classes, rotation=30, ha="right")
        ax.set_yticklabels(classes)
        for row_i in range(cm_pct.shape[0]):
            for col_j in range(cm_pct.shape[1]):
                color = "white" if cm_pct[row_i, col_j] > 50 else "black"
                ax.text(col_j, row_i, f"{cm[row_i,col_j]}\n({cm_pct[row_i,col_j]:.0f}%)",
                        ha="center", va="center", fontsize=9, color=color, fontweight="bold")
        ax.set_xlabel("Prédit")
        ax.set_ylabel("Réel")
        ax.set_title(f"Matrice de confusion — {modele_selec}")
        st.pyplot(fig)
        plt.close()

    with tab2:
        report = classification_report(y_test_c, y_pred, target_names=classes,
                                        output_dict=True, zero_division=0)
        f1_scores = [report[c]["f1-score"] for c in classes]
        fig, ax   = plt.subplots(figsize=(8, 4))
        bars = ax.barh(classes, f1_scores,
                       color=[COULEURS.get(c, "#AAAAAA") for c in classes],
                       edgecolor="white", height=0.6)
        ax.axvline(x=report["weighted avg"]["f1-score"], color="red", linestyle="--",
                   linewidth=1.5, label=f"F1 moyen = {report['weighted avg']['f1-score']:.2f}")
        ax.set_xlim(0, 1.1)
        ax.set_xlabel("F1-score")
        ax.legend()
        ax.spines[["top","right"]].set_visible(False)
        for bar, val in zip(bars, f1_scores):
            ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                    f"{val:.2f}", va="center", fontweight="bold")
        st.pyplot(fig)
        plt.close()

    with tab3:
        st.info("Calcul en cours — peut prendre 30 secondes...")
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        train_sizes, train_scores, val_scores = learning_curve(
            pipeline, X_combined, y_combined, cv=skf,
            scoring="f1_weighted", train_sizes=np.linspace(0.1, 1.0, 10), n_jobs=-1
        )
        train_mean = train_scores.mean(axis=1)
        val_mean   = val_scores.mean(axis=1)
        train_std  = train_scores.std(axis=1)
        val_std    = val_scores.std(axis=1)

        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(train_sizes, train_mean, "o-", color="#E24B4A", linewidth=2, label="Entraînement")
        ax.fill_between(train_sizes, train_mean-train_std, train_mean+train_std, alpha=0.15, color="#E24B4A")
        ax.plot(train_sizes, val_mean, "o-", color="#4488CC", linewidth=2, label="Validation")
        ax.fill_between(train_sizes, val_mean-val_std, val_mean+val_std, alpha=0.15, color="#4488CC")
        ax.axhline(y=0.7, color="gray", linestyle="--", alpha=0.6, label="Seuil 0.70")
        ax.set_xlabel("Taille d'entraînement")
        ax.set_ylabel("F1 weighted")
        ax.set_ylim(0, 1.05)
        ax.legend()
        ax.grid(alpha=0.3)
        ax.spines[["top","right"]].set_visible(False)
        st.pyplot(fig)
        plt.close()

# ==============================================================================
# PAGE 4 — ANALYSE PAR MODELE
# ==============================================================================
elif page == " Analyse par modèle":
    st.title(" Analyse détaillée par modèle")

    st.subheader("Importance des features — Random Forest")
    rf_clf      = modeles_combined["Random Forest"].named_steps["clf"]
    importances = rf_clf.feature_importances_
    indices     = np.argsort(importances)[::-1][:20]
    top_feat    = [X_combined.columns[i] for i in indices]
    top_vals    = [importances[i] for i in indices]

    colors_imp = ["#4488CC" if "euro_" in f else "#33AA44" if "delta_" in f else "#E87070"
                  for f in top_feat]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top_feat[::-1], top_vals[::-1], color=colors_imp[::-1], edgecolor="white", height=0.7)
    ax.set_xlabel("Importance (Gini)")
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.3)
    legend_patches = [
        mpatches.Patch(color="#4488CC", label="Scores européennes"),
        mpatches.Patch(color="#33AA44", label="Deltas socioéco"),
        mpatches.Patch(color="#E87070", label="Socioéco absolus"),
    ]
    ax.legend(handles=legend_patches, fontsize=10)
    st.pyplot(fig)
    plt.close()

    st.markdown("---")
    st.subheader("Rapport de classification complet")
    modele_selec2 = st.selectbox("Modèle", list(modeles_combined.keys()), key="modele2")
    y_pred2 = modeles_combined[modele_selec2].predict(X_test_c)
    report  = classification_report(y_test_c, y_pred2, target_names=le_combined.classes_,
                                     output_dict=True, zero_division=0)
    df_report = pd.DataFrame(report).T.round(3)
    st.dataframe(df_report.style.background_gradient(subset=["f1-score"], cmap="YlGn"),
                 use_container_width=True)

# ==============================================================================
# PAGE 5 — COMPARAISON VERSIONS
# ==============================================================================
elif page == " Comparaison versions":
    st.title(" Comparaison des 3 versions")

    df_all = pd.concat([
        df_bilan.assign(version="Master complet"),
        df_bilan_deltas.assign(version="Deltas seuls"),
        df_bilan_combined.assign(version="Master + Deltas"),
    ], ignore_index=True)

    couleurs_versions = {
        "Master complet" : "#4488CC",
        "Deltas seuls"   : "#FF6666",
        "Master + Deltas": "#33AA44",
    }

    tab1, tab2, tab3 = st.tabs(["Heatmap performances", "CV vs Test", "Radar"])

    with tab1:
        pivot = df_all.pivot_table(index="modele", columns="version",
                                    values="f1_weighted", aggfunc="mean")
        pivot = pivot[["Master complet","Deltas seuls","Master + Deltas"]]
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.heatmap(pivot, annot=True, fmt=".3f", cmap="YlGn",
                    vmin=0.5, vmax=1.0, linewidths=0.5, linecolor="white",
                    ax=ax, annot_kws={"size": 13, "weight": "bold"})
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.tick_params(axis="x", rotation=15)
        ax.tick_params(axis="y", rotation=0)
        st.pyplot(fig)
        plt.close()

    with tab2:
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        for ax, (titre, df_v, color) in zip(axes, [
            ("Master complet",  df_bilan,         "#4488CC"),
            ("Deltas seuls",    df_bilan_deltas,   "#FF6666"),
            ("Master + Deltas", df_bilan_combined, "#33AA44"),
        ]):
            modeles_noms = df_v["modele"].tolist()
            scores_cv    = df_v["score_cv"].tolist()
            scores_test  = df_v["f1_weighted"].tolist()
            x = np.arange(len(modeles_noms))
            w = 0.35
            bars1 = ax.bar(x - w/2, scores_cv,   width=w, color=color,    alpha=0.85,
                           label="CV", edgecolor="white")
            bars2 = ax.bar(x + w/2, scores_test, width=w, color="#DDAA00", alpha=0.85,
                           label="Test", edgecolor="white")
            for bar in list(bars1) + list(bars2):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f"{bar.get_height():.2f}", ha="center", fontsize=8, fontweight="bold")
            ax.set_xticks(x)
            ax.set_xticklabels([m.replace(" ", "\n") for m in modeles_noms], fontsize=9)
            ax.set_ylim(0, 1.1)
            ax.set_title(titre, fontsize=11, fontweight="bold")
            ax.set_ylabel("F1 weighted")
            ax.legend(fontsize=9)
            ax.grid(axis="y", alpha=0.3)
            ax.spines[["top","right"]].set_visible(False)
        st.pyplot(fig)
        plt.close()

    with tab3:
        categories = ["Random Forest", "Gradient\nBoosting", "Logistic\nRegression", "KNN"]
        n_cat      = len(categories)
        angles     = np.linspace(0, 2*np.pi, n_cat, endpoint=False).tolist()
        angles    += angles[:1]

        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        for titre, df_v, color in [
            ("Master complet",  df_bilan,         "#4488CC"),
            ("Deltas seuls",    df_bilan_deltas,   "#FF6666"),
            ("Master + Deltas", df_bilan_combined, "#33AA44"),
        ]:
            df_sorted = df_v.set_index("modele").reindex(
                ["Random Forest","Gradient Boosting","Logistic Regression","KNN"]
            )
            values  = df_sorted["f1_weighted"].fillna(0).tolist()
            values += values[:1]
            ax.plot(angles, values, "o-", linewidth=2, color=color, label=titre)
            ax.fill(angles, values, alpha=0.08, color=color)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylim(0, 1)
        ax.legend(loc="upper right", bbox_to_anchor=(1.4, 1.1), fontsize=10)
        ax.grid(alpha=0.3)
        st.pyplot(fig)
        plt.close()

# ==============================================================================
# PAGE 6 — PROJECTION 2027
# ==============================================================================
elif page == " Projection 2027":
    st.title(" Projection Présidentielles 2027")
    st.info("Projection indicative basée sur les données socioéconomiques 2017-2022 et les signaux électoraux les plus récents.")

    try:
        meilleur = joblib.load(MODELS_DIR / "meilleur_modele_combined.joblib")

        df_master_2027 = df_master[df_master["id_election"] == "2024_legi_t1"].copy()
        cols_exclure   = ["code_commune","famille_gagnante","famille_regroupee",
                          "id_election","annee","type_election"]
        X_2027 = df_master_2027[[c for c in df_master_2027.columns
                                  if c not in cols_exclure]].copy()
        for col in X_2027.columns:
            X_2027[col] = pd.to_numeric(X_2027[col], errors="coerce")

        X_2027_aligned = X_2027.reindex(columns=X_combined.columns, fill_value=0)

        from sklearn.preprocessing import LabelEncoder
        le_tmp = LabelEncoder()
        le_tmp.classes_ = le_combined.classes_
        y_proj = meilleur.predict(X_2027_aligned)
        df_master_2027["prediction_2027"] = le_combined.inverse_transform(y_proj)

        projection = df_master_2027["prediction_2027"].value_counts()
        total      = len(df_master_2027)
        vainqueur  = projection.index[0]

        st.success(f" Vainqueur prédit 2027 : **{vainqueur}** ({projection[vainqueur]} communes sur {total})")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Répartition prédite 2027")
            fig, ax = plt.subplots(figsize=(6, 5))
            wedges, texts, autotexts = ax.pie(
                projection.values,
                labels=None, autopct="%1.1f%%",
                colors=[COULEURS.get(f, "#AAAAAA") for f in projection.index],
                startangle=90, pctdistance=0.75,
                wedgeprops={"edgecolor": "white", "linewidth": 2}
            )
            for at in autotexts:
                at.set_fontsize(10)
                at.set_fontweight("bold")
                at.set_color("white")
            legend_patches = [mpatches.Patch(color=COULEURS.get(f,"#AAAAAA"), label=f"{f} ({projection[f]})")
                              for f in projection.index]
            ax.legend(handles=legend_patches, loc="lower center",
                      bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9)
            st.pyplot(fig)
            plt.close()

        with col2:
            st.subheader("Détail par famille")
            df_proj = pd.DataFrame({
                "Famille": projection.index,
                "Communes": projection.values,
                "% communes": (projection.values / total * 100).round(1)
            })
            st.dataframe(df_proj, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erreur lors de la projection : {e}")
        st.warning("Assurez-vous que le modèle meilleur_modele_combined.joblib est bien sauvegardé.")
    with open(r"C:\Users\NIAMBELE Siata\Desktop\MSPR2\dashboard.py", "w", encoding="utf-8") as f:
        f.write(st.code)
print("dashboard.py créé.")   