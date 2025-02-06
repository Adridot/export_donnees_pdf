import os
import time
import fitz  # PyMuPDF
import google.generativeai as genai
import pandas as pd
import json
import logging
from google.api_core.exceptions import InternalServerError, ResourceExhausted

# Configuration du logger
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🔑 Demande de la clé API Gemini
API_KEY = input("🔑 Saisir la clé API Gemini : ").strip()
genai.configure(api_key=API_KEY)

logging.info("✅ Clé API ajoutée avec succès !")

# 📌 Définition des colonnes pour le fichier Excel
EXCEL_COLUMNS = [
    "Raison sociale", "Sigle", "Responsabilité légale", "Adresse", "Téléphone", "Portable", "E-mail",
    "Site Internet", "SIRET", "Code NACE", "Assurance Travaux",
    "Assurance Civile", "Effectif moyen", "Chiffre d’affaires H.T.", "Qualifications professionnelles"
]

# 📑 Sélection du modèle Gemini
gemini_model = genai.GenerativeModel("gemini-1.5-flash")


def extract_pdf_text(file_path):
    """Extrait le texte d'un fichier PDF."""
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'extraction du texte ({file_path}) : {e}")
    return text


def generate_prompt(content):
    """Génère le prompt à partir du contenu du PDF."""
    return f"""
        Analyse ce document et extrais les informations suivantes :
        - Raison sociale
        - Sigle
        - Responsabilité légale
        - Adresse complète
        - Téléphone et portable
        - Email
        - Site Internet
        - SIRET
        - Code NACE
        - Assurance Travaux
        - Assurance Civile
        - Effectif moyen
        - Chiffre d'affaires HT
        - Qualifications professionnelles

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
        {content}
        """


def analyze_content_with_gemini(content):
    """Envoie le texte extrait à l'API Gemini et récupère les informations formatées avec gestion des erreurs et retries."""
    prompt = generate_prompt(content)
    retries = 5
    attempt = 0
    while attempt < retries:
        try:
            response = gemini_model.generate_content(prompt)
            result = response.text
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            return json.loads(result)
        except json.JSONDecodeError:
            return None
        except InternalServerError:
            attempt += 1
            logging.warning(f"🔄 Erreur 500 détectée (tentative {attempt}/{retries}). Nouvelle tentative...")
        except ResourceExhausted:
            logging.warning("⚠️ Quota d'API dépassé. Attente de 60 secondes avant de réessayer...")
            time.sleep(60)
        except Exception as e:
            logging.error(f"⚠️ Erreur avec Gemini : {e}")
            break
    return None


def process_pdf_folder(folder_path):
    """Parcourt un dossier, extrait et analyse les PDF puis génère un fichier Excel."""
    extracted_data = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".pdf"):
            full_path = os.path.join(folder_path, file_name)
            print(f"📄 Traitement du fichier : {file_name}...", end="")
            pdf_text = extract_pdf_text(full_path)
            if pdf_text:
                extracted_info = analyze_content_with_gemini(pdf_text)
                if extracted_info:
                    extracted_data.append(extracted_info)
                    print(" ✅")
                else:
                    print(" ⚠️")
                    logging.warning(f"⚠️ Erreur lors du traitement de {file_name}, nouvelle tentative...")
                    print(f"🔄 Retraitement du fichier : {file_name}...")
                    extracted_info = analyze_content_with_gemini(pdf_text)
                    if extracted_info:
                        extracted_data.append(extracted_info)
                        print(f"✅ Succès après retry pour {file_name}")
                    else:
                        logging.error(f"❌ Impossible de traiter {file_name} après plusieurs tentatives.")
    if extracted_data:
        df = pd.DataFrame(extracted_data, columns=EXCEL_COLUMNS)
        df["Qualifications professionnelles"] = df["Qualifications professionnelles"].str.replace(";", "\n")
        output_file = os.path.join(folder_path, "export_qualifications.xlsx")
        df.to_excel(output_file, index=False)
        logging.info(f"✅ Extraction terminée ! Fichier généré : {output_file}")


if __name__ == "__main__":
    folder_path = input("Entrez le chemin du dossier contenant les fichiers PDF : ")
    process_pdf_folder(folder_path)
