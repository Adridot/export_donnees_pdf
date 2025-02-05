import os
import time
import fitz  # PyMuPDF
import google.generativeai as genai
import pandas as pd
import json
import ssl
import requests

# 🔧 Désactiver la vérification SSL (Fix temporaire pour les réseaux d'entreprise)
ssl._create_default_https_context = ssl._create_unverified_context
requests.packages.urllib3.disable_warnings()

API_KEY = input("🔑 Enter your Gemini API key: ").strip()

genai.configure(api_key=API_KEY)

print("✅ API key configured successfully!")

# Sélection du modèle Gemini
model = genai.GenerativeModel("gemini-1.5-flash")

# 📌 Définition des colonnes pour le fichier Excel
COLUMNS = [
    "Raison sociale", "Sigle", "Responsabilité légale", "Adresse", "Téléphone", "Portable", "E-mail",
    "Site Internet", "SIRET", "Code NACE", "Assurance Travaux",
    "Assurance Civile", "Effectif moyen", "Chiffre d’affaires H.T.", "Qualifications professionnelles"
]

# ⏳ Gestion du quota API (attendre 1 min toutes les 10 requêtes)
MAX_REQUESTS_BEFORE_PAUSE = 10
request_count = 0

def extraire_texte_pdf(chemin_fichier):
    """Extrait le texte d'un fichier PDF."""
    texte = ""
    try:
        with fitz.open(chemin_fichier) as doc:
            for page in doc:
                texte += page.get_text() + "\n"
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction du texte ({chemin_fichier}): {e}")
    return texte

def limiter_requetes():
    """Gère le quota de requêtes en ajoutant une pause de 1 minute toutes les 10 requêtes."""
    global request_count
    request_count += 1

    if request_count % MAX_REQUESTS_BEFORE_PAUSE == 0:
        print("⏳ Limite atteinte ! Pause de 1 minute...")
        time.sleep(60)  # Pause de 1 minute

def analyser_contenu_avec_gemini(contenu):
    """Envoie le texte extrait à l'API Gemini et récupère les informations formatées."""

    prompt = f"""
Analyse ce document et extrais les informations suivantes :
- Raison sociale
- Sigle
- Responsabilité légale (Nom et fonction des principaux responsables légaux, ex: "MERGUI CYRIL RESPONSABLE DE SERVICE" ou "PILLOT EPOUSE NAHI CATHERINE GÉRANT(E) ASSOCIÉ(E) MAJORITAIRE / NAHI NORDINE CO-GÉRANT")
- Adresse complète
- Téléphone et portable
- Email
- Site Internet
- SIRET
- Code NACE
- Assurance Travaux
- Assurance Civile
- Effectif moyen
- Chiffre d'affaires HT (si disponible)
- Qualifications professionnelles (avec retour à la ligne entre chaque entrée)

Donne la réponse au format **JSON** structuré, comme ceci :
```json
{{
"Raison sociale": "...",
"Sigle": "...",
"Responsabilité légale": "...",
"Adresse": "...",
"Téléphone": "...",
"Portable": "...",
"E-mail": "...",
"Site Internet": "...",
"SIRET": "...",
"Code NACE": "...",
"Assurance Travaux": "...",
"Assurance Civile": "...",
"Effectif moyen": "...",
"Chiffre d’affaires H.T.": "...",
"Qualifications professionnelles": "..."
}}
```

Contenu du fichier PDF :
        {contenu}
        """

    try:
        limiter_requetes()  # 🔹 Vérifie la limite d'API avant d'envoyer la requête
        response = model.generate_content(prompt)
        result = response.text  # Obtenir le texte brut

        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()  # Extraction JSON

        # Utilisation de json.loads() pour éviter les erreurs de `null`
        parsed_data = json.loads(result)

        return parsed_data
    except json.JSONDecodeError as e:
        print(f"⚠️ Erreur de parsing JSON : {e}")
    except Exception as e:
        print(f"⚠️ Erreur avec Gemini : {e}")

    return None

def traiter_dossier_pdf(chemin_dossier):
    """Parcourt un dossier, extrait et analyse les PDF puis génère un fichier Excel."""
    donnees = []

    for nom_fichier in os.listdir(chemin_dossier):
        if nom_fichier.endswith(".pdf"):
            chemin_complet = os.path.join(chemin_dossier, nom_fichier)
            print(f"📄 Traitement du fichier : {nom_fichier}")

            texte = extraire_texte_pdf(chemin_complet)
            if texte:
                resultat = analyser_contenu_avec_gemini(texte)
                if resultat:
                    donnees.append(resultat)
                else:
                    print(f"⚠️ Aucune réponse obtenue pour {nom_fichier}")
            else:
                print(f"⚠️ Aucun texte extrait pour {nom_fichier}")

    # 📊 Génération du fichier Excel
    if donnees:
        df = pd.DataFrame(donnees, columns=COLUMNS)
        df["Qualifications professionnelles"] = df["Qualifications professionnelles"].str.replace(";", "\n")  # Retour à la ligne
        fichier_sortie = os.path.join(chemin_dossier, "export_qualifications.xlsx")
        df.to_excel(fichier_sortie, index=False)
        print(f"✅ Extraction terminée ! Fichier généré : {fichier_sortie}")

if __name__ == "__main__":
    chemin_dossier = input("Entrez le chemin du dossier contenant les fichiers PDF : ")
    traiter_dossier_pdf(chemin_dossier)