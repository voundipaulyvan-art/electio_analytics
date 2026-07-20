# MSPR Electio-Analytics

Pipeline Big Data & Machine Learning pour la prédiction des résultats des élections législatives françaises à travers l'analyse socio-économique des communes.

**Établissement :** EPSI — Projet MSPR (Mission Système Professionnalisant)
**Périmètre géographique :** Département du Rhône (69) — ~266 à 280 communes
**Élections couvertes :** Législatives 2017, 2022, 2024

---

## Objectif du projet

Construire un modèle de Machine Learning capable de **prédire le vainqueur des élections législatives 2027** dans le Rhône, en s'appuyant sur l'évolution d'indicateurs socio-économiques (chômage, revenus, pauvreté, délinquance, vie associative, immigration, abstention, etc.) entre plusieurs millésimes.

- **Entraînement :** données législatives 2017 et 2022
- **Test :** données législatives 2024
- **Cible :** projection 2027
- **Critère de succès :** R² > 0.5
- **Résultat actuel :** Random Forest, **R² = 0.859** (validation croisée), MAE ≈ 1.94–3.2 %

---

## Équipe

Projet réalisé en groupe de 4, avec les rôles suivants :

| Rôle | Mission |
|---|---|
| Product Manager | Cadrage fonctionnel, priorisation |
| Data Analyst | Exploration et analyse des données |
| **Data Scientist** *(Paul Yvan)* | Feature engineering, modélisation ML |
| Data Engineer | Pipeline de données, infrastructure |

---

## Architecture du pipeline de données

```
01_raw/          → Données brutes issues des sources officielles
02_staging/      → Données nettoyées et standardisées
03_processed/    → Features engineerées (dont les indicateurs delta)
04_output/       → Résultats, modèles entraînés, prédictions
```

---

## Sources de données

| Source | Données |
|---|---|
| INSEE | Emploi/chômage, démographie, immigration, Filosofi (revenus/pauvreté) |
| Ministère de l'Intérieur | Résultats électoraux |
| SSMSI | Délinquance et criminalité |
| RNA Waldec | Vie associative |
| data.gouv.fr | Fichiers communaux (format parquet) |

**Formats rencontrés :** CSV (séparateur `;`, encodage latin1), XLS, Parquet

---

## Approche "Delta" (feature engineering)

Plutôt que d'utiliser des données socio-économiques figées à un instant T (source de biais temporel identifiée par le corps enseignant), le projet calcule des **indicateurs delta** (Année2 − Année1) pour capturer la dynamique d'évolution des territoires.

**Principe :** toujours comparer deux millésimes issus de la **même source** de données pour éviter les incohérences méthodologiques.

### Indicateurs delta produits

| Fichier | Indicateur | Période |
|---|---|---|
| `delta_chomage_2016_2022.csv` | Taux de chômage (INSEE) | 2016–2022 |
| `delta_filosofi_2017_2020.csv` | Revenu médian et pauvreté | 2017–2020 |
| `delta_abstention_2017_2022.csv` | Abstention (agrégée bureau → commune) | 2017–2022 |
| `delta_ssmsi_2016_2021.csv` | 4 indicateurs de délinquance | 2016–2021 |
| `delta_vie_associative_2019_2022.csv` | Vie associative (RNA Waldec) | 2019–2022 |
| `delta_taux_jeunes_2016_2022.csv` | Part de la population jeune | 2016–2022 |
| `delta_immigration_2016_2022.csv` | Taux d'immigration | 2016–2022 |
| `delta_violences_2017_2024.csv` | Violences physiques hors cadre familial | 2017–2024 |

Les fichiers socio-économiques 2021 d'origine sont conservés tels quels ; les fichiers delta viennent s'y ajouter de manière additive.

### Indicateurs SSMSI retenus
Sur l'ensemble des indicateurs disponibles, 4 ont été jugés les plus pertinents électoralement :
violences hors cadre familial, vols sans violence, cambriolages, dégradations/vandalisme.

---

## Modélisation Machine Learning

- **Modèles testés :** Random Forest, Gradient Boosting, Ridge, régression linéaire
- **Meilleur modèle :** Random Forest
  - R² = 0.859 (validation croisée 5-fold)
  - MAE ≈ 1.94–3.2 %
- **Split temporel :** entraînement sur 2017 + 2022, test sur 2024
- **Centrage :** technique appliquée pour retirer le biais temporel introduit par l'événement exceptionnel de la dissolution de 2024

---

## Points de vigilance méthodologiques

- **Secret statistique INSEE** (codes `s`) : valeurs imputées à partir des colonnes `complement_info` ; 266/280 communes conservées après nettoyage
- **RNA Waldec :** les fichiers historiques n'étant pas disponibles, les snapshots 2019 et 2022 ont été reconstruits à partir du fichier de décembre 2022
- **Toujours utiliser `.copy()`** lors de la création de DataFrames pandas, pour éviter les bugs d'écrasement accidentel (un bug de delta=0 a été causé par l'écrasement de `df_2017`)

---

## Stack technique

- **Langage :** Python
- **Traitement de données :** pandas, pyarrow
- **Machine Learning :** scikit-learn (Random Forest, Gradient Boosting, Ridge, régression linéaire)
- **Visualisation :** matplotlib
- **Environnement :** Jupyter Notebooks

---

## Prochaines étapes

- Poursuivre le calcul des indicateurs delta manquants
- Intégrer l'ensemble des features delta finalisées dans le pipeline ML
- Développer la mini-application web **Electio-Analytics** (React, Recharts, Tailwind CSS) avec 6 pages :
  1. Dashboard
  2. Recherche par commune
  3. Simulateur de prédiction
  4. Visualisations
  5. Projections 2027
  6. Résultats du modèle ML

*(spécifications détaillées disponibles dans `electio_analytics_specifications.md`)*

---

## Dossier de travail

Un dossier `TestFacteur/` est utilisé comme bac à sable pour expérimenter avant intégration dans le pipeline principal.

---

## Notes

Ce README a été généré à partir de l'état du projet et pourra être complété au fur et à mesure de son avancement (instructions d'installation, arborescence détaillée des dossiers, exemples d'utilisation des notebooks, etc.).
