import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os  
import numpy as np

# Configuration de la page en mode "Large"
st.set_page_config(page_title="Dashboard LIAS", page_icon="📊", layout="wide")

st.title("📊 Tableau de Bord - Laboratoire LIAS")
st.markdown("---")

# On lit la variable d'environnement Docker, sinon on prend l'adresse par défaut de Docker (api:8000)
API_URL = os.getenv("API_URL", "http://api:8000")

# Fonction de récupération des données (avec la correction anti-proxy)
def fetch_data(endpoint):
    try:
        proxies = {"http": None, "https": None}
        response = requests.get(f"{API_URL}/{endpoint}", timeout=10, proxies=proxies)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.sidebar.error(f"Erreur de connexion API : {e}")
    return []

# Fonction pour calculer l'indice de Gini (placée en haut proprement)
def gini(array):
    """Calcule l'indice de Gini (0 = égalité parfaite, 1 = inégalité totale)."""
    array = np.array(array, dtype=np.float64)
    if np.amin(array) < 0: array -= np.amin(array)
    array += 0.0000001 # Évite la division par zéro
    array = np.sort(array)
    index = np.arange(1,array.shape[0]+1)
    n = array.shape[0]
    return ((np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array)))

# 1. Chargement des données
publications_data = fetch_data("publications")
theses_data = fetch_data("theses")

