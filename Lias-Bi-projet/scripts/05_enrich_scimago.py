import pandas as pd
import os

INPUT_CSV = "../cache/publications_core.csv"
SCIMAGO_CSV = "../data/scimago.csv"
OUTPUT_CSV = "../cache/publications_enriches.csv"

def enrichir_scimago():
    print("Début de l'enrichissement avec le classement SCImago...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"[Erreur] Fichier source {INPUT_CSV} introuvable.")
        return
        
    df_publis = pd.read_csv(INPUT_CSV)
    
    # Initialisation de la colonne si elle n'existe pas
    if 'quartile_scimago' not in df_publis.columns:
        df_publis['quartile_scimago'] = 'Non classé'
        
    if not os.path.exists(SCIMAGO_CSV):
        print(f"[Alerte] Fichier {SCIMAGO_CSV} introuvable. Les revues resteront 'Non classées'.")
    else:
        try:
            # Lecture robuste du fichier scimago (détecte tout seul le bon séparateur)
            df_scimago = pd.read_csv(SCIMAGO_CSV, sep=',', encoding='latin-1')
            
            # On cherche les colonnes qui ressemblent à "Title" et "Quartile"
            col_titre = [c for c in df_scimago.columns if 'title' in c.lower() or 'titre' in c.lower()][0]
            col_q = [c for c in df_scimago.columns if 'quartile' in c.lower() or 'sjr' in c.lower()][0]
            
            # Création d'un dictionnaire de correspondance en minuscules
            dict_scimago = dict(zip(df_scimago[col_titre].astype(str).str.lower().str.strip(), 
                                    df_scimago[col_q].astype(str).str.strip()))
            
            # Fonction pour attribuer le quartile
            def get_quartile(row):
                if row.get('type_publi') == 'Revue':
                    venue = str(row.get('venue', '')).lower().strip()
                    return dict_scimago.get(venue, 'Non classé')
                return row.get('quartile_scimago', 'Non classé')
                
            df_publis['quartile_scimago'] = df_publis.apply(get_quartile, axis=1)
            
        except Exception as e:
            print(f"[Erreur] Problème lors de la lecture de SCImago : {e}")
            
    # Sauvegarde du fichier final de l'ETL
    df_publis.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    print(f"Enrichissement SCImago terminé ! Sauvegardé dans {OUTPUT_CSV}.")

if __name__ == "__main__":
    enrichir_scimago()