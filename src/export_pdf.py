import os
import time
import fitz  # PyMuPDF
import google.generativeai as genai
import pandas as pd
import json
from google.api_core.exceptions import InternalServerError, ResourceExhausted

# 🔑 Demande de la clé API Gemini
API_KEY = input("🔑 Saisir la clé API Gemini : ").strip()
genai.configure(api_key=API_KEY)

print("✅ Clé API ajoutée avec succès !")

# 📌 Définition des colonnes pour le fichier Excel
EXCEL_COLUMNS = [
    "Raison sociale", "Sigle", "Responsabilité légale", "Adresse", "Téléphone", "Portable", "E-mail",
    "Site Internet", "SIRET", "Code NACE", "Assurance Travaux",
    "Assurance Civile", "Effectif moyen", "Chiffre d’affaires H.T.", "Qualifications professionnelles"
]

# 📑 Sélection du modèle Gemini
gemini_model = genai.GenerativeModel("gemini-2.0-flash-lite")


def extract_pdf_text(file_path):
    """Extrait le texte d'un fichier PDF."""
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction du texte ({file_path}) : {e}")
    return text


def generate_prompt(content):
    """Génère le prompt à partir du contenu du PDF."""
    return f"""
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
        {content}
        """


def handle_api_errors(func):
    """Décorateur pour gérer les erreurs API avec des tentatives de nouvelle exécution."""

    def wrapper(*args, **kwargs):
        max_retries = 5
        attempt = 0
        while attempt < max_retries:
            try:
                return func(*args, **kwargs)
            except json.JSONDecodeError as e:
                print(f"⚠️ Erreur de parsing JSON : {e}")
                break  # Ne pas réessayer en cas d'erreur de parsing
            except InternalServerError as e:
                attempt += 1
                print(f"🔄 Erreur 500 détectée (tentative {attempt}/{max_retries}). Nouvelle tentative...")
                if attempt >= max_retries:
                    print("❌ Erreur persistante après plusieurs tentatives.")
                    break
            except ResourceExhausted as e:
                print("⚠️ Quota d'API dépassé. Attente de 60 secondes avant de réessayer...")
                time.sleep(60)  # Pause de 60 secondes avant de réessayer
            except Exception as e:
                print(f"⚠️ Erreur avec Gemini : {e}")
                break  # Ne pas réessayer pour d'autres types d'erreurs
        return None

    return wrapper


@handle_api_errors
def analyze_content_with_gemini(content):
    """Envoie le texte extrait à l'API Gemini et récupère les informations formatées."""
    prompt = generate_prompt(content)
    response = gemini_model.generate_content(prompt)
    result = response.text
    if "```json" in result:
        result = result.split("```json")[1].split("```")[0].strip()
    return json.loads(result)


def process_pdf_folder(folder_path):
    """Parcourt un dossier, extrait et analyse les PDF puis génère un fichier Excel."""
    extracted_data = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".pdf"):
            full_path = os.path.join(folder_path, file_name)
            print(f"📄 Traitement du fichier : {file_name}")
            pdf_text = extract_pdf_text(full_path)
            if pdf_text:
                extracted_info = analyze_content_with_gemini(pdf_text)
                if extracted_info:
                    extracted_data.append(extracted_info)
                else:
                    print(f"⚠️ Aucune réponse obtenue pour {file_name}")
            else:
                print(f"⚠️ Aucun texte extrait pour {file_name}")

    # 📊 Génération du fichier Excel
    if extracted_data:
        df = pd.DataFrame(extracted_data, columns=EXCEL_COLUMNS)
        df["Qualifications professionnelles"] = df["Qualifications professionnelles"].str.replace(";", "\n")
        output_file = os.path.join(folder_path, "export_qualifications.xlsx")
        df.to_excel(output_file, index=False)
        print(f"✅ Extraction terminée ! Fichier généré : {output_file}")


if __name__ == "__main__":
    folder_path = input("Entrez le chemin du dossier contenant les fichiers PDF : ")
    process_pdf_folder(folder_path)
    