if publications_data:
    # Transformation en DataFrame Pandas
    df_publis = pd.DataFrame(publications_data)
    df_theses = pd.DataFrame(theses_data) if theses_data else pd.DataFrame()

    # ==========================================
    # BARRE LATÉRALE (SIDEBAR) - LES FILTRES
    # ==========================================
    st.sidebar.image("https://www.lias-lab.fr/wp-content/uploads/2021/06/logo-lias.png", use_container_width=True)
    st.sidebar.header("🔍 Filtres de recherche")
    
    # Filtre par Équipe
    liste_equipes = ["Toutes"] + sorted(df_publis["equipe"].dropna().unique().tolist())
    choix_equipe = st.sidebar.selectbox("1️⃣ Sélectionner une équipe", liste_equipes)
    
    # On applique le filtre Équipe si ce n'est pas "Toutes"
    if choix_equipe != "Toutes":
        df_publis = df_publis[df_publis["equipe"] == choix_equipe]
        
    # Filtre par Chercheur (mis à jour en fonction de l'équipe choisie)
    liste_chercheurs = ["Tous"] + sorted(df_publis["auteur"].dropna().unique().tolist())
    choix_chercheur = st.sidebar.selectbox("2️⃣ Sélectionner un chercheur", liste_chercheurs)
    
    # On applique le filtre Chercheur
    if choix_chercheur != "Tous":
        df_publis = df_publis[df_publis["auteur"] == choix_chercheur]
        # On filtre aussi les thèses si on a choisi un chercheur précis
        if not df_theses.empty and "directeur" in df_theses.columns:
            df_theses = df_theses[df_theses["directeur"].str.contains(choix_chercheur, case=False, na=False)]

    # ==========================================
    # CONTENU PRINCIPAL - LES ONGLETS (TABS)
    # ==========================================
    # CORRECTION ICI : On crée bien les 3 onglets en même temps !
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Publications", "🎓 Thèses", "📈 Analyse Stratégique", "🧪 Simulateur & Réseau"])
    
    # ONGLET 1 : PUBLICATIONS
    with tab1:
        st.subheader(f"Indicateurs de Publications (2021-2025) - {choix_chercheur if choix_chercheur != 'Tous' else choix_equipe}")
        
        # Les KPIs
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Publications", len(df_publis))
        col2.metric("Chercheurs impliqués", df_publis["auteur"].nunique())
        col3.metric("Conférences / Revues", df_publis["type_publi"].nunique())
        
        if not df_publis.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            # Graphique interactif
            df_publis['annee_str'] = df_publis['annee'].astype(str)
            fig = px.histogram(df_publis, x="annee_str", color="type_publi", 
                               title="Évolution annuelle des publications",
                               labels={"annee_str": "Année", "type_publi": "Type de publication"},
                               barmode="group", color_discrete_sequence=["#1f77b4", "#ff7f0e"])
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau de données
            st.subheader("Base de données détaillée")
            st.dataframe(df_publis[["auteur", "equipe", "titre", "annee", "type_publi", "venue"]], use_container_width=True)
        else:
            st.info("Aucune publication trouvée pour ces critères.")
            
    # ONGLET 2 : THÈSES
    with tab2:
        st.subheader("Indicateurs d'encadrement Doctoral")
        
        if not df_theses.empty:
            c1, c2 = st.columns(2)
            c1.metric("Total Thèses trouvées", len(df_theses))
            
            # Compter combien sont en cours vs soutenues
            statuts = df_theses["statut"].value_counts().to_dict()
            en_cours = statuts.get("En cours", 0)
            c2.metric("Thèses en cours", en_cours)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df_theses, use_container_width=True)
        else:
            st.info("Aucune thèse trouvée pour cette sélection sur la période 2021-2025.")
    
    # ONGLET 3 : ANALYSE STRATÉGIQUE
    with tab3:
        st.header("6.1 Analyse de la Fusion IDD + SETR")
        
        # Filtrer uniquement IDD et SETR (on annule les filtres de la sidebar pour cette analyse globale)
        df_fusion = pd.DataFrame(publications_data)
        df_fusion = df_fusion[df_fusion['equipe'].isin(['IDD', 'SETR'])]
        
        if not df_fusion.empty:
            col1, col2 = st.columns(2)
            # Productivité brute
            prod_equipe = df_fusion.groupby('equipe')['titre'].count()
            membres_equipe = df_fusion.groupby('equipe')['auteur'].nunique()
            ratio_prod = prod_equipe / membres_equipe
            
            col1.write("**Volume total par équipe :**")
            col1.dataframe(prod_equipe)
            
            col2.write("**Productivité par membre :**")
            col2.dataframe(ratio_prod)

            st.header("6.2 Qualité des publications")
            if 'rang_core' in df_fusion.columns:
                fig_qualite = px.histogram(df_fusion, x="equipe", color="rang_core", 
                                        title="Répartition des Conférences par Rang CORE",
                                        barmode="stack")
                st.plotly_chart(fig_qualite, use_container_width=True)
            else:
                st.info("La colonne 'rang_core' n'est pas disponible dans les données actuelles.")

            st.header("6.3 Dépendance et Inégalités")
        
            for equipe in ['IDD', 'SETR']:
                st.subheader(f"Équipe {equipe}")
                df_eq = df_fusion[df_fusion['equipe'] == equipe]
                
                if not df_eq.empty:
                    prod_chercheurs = df_eq['auteur'].value_counts()
                    
                    # Calcul Gini
                    indice_gini = gini(prod_chercheurs.values)
                    st.metric(f"Indice de Gini ({equipe})", round(indice_gini, 2))
                    
                    # Locomotives (>25%)
                    total_eq = len(df_eq)
                    locomotives = prod_chercheurs[prod_chercheurs > (0.25 * total_eq)]
                    if not locomotives.empty:
                        st.write("Locomotives (>25% de la prod de l'équipe) :")
                        st.dataframe(locomotives)
                    else:
                        st.write("Aucune locomotive écrasante (>25%) détectée.")

            st.header("6.4 Dynamiques")
            dynamique = df_fusion.groupby(['annee', 'equipe']).size().reset_index(name='Nombre')
            if not dynamique.empty:
                fig_dyn = px.line(dynamique, x="annee", y="Nombre", color="equipe", title="Évolution des publications (2021-2025)")
                fig_dyn.update_xaxes(type='category') # Pour forcer l'affichage propre des années
                st.plotly_chart(fig_dyn, use_container_width=True)

            st.header("6.5 Projections 2026-2030 (Équipe Fusionnée IDD+SETR)")
        
            # 1. Préparer les données historiques (2021-2025)
            historique = df_fusion.groupby('annee').size().reset_index(name='Total')
            historique['annee'] = historique['annee'].astype(int)
            
            if len(historique) > 1:
                # 2. Modèle de régression linéaire simple (Baseline)
                x = historique['annee'] - 2021
                y = historique['Total']
                coef = np.polyfit(x, y, 1) 
                
                # 3. Créer les projections
                annees_futures = np.array([2026, 2027, 2028, 2029, 2030])
                x_futur = annees_futures - 2021
                
                baseline = coef[0] * x_futur + coef[1]
                optimiste = baseline * 1.15
                pessimiste = baseline * 0.70
                
                # 4. Affichage Graphique
                df_proj = pd.DataFrame({
                    'Année': np.concatenate([historique['annee'], annees_futures, annees_futures, annees_futures]),
                    'Volume': np.concatenate([historique['Total'], baseline, optimiste, pessimiste]),
                    'Scénario': ['Historique']*len(historique) + ['Baseline']*5 + ['Optimiste (+15%)']*5 + ['Pessimiste (-30%)']*5
                })
                
                fig_proj = px.line(df_proj, x='Année', y='Volume', color='Scénario', 
                                title="Projections de la fusion IDD+SETR", markers=True)
                fig_proj.update_traces(line=dict(width=4), selector=dict(name='Historique'))
                st.plotly_chart(fig_proj, use_container_width=True)
            else:
                st.info("Pas assez de données historiques pour faire une projection linéaire.")
        else:
             st.warning("Aucune donnée trouvée pour les équipes IDD et SETR.")

        # ONGLET 4 : SIMULATEUR ET RÉSEAU
        with tab4:
            import networkx as nx
            st.header("🕸️ Graphe de Collaboration (Co-publications)")
            
            # 1. Création du graphe de collaboration
            # On regroupe les auteurs qui ont publié le même titre d'article
            co_publis = df_publis.groupby('titre')['auteur'].apply(list)
            
            G = nx.Graph()
            for authors in co_publis:
                # S'il y a plus d'un auteur du labo sur le même article = collaboration !
                if len(authors) > 1:
                    # On enlève les doublons si un auteur apparaît 2 fois
                    authors = list(set(authors)) 
                    for i in range(len(authors)):
                        for j in range(i+1, len(authors)):
                            if G.has_edge(authors[i], authors[j]):
                                G[authors[i]][authors[j]]['weight'] += 1
                            else:
                                G.add_edge(authors[i], authors[j], weight=1)
            
            if G.number_of_edges() > 0:
                # Dessin du graphe avec NetworkX et matplotlib (converti pour Streamlit)
                import matplotlib.pyplot as plt
                fig_net, ax = plt.subplots(figsize=(10, 6))
                pos = nx.spring_layout(G, k=0.5)
                
                # Récupération des couleurs par équipe
                color_map = []
                for node in G:
                    eq = df_publis[df_publis['auteur'] == node]['equipe'].iloc[0]
                    color_map.append('skyblue' if eq == 'IDD' else 'lightgreen')
                    
                nx.draw(G, pos, with_labels=True, node_color=color_map, node_size=2000, 
                        font_size=10, font_weight="bold", edge_color="gray", ax=ax)
                st.pyplot(fig_net)
                st.caption("🟢 Vert = SETR | 🔵 Bleu = IDD. Les liens représentent les articles co-écrits.")
            else:
                st.info("Aucune co-publication stricte détectée entre les membres actuels de la base de données.")

            st.markdown("---")
            st.header("🔮 Module de Simulation (Marginalisation & Transfert)")
            
            col_sim1, col_sim2 = st.columns(2)
            
            with col_sim1:
                st.subheader("Paramètres de simulation")
                sim_chercheur = st.selectbox("Choisir un chercheur cible", df_publis['auteur'].unique())
                equipe_actuelle = df_publis[df_publis['auteur'] == sim_chercheur]['equipe'].iloc[0]
                st.write(f"Équipe actuelle : **{equipe_actuelle}**")
                
                sim_action = st.radio("Action à simuler :", 
                                    ["Marginalisation (Baisse de production)", "Transfert d'équipe"])
                
                if sim_action == "Marginalisation (Baisse de production)":
                    baisse = st.slider("Pourcentage de baisse de production", 0, 100, 50)
                    transfert_eq = equipe_actuelle
                else:
                    transfert_eq = st.radio("Transférer vers :", ["IDD", "SETR"])
                    baisse = 0
                    
            with col_sim2:
                st.subheader("Impact sur l'équipe IDD+SETR")
                
                # Copie des données pour la simulation
                df_sim = df_publis[df_publis['equipe'].isin(['IDD', 'SETR'])].copy()
                
                # Application du transfert
                if sim_action == "Transfert d'équipe":
                    df_sim.loc[df_sim['auteur'] == sim_chercheur, 'equipe'] = transfert_eq
                    
                # Calculs
                prod_avant = df_publis[df_publis['equipe'].isin(['IDD', 'SETR'])].groupby('equipe')['titre'].count()
                
                # Application de la baisse (on retire un % d'articles aléatoires du chercheur)
                if baisse > 0:
                    articles_chercheur = df_sim[df_sim['auteur'] == sim_chercheur]
                    nb_a_supprimer = int(len(articles_chercheur) * (baisse / 100.0))
                    if nb_a_supprimer > 0:
                        indices_a_supprimer = articles_chercheur.sample(nb_a_supprimer).index
                        df_sim = df_sim.drop(indices_a_supprimer)
                
                prod_apres = df_sim.groupby('equipe')['titre'].count()
                
                # Affichage des métriques comparatives
                st.write("📊 **Volume de publications**")
                m1, m2 = st.columns(2)
                
                idd_avant = prod_avant.get('IDD', 0)
                idd_apres = prod_apres.get('IDD', 0)
                m1.metric("Équipe IDD", f"{idd_apres} publis", delta=int(idd_apres - idd_avant))
                
                setr_avant = prod_avant.get('SETR', 0)
                setr_apres = prod_apres.get('SETR', 0)
                m2.metric("Équipe SETR", f"{setr_apres} publis", delta=int(setr_apres - setr_avant))
                
                # Productivité par membre
                st.write("👨‍🔬 **Productivité par membre**")
                membres_avant = df_publis[df_publis['equipe'].isin(['IDD', 'SETR'])].groupby('equipe')['auteur'].nunique()
                membres_apres = df_sim.groupby('equipe')['auteur'].nunique()
                
                p1, p2 = st.columns(2)
                ratio_idd_avant = idd_avant / membres_avant.get('IDD', 1)
                ratio_idd_apres = idd_apres / membres_apres.get('IDD', 1)
                p1.metric("Ratio IDD", round(ratio_idd_apres, 1), delta=round(ratio_idd_apres - ratio_idd_avant, 1))
                
                ratio_setr_avant = setr_avant / membres_avant.get('SETR', 1)
                ratio_setr_apres = setr_apres / membres_apres.get('SETR', 1)
                p2.metric("Ratio SETR", round(ratio_setr_apres, 1), delta=round(ratio_setr_apres - ratio_setr_avant, 1))

else:
    st.warning("⚠️ Impossible de charger les données. Vérifiez que l'API tourne bien.")