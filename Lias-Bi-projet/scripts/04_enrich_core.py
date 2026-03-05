import os
import pandas as pd

# --- Configuration ---
INPUT_CSV = "../cache/publications_brutes.csv"
CORE_CSV = "../data/core_ranks.csv"  # Doit contenir des colonnes ex: 'Acronym', 'Title', 'Rank'
OUTPUT_CSV = "../cache/publications_core.csv"

# Barème CORE 
CORE_SCORES = {'A*': 4, 'A': 3, 'B': 2, 'C': 1}

def enrichir_core():
    print("Début de l'enrichissement avec le classement CORE...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"[Erreur] Fichier source {INPUT_CSV} introuvable.")
        return
        
    df_publis = pd.read_csv(INPUT_CSV)
    
    # Initialisation des nouvelles colonnes
    df_publis['rang_core'] = 'Non classé'
    df_publis['score_qualite'] = 0.0  # Float pour uniformiser avec SCImago plus tard
    
    if not os.path.exists(CORE_CSV):
        print(f"[Alerte] Fichier {CORE_CSV} introuvable. Les conférences resteront 'Non classées'.")
    else:
        # Chargement du référentiel CORE
        # On suppose que ton CSV CORE a au moins les colonnes 'Title', 'Acronym' et 'Rank'
        df_core = pd.read_csv(CORE_CSV, sep=';', on_bad_lines='skip') # Adapter le 'sep' selon ton fichier
        df_core['Title'] = df_core['Title'].astype(str).str.lower()
        df_core['Acronym'] = df_core['Acronym'].astype(str).str.lower()
        
        # Logique de matching
        for index, row in df_publis.iterrows():
            if row['type_publi'] == 'Conférence':
                venue = str(row['venue']).lower()
                
                # Recherche par titre exact ou par acronyme dans la venue
                match = df_core[(df_core['Title'] == venue) | 
                                df_core.apply(lambda x: x['Acronym'] in venue.split(), axis=1)]
                
                if not match.empty:
                    rang = str(match.iloc[0]['Rank']).upper()
                    if rang in CORE_SCORES:
                        df_publis.at[index, 'rang_core'] = rang
                        df_publis.at[index, 'score_qualite'] = float(CORE_SCORES[rang])

    # Sauvegarde
    df_publis.to_csv(OUTPUT_CSV, index=False)
    print(f"Enrichissement CORE terminé ! Sauvegardé dans {OUTPUT_CSV}.")

if __name__ == "__main__":
    enrichir_core()