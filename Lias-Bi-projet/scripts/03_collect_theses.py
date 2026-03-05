import os
import csv
import time
import requests

# --- Configuration des chemins ---
MEMBRES_CSV = "../data/membres.csv"
OUTPUT_CSV = "../cache/theses_brutes.csv"
DELAY = 2  # Respect du serveur

# Période ciblée
ANNEE_DEBUT = 2021
ANNEE_FIN = 2025

def chercher_theses_directeur(nom, prenom):
    """Interroge l'API de theses.fr avec une recherche plus large et robuste."""
    theses = []
    nom_complet = f"{prenom} {nom}"
    
    # Recherche plus large par mots-clés simples sur le nom et prénom
    url = f"https://theses.fr/api/v1/theses/recherche/?q={nom}%20{prenom}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Adaptation intelligente à la structure JSON de theses.fr (qui change parfois)
        resultats = []
        if 'response' in data and 'docs' in data['response']:
            resultats = data['response']['docs']  # Format Solr classique
        elif 'theses' in data:
            resultats = data['theses']
        elif isinstance(data, list):
            resultats = data
        elif 'hydra:member' in data:
            resultats = data['hydra:member']
            
        for t in resultats:
            # Récupération sécurisée des champs (selon les différentes versions de l'API)
            titre = t.get('titrePrincipal', t.get('titre', 'Titre inconnu'))
            statut = str(t.get('status', t.get('statut', ''))).lower()
            
            # Extraction de l'année
            annee = ""
            if t.get('date_soutenance'):
                annee = str(t.get('date_soutenance'))[:4]
            elif t.get('dateSoutenance'):
                annee = str(t.get('dateSoutenance'))[:4]
                
            # Vérification très souple de la période
            if annee.isdigit() and not (ANNEE_DEBUT <= int(annee) <= ANNEE_FIN):
                continue
                
            # Si on ne trouve pas de statut explicite mais une année dans notre période, on valide
            statut_propre = "Soutenue" if 'soutenue' in statut or annee else "En cours"
            annee_finale = annee if annee else "En cours"
            
            # On vérifie si c'est bien notre chercheur le directeur
            directeurs = str(t.get('directeur', t.get('directeurs_these', '')))
            if nom.lower() in directeurs.lower():
                theses.append({
                    "directeur": nom_complet,
                    "titre": titre,
                    "doctorant": t.get('auteur', {}).get('nom_prenom', t.get('auteur', 'Inconnu')),
                    "statut": statut_propre,
                    "annee": annee_finale
                })
            
    except Exception as e:
        print(f"  [Alerte] Problème avec l'API theses.fr pour {nom_complet}: {e}")
        
    return theses