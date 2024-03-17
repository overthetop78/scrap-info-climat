import calendar  # Importer le module de calendrier pour obtenir le nombre de jours dans un mois
import json
import re
from time import sleep

import requests
from bs4 import BeautifulSoup

"""
Ce script extrait les données de température mensuelles pour une station météo spécifique à partir du site Web d'InfoClimat.
Les données sont extraites pour chaque année, mois et jour, et écrites dans un fichier JSON.
"""

# Spécifier les en-têtes de la requête
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Numéro de la station météo
station = '07190'
station_name = 'strasbourg-entzheim'

# Spécifier l'année de début et de fin
annee_debut = 2009
annee_fin = 2024

# Spécifier l'année actuelle et le mois actuel
annee_actuelle = 2024
mois_actuel = 'mars'

# Initialiser une liste pour stocker les données de température
temperature_data = []
# Liste des mois
mois_liste = ['janvier', 'fevrier', 'mars', 'avril', 'mai', 'juin', 'juillet', 'aout', 'septembre', 'octobre', 'novembre', 'decembre']
# dossier de sortie
output_folder = "1-docs/tools/data"

# Fonction pour extraire les données de température à partir d'un lien
def scrape_temperature(station, mois, annee):
    # Construire l'URL en utilisant les paramètres fournis
    url = f"https://www.infoclimat.fr/climatologie-mensuelle/{station}/{mois}/{annee}/{station_name}.html"
    print(f"Récupération des données pour le mois de {mois} {annee}...")
    # Effectuer une requête GET avec les en-têtes spécifiés
    response = requests.get(url, headers=headers)
    # Vérifier si la requête s'est bien déroulée
    if response.status_code == 200:
        # Analyser le contenu HTML de la page
        soup = BeautifulSoup(response.text, 'html.parser')
        script = soup.find('script', string=re.compile(r'var\s+chart1\s+=\s+new\s+Highcharts.Chart'))
        if script is not None:
            # Utilisez une expression régulière pour extraire la partie spécifique du script
            pattern = r'var\s+chart1\s+=\s+new\s+Highcharts\.Chart\(\{.*?\}\)'
            match = re.search(pattern, script.string, re.DOTALL)
            if match is not None:
                series = re.search(r'series: (\[.*?\}\])', match.group(0), re.DOTALL)
                if series is not None:
                    seriesData = series.group(1)
                    # remplacer les caractères d'échappement dans la chaîne JSON par des caractères valides
                    seriesData = seriesData.replace('\351"', 'é')
                    seriesData = seriesData.replace('\\', '')
                    seriesData = seriesData[1:-1]
                    # séparer les données de la série en utilisant une expression régulière
                    patternSplit = r'\}\,'
                    seriesDataArray = re.split(patternSplit, seriesData)
                    tempDateArray = []                    
                    tempMaxArray = []
                    tempMinArray = []
                    if seriesDataArray[1] is not None:
                        # Température maximale, faire un tableau des données de data
                        maxTempData = re.search(r'data: (\[\[.*?\]\])', seriesDataArray[1], re.DOTALL)
                        if maxTempData is not None:
                            # Convertir la chaîne JSON en liste Python  
                            maxTempData = json.loads(maxTempData.group(1))
                            # Extraire les données de température maximale
                            for data in maxTempData:
                                    year = str(annee)
                                    month = str(mois_liste.index(mois) + 1)
                                    month = month.zfill(2)
                                    dayNumber = str(data[0])
                                    day = dayNumber.zfill(2)
                                    date = year + "-" + month + "-" + day
                                    temp_max = data[1]
                                    tempDateArray.append(date)
                                    tempMaxArray.append(temp_max)
                    if seriesDataArray[2] is not None:
                        # Température minimale, faire un tableau des données de data
                        minTempData = re.search(r'data: (\[\[.*?\]\])', seriesDataArray[2], re.DOTALL)
                        if minTempData is not None:
                            # Convertir la chaîne JSON en liste Python
                            minTempData = json.loads(minTempData.group(1))
                            # Extraire les données de température minimale
                            for data in minTempData:
                                year = str(annee)
                                month = str(mois_liste.index(mois) + 1)
                                month = month.zfill(2)
                                dayNumber = str(data[0])
                                day = dayNumber.zfill(2)
                                date = year + "-" + month + "-" + day
                                temp_min = data[1]
                                tempMinArray.append(temp_min)
                    monthDataArray = []  
                    for date in tempDateArray:
                        monthDataArray.append({
                            "date": date,
                            "temp_min": tempMinArray[tempDateArray.index(date)],
                            "temp_max": tempMaxArray[tempDateArray.index(date)]
                        })
                else:
                    print("Pas de match")
                    return None, None
            else : 
                print("Pas de match")
                return None, None
        else :
            print("Pas de script")
            return None, None
        return monthDataArray
    else:
        print(f"La requête a échoué avec le code d'état: {response.status_code}")
        return None, None


# Scraper les données pour chaque année, mois et jour
for annee in range(annee_debut, annee_fin+1):
    print(f"Récupération des données pour l'année {annee}...")
    # Initialiser une liste pour stocker les données de température pour l'année en cours
    yearDataArray = []
    for mois in range(1, 13):
        # Déterminer le nombre de jours dans le mois en fonction de l'année et du mois
        mois_str = mois_liste[mois - 1]
        # Vérifier si l'année et le mois actuels ont été atteints
        if(annee == annee_actuelle and mois_str == mois_actuel):
            # Si c'est le cas, arrêtez la boucle
            break
        # Récupérer les données de température pour le mois en cours
        response_value = scrape_temperature(station, mois_str, str(annee))
        if response_value is not None:
            monthDataArray = response_value
            # Ajouter les données de température à la liste
            yearDataArray.append(monthDataArray)
            sleep(2)
        else:
            print("Impossible de récupérer les données.")
    sleep(5)
    # Écrire les données dans un fichier JSON
    filename = f"{station_name}-{annee}.json"
    filename = f"{output_folder}/{filename}"
    with open(filename, "w") as f:
        json.dump(yearDataArray, f, indent=4)
    print(f"Les données ont été écrites dans le fichier {filename}.")
    # Ajouter toutes les données de température à la liste principale
    temperature_data.append({
        "annee": annee,
        "data": yearDataArray
    })
# Écrire les données dans un fichier JSON
filename = f"{output_folder}/{station_name}.json"
with open(filename, "w") as f:
    json.dump(temperature_data, f, indent=4)
print("Les données ont été écrites dans le fichier temperature_data.json.")
