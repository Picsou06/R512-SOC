# Simulation de foule dans un magasin

Projet de modelisation mathematique, BUT Informatique, IUT Nice Sophia Antipolis.

Simulation multi-agents (Python + [Mesa](https://mesa.readthedocs.io/)) de clients se
deplacant dans un magasin lors d'un pic d'affluence, avec gestion des contacts entre
individus (modele inspire des travaux de Bertrand Maury sur les mouvements de foule).

Le detail des objectifs, de la problematique et du perimetre fonctionnel se trouve dans
[`cdc.md`](cdc.md) (cahier des charges).

## Structure du projet

```
.
├── cdc.md                      # Cahier des charges
├── configs/
│   └── reference.json          # Configuration de reference
├── simulation/
│   ├── config.py                # Chargement / sauvegarde / duplication des configs JSON
│   ├── model.py                  # Modele Mesa (espace, agents, boucle de simulation)
│   └── visualization.py          # Affichage du magasin et des indicateurs
├── run.py                       # Point d'entree : affiche le magasin a partir d'une config
└── requirements.txt
```

## Installation

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Utilisation

Afficher la configuration de reference dans une fenetre interactive :

```powershell
.venv\Scripts\python run.py
```

Afficher une autre configuration et exporter l'image au lieu d'ouvrir une fenetre :

```powershell
.venv\Scripts\python run.py configs/ma_variante.json --sortie outputs/ma_variante.png
```

### Creer une variante de configuration

```python
from simulation.config import duplicate_config

duplicate_config(
    "configs/reference.json",
    "configs/allees_larges.json",
    overrides={"nom": "allees_larges", "allees": {"largeur": 3.5}},
)
```

## Avancement

| Phase | Contenu | Statut |
|---|---|---|
| 1 | Chargement du JSON, affichage du magasin | Fait |
| 2 | Agents qui se deplacent vers un objectif en evitant les murs | A venir |
| 3 | Gestion des contacts et desactivation | A venir |
| 4 | Ressource limitee, prise d'objets, sortie | A venir |
| 5 | Collecte des indicateurs et comparaison de configurations | A venir |
| 6 | Evolutions : file d'attente, entree progressive, caisses, regles d'acces | A venir |
