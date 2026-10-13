# Point d'entree : affiche le magasin a partir d'une config.
#
# Ce fichier contiendra :
#   - la lecture des arguments : chemin de la config (par defaut
#     configs/reference.json) et option --sortie pour exporter une image
#   - le chargement de la config (simulation/config.py)
#   - la creation du modele (simulation/model.py)
#   - l'affichage du magasin (simulation/visualization.py)
#
# Utilisation :
#   .venv\Scripts\python run.py
#   .venv\Scripts\python run.py configs/ma_variante.json --sortie outputs/ma_variante.png
