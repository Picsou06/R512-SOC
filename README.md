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

Le projet avance par modeles successifs, du plus simple au plus complet (planning
detaille dans [`cdc.md`](cdc.md)).

| Mois | Semaines | Modele | Phase | Contenu                                                                                 | Statut  |
| ---- | -------- | ------ | ----- | --------------------------------------------------------------------------------------- | ------- |
| 1    | 1        | M0     | 1     | Le magasin seul, sans client : chargement du JSON, affichage du magasin                 | A venir |
| 1    | 2 - 4    | M1     | 2     | Plusieurs clients qui s'ignorent et vont vers un objectif en contournant murs et rayons | A venir |
| 2    | 5 - 6    | M2     | 3     | Les contacts entre clients                                                              | A venir |
| 2    | 7        | M3     | 4     | La ressource limitee et la sortie                                                       | A venir |
| 2    | 8        | M4     | 5     | Les indicateurs et la comparaison de configurations                                     | A venir |
| 3    | 9        |        |       | La validation chiffree du modele                                                        | A venir |
| 3    | 10       | M5     | 6     | Les evolutions : file d'attente, entree progressive, caisses, regles d'acces            | A venir |
| 3    | 11 - 12  |        |       | Redaction du rapport, rendu du rapport et du code le 5 janvier 2027                     | A venir |
|      |          |        |       | Transparents (18 janvier 2027) et soutenance (19 janvier 2027)                          | A venir |
