# Export PDF Data

## 📌 Description
Ce projet permet d'extraire des données de fichiers PDF et de générer un fichier exploitable. Il est conçu pour être facilement exécutable sous Windows et macOS.

## 🚀 Installation
### Prérequis
- Python 3.10+
- pip
- [PyInstaller](https://pyinstaller.org/) (installé automatiquement avec les dépendances)

### Installation des dépendances
Exécutez la commande suivante pour installer les dépendances nécessaires :
```sh
pip install -r requirements.txt
```

## 🛠️ Utilisation
### Exécution du script
Lancez simplement le script principal :
```sh
python src/export_pdf.py
```

### Génération d'un exécutable
Pour générer un fichier exécutable standalone, utilisez :
```sh
python setup.py
```
L'exécutable sera créé dans le dossier `dist/`.

## 🔄 Automatisation CI/CD
Le projet inclut un workflow GitHub Actions pour générer automatiquement des exécutables pour Windows et macOS lors des commits sur la branche principale.

Fichier de pipeline : `.github/workflows/build.yml`

## 📂 Structure du projet
```
export_donnees_pdf/
│── src/
│   ├── export_pdf.py      # Script principal d'extraction
│── setup.py               # Script pour la génération de l'exécutable
│── requirements.txt       # Liste des dépendances
│── .github/
│   ├── workflows/
│       ├── build.yml      # Pipeline GitHub Actions
│── .gitignore             # Fichiers à ignorer par Git
│── README.md              # Documentation du projet
```