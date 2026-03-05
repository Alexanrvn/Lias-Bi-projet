import os
import time
import csv
import requests
import xml.etree.ElementTree as ET

# Configuration des chemins (le script est dans /scripts, on remonte d'un cran)
INPUT_CSV = "../data/membres.csv"
CACHE_DIR = "../cache/dblp"
DELAY = 3  # Délai de 3 secondes pour respecter le rate-limiting

# Création du dossier de cache s'il n'existe pas
os.makedirs(CACHE_DIR, exist_ok=True)

def get_pid_from_api(nom):
    """Interroge l'API DBLP pour trouver le PID d'un auteur d'après son nom."""
    url = f"https://dblp.org/search/author/api?q={nom}&format=xml"
    print(f"  -> Recherche du PID pour {nom}...")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        # Récupération du premier auteur trouvé (Attention aux homonymes !)
        author_node = root.find(".//author")
        if author_node is not None and 'pid' in author_node.attrib:
            return author_node.attrib['pid']
        return None
    except Exception as e:
        print(f"  [Erreur] Impossible de récupérer le PID pour {nom}: {e}")
        return None

def download_publications(pid, nom_complet):
    """Télécharge le fichier XML des publications d'un auteur via son PID."""
    
    # --- LA CORRECTION MAGIQUE EST ICI ---
    pid_corrige = pid.replace('-', '/')
    url = f"https://dblp.org/pid/{pid_corrige}.xml"
    
    # Formatage du nom pour le fichier (ex: Ladjel_Bellatreche.xml)
    fichier_cache = os.path.join(CACHE_DIR, f"{nom_complet.replace(' ', '_')}.xml")
    
    # Vérification du cache pour ne pas retélécharger
    if os.path.exists(fichier_cache):
        print(f"  -> Fichier déjà en cache pour {nom_complet}.")
        return True

    print(f"  -> Téléchargement des publications (URL: {url})...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with open(fichier_cache, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  [Erreur] Échec du téléchargement pour {nom_complet} (PID: {pid_corrige}): {e}")
        return False
def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Fichier {INPUT_CSV} introuvable. Vérifiez le chemin.")
        return

    # On utilise toujours latin-1 pour éviter le plantage sur le "ï" de Loïc
    with open(INPUT_CSV, mode='r', encoding='latin-1') as f:
        # On détecte automatiquement si c'est une virgule ou un point-virgule
        premiere_ligne = f.readline()
        separateur = ';' if ';' in premiere_ligne else ','
        f.seek(0) # On remet le curseur au début du fichier
        
        reader = csv.DictReader(f, delimiter=separateur)
        
        lignes_traitees = 0
        for row in reader:
            # Nettoyage magique des noms de colonnes (enlève les majuscules, les espaces et les caractères invisibles)
            row_propre = {str(k).strip(' \ufeffï»¿').lower(): str(v).strip() for k, v in row.items() if k}
            
            nom = row_propre.get("nom", "")
            prenom = row_propre.get("prenom", "")
            pid = row_propre.get("pid_dblp", "")
            
            if not nom or not prenom:
                print(f"[Alerte] Ligne ignorée car nom ou prénom manquant : {row_propre}")
                continue
                
            lignes_traitees += 1
            nom_complet = f"{prenom} {nom}"
            print(f"\nTraitement de : {nom_complet}")
            
            if not pid:
                pid = get_pid_from_api(nom_complet)
                time.sleep(DELAY)
                
            if not pid:
                print(f"  [Alerte] Aucun PID trouvé pour {nom_complet}. Ignoré.")
                continue
                
            succes = download_publications(pid, nom_complet)
            if succes:
                print(f"  [Succès] Données enregistrées pour {nom_complet}.")
                
            time.sleep(DELAY)

        if lignes_traitees == 0:
            print("\n[Erreur] Aucune ligne valide trouvée dans le CSV. Vérifiez les colonnes.")

if __name__ == "__main__":
    print("Début de la collecte DBLP...")
    main()
    print("\nCollecte terminée. Les fichiers XML sont dans le dossier cache/dblp.")