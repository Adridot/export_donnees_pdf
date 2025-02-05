from PyInstaller.__main__ import run

run([
    "src/export_pdf.py",
    "--onefile",          # Un seul exécutable
    "--name", "export_pdf"  # Nom du fichier généré
])