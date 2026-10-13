# Modele Mesa (espace, agents, boucle de simulation).
#
# Ce fichier contiendra :
#   - l'espace du magasin construit a partir de la config (murs, rayons, allees,
#     entree, sortie, ressource)
#   - l'agent client : deplacement vers un objectif en evitant les murs (phase 2)
#   - la gestion des contacts entre individus et la desactivation (phase 3)
#   - la ressource limitee, la prise d'objets et la sortie (phase 4)
#   - la collecte des indicateurs (phase 5)
#   - la boucle de simulation (un pas de temps = un step du modele)
