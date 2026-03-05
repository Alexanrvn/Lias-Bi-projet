docker-compose up --build

# 📊 Projet BI & Bibliométrie - Laboratoire LIAS

## 🚀 Fonctionnalités du Pipeline

Le projet est structuré autour d'une architecture Data complète (ETL > API > Dashboard) :

1. **Extraction (Scraping & API) :** Collecte automatisée des publications sur *DBLP* et des données d'encadrement sur *Theses.fr*.
2. **Transformation & Nettoyage :** Traitement des données via *Pandas* (gestion des homonymes, standardisation des années).
3. **Enrichissement Qualitatif :** Croisement algorithmique des publications avec les classements internationaux **CORE** (conférences : A*, A, B, C) et **SCImago / SJR** (revues : Q1 à Q4).
4. **Distribution (API REST) :** Mise à disposition des données nettoyées via une API **FastAPI** documentée et sécurisée.
5. **Visualisation (Dashboard) :** Interface interactive **Streamlit** incluant :
   - Des KPIs globaux et individuels (2021-2025).
   - Le calcul de l'Indice de Gini pour mesurer les inégalités de production.
   - Un modèle de projection linéaire (NumPy) à l'horizon 2030.
   - Un graphe de collaboration (NetworkX) mettant en évidence les "ponts" entre chercheurs.
   - Un simulateur de marginalisation/transfert pour tester la résilience de la fusion.

## 🛠️ Technologies Utilisées

- **Langage :** Python 3.10+
- **Data Engineering :** Pandas, Numpy, OpenPyXL, Requests
- **Backend :** FastAPI, Uvicorn
- **Frontend / Dataviz :** Streamlit, Plotly, NetworkX, Matplotlib
- **Déploiement :** Docker, Docker Compose

## 📁 Structure du Dépôt

```text
Lias-Bi-projet/
│
├── data/                       # Référentiels (CORE, SCImago) et Livrables Excel générés
├── cache/                      # Fichiers CSV intermédiaires (Pipeline ETL)
├── scripts/                    # Code source de l'application
│   ├── 02_parse_dblp.py        # Script d'extraction DBLP
│   ├── 03_collect_theses.py    # Script d'extraction Theses.fr
│   ├── 04_enrich_core.py       # Algorithme de matching CORE
│   ├── 05_enrich_scimago.py    # Algorithme de matching SCImago
│   ├── 06_generate_excel.py    # Génération des livrables consolidés (.xlsx)
│   ├── api.py                  # Code du serveur FastAPI
│   ├── dashboard.py            # Code de l'interface Streamlit
│   ├── Dockerfile.api          # Image Docker pour le backend
│   ├── Dockerfile.dashboard    # Image Docker pour le frontend
│   └── requirements.txt        # Dépendances Python
│
├── docker-compose.yml          # Fichier d'orchestration Docker
└── README.md                   # Documentation du projet
