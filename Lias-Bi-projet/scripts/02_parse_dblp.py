import os
import csv
import xml.etree.ElementTree as ET

# Chemins
MEMBRES_CSV = "../data/membres.csv"
CACHE_DBLP_DIR = "../cache/dblp"
OUTPUT_CSV = "../cache/publications_brutes.csv"
ANNEE_DEBUT = 2021
ANNEE_FIN = 2025

def charger_membres():
    """Charge les membres depuis le CSV en gérant l'encodage Windows."""
    membres = {}
    if not os.path.exists(MEMBRES_CSV):
        print(f"[Erreur] Fichier {MEMBRES_CSV} introuvable.")
        return membres

    with open(MEMBRES_CSV, mode='r', encoding='latin-1') as f:
        premiere_ligne = f.readline()
        separateur = ';' if ';' in premiere_ligne else ','
        f.seek(0)
        
        reader = csv.DictReader(f, delimiter=separateur)
        for row in reader:
            row_propre = {str(k).strip(' \ufeffï»¿').lower(): str(v).strip() for k, v in row.items() if k}
            nom = row_propre.get("nom", "")
            prenom = row_propre.get("prenom", "")
            equipe = row_propre.get("equipe", "")
            
            if nom and prenom:
                nom_complet = f"{prenom} {nom}"
                nom_fichier = nom_complet.replace(' ', '_')
                membres[nom_fichier] = {"nom_complet": nom_complet, "equipe": equipe}
    return membres

def main():
    print("Début du parsing des données DBLP...")
    membres = charger_membres()
    if not membres:
        print("[Erreur] Aucun membre chargé. Arrêt du parsing.")
        return

    publications = []
    
    for nom_fichier, infos in membres.items():
        xml_path = os.path.join(CACHE_DBLP_DIR, f"{nom_fichier}.xml")
        if not os.path.exists(xml_path):
            continue
            
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Parcours des publications dans le XML DBLP
            for r in root.findall('r'):
                pub_node = r[0] 
                type_pub = pub_node.tag
                
                if type_pub not in ['article', 'inproceedings']:
                    continue
                    
                year_node = pub_node.find('year')
                if year_node is None or not year_node.text.isdigit():
                    continue
                    
                year = int(year_node.text)
                if not (ANNEE_DEBUT <= year <= ANNEE_FIN):
                    continue
                    
                title_node = pub_node.find('title')
                title = title_node.text if title_node is not None else "Titre inconnu"
                
                # Détection Revue ou Conférence
                venue = ""
                if type_pub == 'article':
                    journal_node = pub_node.find('journal')
                    venue = journal_node.text if journal_node is not None else ""
                    type_propre = "Revue"
                else:
                    booktitle_node = pub_node.find('booktitle')
                    venue = booktitle_node.text if booktitle_node is not None else ""
                    type_propre = "Conférence"
                    
                publications.append({
                    "auteur": infos["nom_complet"],
                    "equipe": infos["equipe"],
                    "titre": title,
                    "annee": year,
                    "type_publi": type_propre,
                    "venue": venue
                })
        except Exception as e:
            print(f"  [Erreur] Impossible de parser le fichier de {infos['nom_complet']}: {e}")

    # Sauvegarde du fichier CSV
    os.makedirs("../cache", exist_ok=True)
    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as f:
        if publications:
            writer = csv.DictWriter(f, fieldnames=["auteur", "equipe", "titre", "annee", "type_publi", "venue"])
            writer.writeheader()
            writer.writerows(publications)
            print(f"[Succès] {len(publications)} publications parsées et sauvegardées dans {OUTPUT_CSV}")
        else:
            print("[Alerte] Aucune publication trouvée sur la période.")

# C'est souvent ces deux lignes qui manquent quand un script ne fait rien !
if __name__ == "__main__":
    main()