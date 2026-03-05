import os
import pandas as pd

# --- Configuration des chemins ---
MEMBRES_CSV = "../data/membres.csv"
PUBLIS_CSV = "../cache/publications_enriches.csv"
THESES_CSV = "../cache/theses_brutes.csv"

OUT_DIR_CHERCHEURS = "../data/output/chercheurs"
OUT_CONSOLIDATED = "../data/output/consolidated.xlsx"

def charger_donnees():
    """Charge les différents jeux de données en gérant les fichiers manquants."""
    df_membres = pd.DataFrame()
    df_publis = pd.DataFrame()
    df_theses = pd.DataFrame()

    if os.path.exists(MEMBRES_CSV):
        df_membres = pd.read_csv(MEMBRES_CSV, encoding='latin-1', sep=None, engine='python')
        # Création de la colonne nom_complet pour faciliter les jointures
        if 'nom' in df_membres.columns and 'prenom' in df_membres.columns:
            df_membres['nom_complet'] = df_membres['prenom'].astype(str).str.strip() + " " + df_membres['nom'].astype(str).str.strip()
    
    if os.path.exists(PUBLIS_CSV):
        df_publis = pd.read_csv(PUBLIS_CSV)
        
    if os.path.exists(THESES_CSV):
        df_theses = pd.read_csv(THESES_CSV)
        
    return df_membres, df_publis, df_theses

def generer_excel_chercheur(nom_complet, df_publis_membre, df_theses_membre):
    """Génère le fichier Excel individuel pour un chercheur."""
    fichier_sortie = os.path.join(OUT_DIR_CHERCHEURS, f"{nom_complet.replace(' ', '_')}.xlsx")
    
    # Séparation des publications
    df_journaux = df_publis_membre[df_publis_membre['type_publi'] == 'Journal'].copy()
    df_confs = df_publis_membre[df_publis_membre['type_publi'] == 'Conférence'].copy()
    
    # Nettoyage des colonnes pour l'affichage
    cols_journaux = ['annee', 'titre', 'venue', 'quartile_scimago', 'sjr', 'score_qualite']
    cols_confs = ['annee', 'titre', 'venue', 'rang_core', 'score_qualite']
    
    df_journaux = df_journaux[[c for c in cols_journaux if c in df_journaux.columns]]
    df_confs = df_confs[[c for c in cols_confs if c in df_confs.columns]]
    
    # Calcul du résumé (Résumé des KPI)
    total_journaux = len(df_journaux)
    total_confs = len(df_confs)
    total_publis = total_journaux + total_confs
    score_moyen = df_publis_membre['score_qualite'].mean() if total_publis > 0 else 0
    total_theses = len(df_theses_membre)
    
    df_resume = pd.DataFrame({
        "Indicateur": [
            "Total Publications (2021-2025)", 
            "Total Journaux", 
            "Total Conférences", 
            "Score Qualité Moyen", 
            "Total Thèses encadrées"
        ],
        "Valeur": [total_publis, total_journaux, total_confs, round(score_moyen, 2), total_theses]
    })
    
    # Onglet "Rapports" vide pour respecter scrupuleusement le cahier des charges
    df_rapports = pd.DataFrame(columns=["annee", "titre", "type"])
    
    # Écriture dans le fichier Excel
    with pd.ExcelWriter(fichier_sortie, engine='openpyxl') as writer:
        df_journaux.to_excel(writer, sheet_name='Journaux Scimago', index=False)
        df_confs.to_excel(writer, sheet_name='Conférences CORE', index=False)
        df_theses_membre.to_excel(writer, sheet_name='Thèses', index=False)
        df_rapports.to_excel(writer, sheet_name='Rapports', index=False)
        df_resume.to_excel(writer, sheet_name='Résumé', index=False)
        
    print(f"  -> Livrable généré : {fichier_sortie}")

def main():
    print("Début de la génération des fichiers Excel...")
    
    # Création des dossiers de sortie
    os.makedirs(OUT_DIR_CHERCHEURS, exist_ok=True)
    
    df_membres, df_publis, df_theses = charger_donnees()
    
    if df_membres.empty:
        print("[Erreur] Impossible de générer les fichiers sans la liste des membres.")
        return

    # 1. Fichier consolidé pour tout le laboratoire
    print("\nCréation du fichier consolidé global...")
    with pd.ExcelWriter(OUT_CONSOLIDATED, engine='openpyxl') as writer:
        if not df_publis.empty:
            df_publis.to_excel(writer, sheet_name='Toutes_Publications', index=False)
        if not df_theses.empty:
            df_theses.to_excel(writer, sheet_name='Toutes_Theses', index=False)
        df_membres.to_excel(writer, sheet_name='Membres_Laboratoire', index=False)
    print(f"  -> Consolidé généré : {OUT_CONSOLIDATED}")
    
    # 2. Fichiers individuels par chercheur
    print("\nCréation des fichiers individuels par chercheur...")
    for _, membre in df_membres.iterrows():
        nom_complet = membre.get('nom_complet')
        if not pd.isna(nom_complet):
            # Filtrer les données pour ce chercheur
            publis_membre = df_publis[df_publis['auteur'] == nom_complet] if not df_publis.empty else pd.DataFrame()
            theses_membre = df_theses[df_theses['directeur'] == nom_complet] if not df_theses.empty else pd.DataFrame()
            
            generer_excel_chercheur(nom_complet, publis_membre, theses_membre)

    print("\nGénération Excel terminée avec succès !")

if __name__ == "__main__":
    main()