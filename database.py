import sqlite3
import pandas as pd

DB_NAME = "BD_coinafrique.db"

def charger_donnees(table_name):
    """Charge les données d'une table dans un DataFrame."""
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception as e:
        print(f"Erreur lors du chargement de {table_name}: {e}")
        df = pd.DataFrame()
    conn.close()
    return df

def sauvegarder_donnees(df, table_name):
    """Sauvegarde un DataFrame dans la table spécifiée."""
    conn = sqlite3.connect(DB_NAME)
    df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()
