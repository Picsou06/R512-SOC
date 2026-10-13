# Chargement / sauvegarde / duplication des configs JSON.
#
# Ce fichier contiendra :
#   - le chargement d'une configuration depuis un fichier JSON (ex. configs/reference.json)
#   - la validation des parametres (dimensions du magasin, allees, clients, ...)
#   - la sauvegarde d'une configuration dans un fichier JSON
#   - duplicate_config(source, destination, overrides) : copie d'une configuration
#     en modifiant certains parametres, pour creer des variantes a comparer
