import streamlit as st
import pandas as pd
from scraper import scraper_coinafrique
from database import charger_donnees, sauvegarder_donnees
import base64
import os
import plotly.express as px
import re
import sqlite3


# Configuration de la page
st.set_page_config(page_title="CoinAfrique Dashboard", layout="wide")

# CSS personnalisé pour un look premium
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
    }
    [data-testid="stSidebar"] {
        background-color: #F8FCFC;
        border-right: 1px solid #E0EDED;
    }
    [data-testid="stSidebar"] .stRadio > div {
        background-color: transparent;
        padding: 5px;
    }
    [data-testid="stSidebar"] .stRadio label {
        background-color: #FFFFFF;
        border: 1px solid #E0EDED;
        border-radius: 8px;
        padding: 10px 15px !important;
        margin-bottom: 8px;
        transition: 0.3s;
        cursor: pointer;
        width: 100%;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        border-color: #008080;
        background-color: #F0F9F9;
        transform: translateX(5px);
    }
    /* Style des boutons radio transformés en menu */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label {
        background-color: #FFFFFF !important;
        border: 1px solid #E0EDED !important;
        border-radius: 12px !important;
        padding: 12px 20px !important;
        margin-bottom: 12px !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        width: 100% !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        display: flex !important;
        align-items: center !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        border-color: #008080 !important;
        background-color: #F0F9F9 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05) !important;
    }

    /* Cacher le bouton radio lui-même mais PAS le texte */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* Style du texte du menu */
    [data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] span {
        color: #262730 !important;
        font-weight: 500 !important;
        font-size: 1.1rem !important;
        margin: 0 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    .stMetric {
        background-color: #F0F9F9;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #008080;
    }
    div.stButton > button:first-child {
        background-color: #008080;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #006666;
        color: white;
        transform: scale(1.02);
    }
    h1 {
        color: #008080;
    }
    h2 {
        color: #006666;
        border-bottom: 2px solid #F0F9F9;
        padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Fonction pour permettre le téléchargement
def download_button(df, filename, file_format):
    if file_format == 'CSV':
        data = df.to_csv(index=False).encode('utf-8')
        mime = 'text/csv'
    elif file_format == 'Excel':
        # Nécessite openpyxl
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        data = output.getvalue()
        mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    st.download_button(
        label=f"Télécharger en {file_format}",
        data=data,
        file_name=f"{filename}.{file_format.lower()}",
        mime=mime
    )

# Titre principal
st.title("🛍️ CoinAfrique Data Explorer")

# Barre latérale pour la navigation
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("📌 Menu")
    menu = st.radio(
        "Choisissez une fonctionnalité :",
        [
            "🏠 Accueil & Scraping", 
            "📂 Données brutes", 
            "📊 Dashboard & Analyse", 
            "📥 Importation CSV", 
            "📝 Évaluation"
        ],
        label_visibility="collapsed"
    )

# Conversion des noms de menu pour la logique interne
menu_key = menu.split(" ")[1] if " " in menu else menu

# --- SECTION 1 : SCRAPER DES DONNÉES ---
if "Accueil" in menu:
    st.header("🔍 Scraping en temps réel")
    
    col1, col2 = st.columns(2)
    with col1:
        categorie = st.selectbox(
            "Choisir une catégorie :",
            ["vetements-homme", "chaussures-homme", "vetements-enfants", "chaussures-enfants"]
        )
    with col2:
        nb_pages = st.number_input("Nombre de pages à scraper :", min_value=1, max_value=50, value=3)

    if st.button("Lancer le Scraping"):
        with st.spinner("Scraping en cours..."):
            # Déterminer le nom de la colonne selon la catégorie
            if "chaussures" in categorie:
                nom_colonne = "type_chaussures"
            else:
                nom_colonne = "type_habits"
                
            df_resultat = scraper_coinafrique(categorie, nom_colonne, nb_pages)
            
            if not df_resultat.empty:
                st.success(f"Scraping terminé ! {len(df_resultat)} éléments trouvés.")
                st.dataframe(df_resultat)
                
                # Téléchargement
                format_choisi = st.selectbox("Format de téléchargement :", ["CSV", "Excel"])
                download_button(df_resultat, f"scraped_{categorie}", format_choisi)
            else:
                st.warning("Aucune donnée trouvée.")

# --- SECTION 2 : DONNÉES BRUTES ---
elif "Données" in menu:
    st.header("🗄️ Consultation des données brutes")
    st.info("Ces données proviennent de la table `data_brutes` de la base `BD_coinafrique`.")
    
    df_brut = charger_donnees("data_brutes")
    
    if not df_brut.empty:
        # Extraire les catégories pour le sélecteur
        def get_cat(url):
            import re
            match = re.search(r'categorie/([^?]+)', str(url))
            return match.group(1) if match else 'Autres'
            
        if 'web_scraper_start_url' in df_brut.columns:
            df_brut['categorie_filtre'] = df_brut['web_scraper_start_url'].apply(get_cat)
            # On enlève "Toutes" pour forcer le choix d'une catégorie
            liste_cats = sorted(df_brut['categorie_filtre'].unique().tolist())
            
            if liste_cats:
                choix_cat = st.selectbox("🎯 Choisir la catégorie à afficher :", liste_cats)
                df_filtre = df_brut[df_brut['categorie_filtre'] == choix_cat].reset_index(drop=True)
            else:
                df_filtre = df_brut.reset_index(drop=True)
        else:
            df_filtre = df_brut.reset_index(drop=True)

        # 1. Masquer les colonnes techniques de base
        cols_techniques = ['web_scraper_order', 'web_scraper_start_url', 'container_links', 'categorie_filtre']
        df_affichage = df_filtre.drop(columns=[c for c in cols_techniques if c in df_filtre.columns], errors='ignore')
        
        # 2. Masquer dynamiquement les colonnes qui sont entièrement vides
        df_affichage = df_affichage.dropna(axis=1, how='all')

        # 3. Réorganiser les colonnes : celles contenant 'type' en premier
        cols = list(df_affichage.columns)
        type_cols = [c for c in cols if 'type' in c.lower()]
        other_cols = [c for c in cols if 'type' not in c.lower()]
        df_affichage = df_affichage[type_cols + other_cols]

        st.write(f"Affichage de **{len(df_affichage)}** résultats pour la catégorie **{choix_cat if 'choix_cat' in locals() else ''}**.")
        st.dataframe(df_affichage)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            format_choisi = st.selectbox("Format :", ["CSV", "Excel"])
        with col2:
            st.write("---")
            download_button(df_affichage, f"donnees_brutes_{choix_cat if 'choix_cat' in locals() else 'completes'}", format_choisi)
    else:
        st.warning("La base de données brute est vide. Vérifiez le dossier 'no clean data'.")

# --- SECTION 3 : DASHBOARD & ANALYSE ---
elif "Dashboard" in menu:
    st.header("📊 Tableau de Bord des données nettoyées")
    
    # 1. Chargement des données et jointure robuste pour la catégorie
    df_clean = charger_donnees("data_clean")
    df_brut_all = charger_donnees("data_brutes")
    df_nettoyee = pd.DataFrame()
    
    if not df_clean.empty:
        if not df_brut_all.empty:
            # On extrait l'URL pure de la colonne brute pour pouvoir faire la jointure
            def extract_pure_url(text):
                if pd.isna(text): return None
                import re
                match = re.search(r'url\("([^"]+)"\)', str(text))
                return match.group(1) if match else str(text)

            df_brut_all['url_image_pure'] = df_brut_all['url_image'].apply(extract_pure_url)
            
            # Jointure pour récupérer web_scraper_start_url
            df_nettoyee = pd.merge(
                df_clean, 
                df_brut_all[['url_image_pure', 'web_scraper_start_url']].drop_duplicates('url_image_pure'),
                left_on='url_image', 
                right_on='url_image_pure', 
                how='left'
            )
        else:
            df_nettoyee = df_clean.copy()
            df_nettoyee['web_scraper_start_url'] = None
    
    if not df_nettoyee.empty:
        # Extraire la catégorie via l'URL (même logique que Données brutes)
        def get_cat(url):
            import re
            match = re.search(r'categorie/([^?]+)', str(url))
            return match.group(1) if match else 'Autres'
            
        df_nettoyee['categorie_exacte'] = df_nettoyee['web_scraper_start_url'].apply(get_cat)

        # 2. Nettoyage du prix pour les analyses numériques
        def clean_price(p):
            if pd.isna(p) or str(p).lower() == 'none' or 'demande' in str(p).lower():
                return None
            try:
                # Enlever les espaces et convertir
                return float(str(p).replace(' ', '').replace('\xa0', ''))
            except:
                return None
        
        df_nettoyee['prix_num'] = df_nettoyee['price'].apply(clean_price)
        
        # Sélecteur de catégorie filtré comme dans les données brutes
        liste_cats_brutes = sorted(df_nettoyee['categorie_exacte'].unique().tolist())
        cat_dashboard = st.selectbox("🎯 Choisir la catégorie à afficher :", liste_cats_brutes)
        
        df_dash = df_nettoyee[df_nettoyee['categorie_exacte'] == cat_dashboard].copy()

        # 3. MASQUAGE DYNAMIQUE DES COLONNES VIDES
        # On enlève les colonnes techniques pour l'affichage propre
        cols_to_hide = ['web_scraper_start_url', 'categorie_exacte', 'prix_num', 'url_image_pure', 'url_image_pure_y']
        df_display = df_dash.drop(columns=[c for c in cols_to_hide if c in df_dash.columns], errors='ignore')
        # On cache les colonnes qui n'ont que des None/NaN pour cette catégorie
        df_display = df_display.dropna(axis=1, how='all')

        # Affichage des données
        st.divider()
        col_title, col_download = st.columns([4, 1])
        with col_title:
            st.subheader(f"📋 Données nettoyées ({cat_dashboard})")
        with col_download:
             download_button(df_dash, f"donnees_nettoyées_{cat_dashboard}", "CSV")
        
        st.dataframe(df_display, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Nombre d'articles", len(df_dash))
        if not df_dash.empty and df_dash['prix_num'].notna().any():
            avg_p = int(df_dash['prix_num'].mean())
            col2.metric("Prix Moyen", f"{avg_p:,} CFA".replace(',', ' '))
            # Pour le mode, on prend la colonne de type non vide la plus fréquente
            type_cols = [c for c in df_display.columns if 'type' in c.lower()]
            if type_cols:
                mode_val = df_display[type_cols[0]].mode()[0] if not df_display[type_cols[0]].empty else "N/A"
                col3.metric("Élément le plus fréquent", mode_val)
            else:
                col3.metric("Catégorie", cat_dashboard)
        else:
            col2.metric("Prix Moyen", "N/A")
            col3.metric("Catégorie", cat_dashboard)

        st.divider()

        # Visualisations avec Plotly (Globales pour comparaison)
        st.subheader("Analyses Globales par Catégorie")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write("**Nombre d'articles par catégorie**")
            fig_count = px.bar(
                df_nettoyee['categorie_exacte'].value_counts().reset_index(),
                x='categorie_exacte',
                y='count',
                color='categorie_exacte',
                labels={'count': 'Nombre', 'categorie_exacte': 'Catégorie'},
                template="plotly_white"
            )
            st.plotly_chart(fig_count, use_container_width=True)
            
        with col_b:
            st.write("**Répartition des prix moyens par catégorie**")
            if not df_nettoyee.empty and df_nettoyee['prix_num'].notna().any():
                avg_price_cat = df_nettoyee.groupby('categorie_exacte')['prix_num'].mean().reset_index()
                fig_price = px.pie(
                    avg_price_cat, 
                    values='prix_num', 
                    names='categorie_exacte',
                    hole=0.4,
                    labels={'prix_num': 'Prix Moyen'}
                )
                st.plotly_chart(fig_price, use_container_width=True)

        st.divider()
        st.subheader("📦 Distribution Comparée des Prix par Catégorie")
        
        # Filtrer df_nettoyee pour enlever les prix nuls pour le graphique
        df_box = df_nettoyee[df_nettoyee['prix_num'].notna()].copy()
        
        fig_box = px.box(
            df_box, 
            x="categorie_exacte",
            y="prix_num", 
            color="categorie_exacte",
            points="outliers", # On garde seulement les outliers pour la clarté
            notched=True, # Design plus moderne et informatif
            labels={'prix_num': 'Prix (CFA)', 'categorie_exacte': 'Catégorie'},
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.T10 # Palette de couleurs plus premium
        )
        
        fig_box.update_layout(
            showlegend=False,
            xaxis_title="Catégories",
            yaxis_title="Prix (CFA)",
            margin=dict(l=20, r=20, t=40, b=20),
            height=500,
            hovermode="x unified"
        )
        
        st.plotly_chart(fig_box, use_container_width=True)
            
        # download_button moved near the table
    else:
        st.warning("Le fichier de données nettoyées n'a pas encore été généré par le Notebook.")
        st.info("Veuillez d'abord exécuter le Notebook `nettoyage_analyse.ipynb` ou lancer le script de nettoyage.")

# --- SECTION 4 : IMPORTATION ---
elif "Importation" in menu:
    st.header("📥 Importer vos données Web Scraper")
    st.write("Utilisez cette section pour charger vos fichiers CSV dans la base de données locale.")
    
    target_table = st.radio("Vers quelle table importer ?", ["donnees_brutes", "donnees_nettoyees"])
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv")
    
    if uploaded_file is not None:
        df_import = pd.read_csv(uploaded_file)
        st.write("Aperçu des données à importer :")
        st.dataframe(df_import.head())
        
        if st.button("Confirmer l'importation"):
            sauvegarder_donnees(df_import, target_table)
            st.success(f"Données importées avec succès dans {target_table} !")

# --- SECTION 5 : ÉVALUATION ---
elif "Évaluation" in menu:
    st.header("📝 Formulaire d'évaluation")
    st.write("Votre avis nous intéresse ! Veuillez remplir le formulaire ci-dessous :")
    
    url_kobo = "https://ee.kobotoolbox.org/x/gFdQf1a5"
    st.markdown(f"""
        <a href="{url_kobo}" target="_blank">
            <button style="
                background-color: #FF4B4B;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 8px;
                border: none;
            ">
                Ouvrir le formulaire KoboToolbox
            </button>
        </a>
    """, unsafe_allow_html=True)
    
    st.write("---")
    st.write("Vous pouvez également accéder au Google Form correspondant (si disponible).")
