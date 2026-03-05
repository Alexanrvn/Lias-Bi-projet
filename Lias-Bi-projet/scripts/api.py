from fastapi import FastAPI, HTTPException
import pandas as pd
import os

app = FastAPI(
    title="API LIAS-BI",
    description="API REST pour consulter les publications et thèses du laboratoire LIAS",
    version="1.0.0"
)

# Chemins vers nos fichiers de données générés par l'ETL
DATA_PATH = "../data/output/consolidated.xlsx"
THESES_PATH = "../cache/theses.csv"

def load_data():
    """Charge les données Excel en mémoire."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Le fichier {DATA_PATH} est introuvable. Lancez le pipeline ETL d'abord.")
    return pd.read_excel(DATA_PATH)

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API du LIAS ! Les données sont prêtes."}

@app.get("/publications")
def get_toutes_les_publications():
    """Retourne toutes les publications du laboratoire."""
    try:
        df = load_data()
        # On remplace les cases vides (NaN) par des chaînes vides pour éviter que le JSON plante
        df = df.fillna("")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chercheurs/{nom_chercheur}/publications")
def get_publications_chercheur(nom_chercheur: str):
    """Retourne les publications d'un chercheur spécifique (ex: 'Ladjel BELLATRECHE')."""
    try:
        df = load_data()
        df = df.fillna("")
        
        # Filtrage par auteur (insensible à la casse)
        df_chercheur = df[df['auteur'].str.contains(nom_chercheur, case=False, na=False)]
        
        if df_chercheur.empty:
            raise HTTPException(status_code=404, detail=f"Aucune publication trouvée pour {nom_chercheur}")
            
        return df_chercheur.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/equipes")
def get_stats_equipes():
    """Retourne le nombre de publications par équipe."""
    try:
        df = load_data()
        stats = df['equipe'].value_counts().to_dict()
        return {"publications_par_equipe": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/theses")
def get_toutes_les_theses():
    """Retourne toutes les thèses encadrées sur la période."""
    try:
        if not os.path.exists(THESES_PATH):
            return [] # Retourne une liste vide si le fichier n'existe pas
            
        df_theses = pd.read_csv(THESES_PATH, encoding='utf-8')
        df_theses = df_theses.fillna("")
        return df_theses.to_dict(orient="records")
    except Exception as e:
        print(f"Erreur lors de la lecture des thèses : {e}")
        return []