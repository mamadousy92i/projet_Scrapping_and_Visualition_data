import pandas as pd
from requests import get
from bs4 import BeautifulSoup as bs
import streamlit as st

def scraper_coinafrique(categorie, nom_colonne_type, nb_pages=3):
    """
    Scrape les données de CoinAfrique pour une catégorie donnée.
    Code simplifié pour être facile à expliquer.
    """
    data = []

    for ind_page in range(1, nb_pages + 1):
        url = f'https://sn.coinafrique.com/categorie/{categorie}?page={ind_page}'
        try:
            res = get(url)
            res.raise_for_status() # Vérifie si la requête a réussi
        except Exception as e:
            st.error(f"Erreur lors de la récupération de la page {ind_page}: {e}")
            continue

        soup = bs(res.content, 'html.parser')
        # On cherche toutes les cartes d'annonces
        containers = soup.find_all("div", class_="col s6 m4 l3")

        for container in containers:
            try:
                # Titre/Type de produit
                type_produit = container.find('p', class_='ad__card-description').a.text.strip()

                # Prix (nettoyage simple)
                price_text = container.find('p', class_='ad__card-price').a.text
                price_text = price_text.strip().replace('CFA', '').replace(' ', '').replace('\xa0', '')
                price = float(price_text)

                # Adresse
                adresse = container.find('p', class_='ad__card-location').span.text.strip()

                # URL de l'image
                url_image = container.find('img', class_='ad__card-img')['src']

                # On ajoute les données dans une liste de dictionnaires
                dic = {
                    nom_colonne_type: type_produit,
                    'price': price,
                    'adress': adresse,
                    'url_image': url_image
                }
                data.append(dic)
            except Exception:
                pass

    # Conversion de la liste de dictionnaires en DataFrame pandas
    return pd.DataFrame(data)
