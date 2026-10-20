# Simulation de foule dans un magasin

Projet de modelisation mathematique, BUT Informatique, IUT Nice Sophia Antipolis.

Simulation multi-agents (Python + [Mesa](https://mesa.readthedocs.io/)) de clients se
deplacant dans un magasin lors d'un pic d'affluence, avec gestion des contacts entre
individus (modele inspire des travaux de Bertrand Maury sur les mouvements de foule).

Le detail des objectifs, de la problematique et du perimetre fonctionnel se trouve dans
[`doc/cdc.md`](doc/cdc.md) (cahier des charges).

## Structure du projet

```
.
├── doc/
│   ├── cdc.md                   # Cahier des charges
│   └── avis_prof.md             # Notes sur l'avis de l'enseignant
├── configs/
│   └── reference.json           # Configuration de reference
├── simulation/
│   ├── config.py                # Chargement / validation / duplication des configs JSON
│   ├── geometry.py              # Obstacles, plus court chemin, contraintes de non-penetration
│   ├── client.py                # Agent client (deplacement, prise, paiement)
│   ├── model.py                 # Modele Mesa (magasin, clients, boucle de simulation)
│   ├── visualization.py         # Figures du rapport (matplotlib)
│   └── web_view.py              # Dessin SVG du magasin pour le site
├── .vscode/settings.json        # Indentation par tabulations
├── app.py                       # Interface Mesa / Solara dans le navigateur
├── server.py                    # Lance le site et le redemarre quand le code change
├── run.py                       # Export des figures, simulation sans interface
└── requirements.txt
```

## Installation

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Utilisation

Interface de simulation (Mesa, dans le navigateur, avec Play / Pause / Step / Reset) :

```powershell
.venv\Scripts\python server.py
```

Le site est sur http://localhost:8765 (`--port` pour en changer). Il redemarre tout seul
quand on modifie le code (`app.py` ou `simulation/`), et la page se recharge toute seule
quand on enregistre le fichier de configuration.

Simuler les clients jusqu'a leur sortie et exporter les figures du rapport (trajectoire
coloree par la vitesse, et vitesse en fonction du temps) :

```powershell
.venv\Scripts\python run.py --simulate --output outputs/reference.png
```

Afficher la configuration de reference dans une fenetre interactive :

```powershell
.venv\Scripts\python run.py
```

Afficher une autre configuration et exporter l'image au lieu d'ouvrir une fenetre :

```powershell
.venv\Scripts\python run.py configs/my_variant.json --output outputs/my_variant.png
```

### Creer une variante de configuration

```python
from simulation.config import duplicate_config

duplicate_config(
	"configs/reference.json",
	"configs/fast_flow.json",
	overrides={
		"name": "fast_flow",
		"client_flow": {"interval": 1.0},
	},
)
```

Le code, les cles du JSON et les textes affiches sont en anglais ; la documentation reste
en francais.

## Avancement

Le projet avance par modeles successifs, du plus simple au plus complet (planning
detaille dans [`doc/cdc.md`](doc/cdc.md)).

| Mois | Semaines | Modele | Phase | Contenu                                                                                 | Statut  |
| ---- | -------- | ------ | ----- | --------------------------------------------------------------------------------------- | ------- |
| 1    | 1        | M0     | 1     | Le magasin seul, sans client : chargement du JSON, affichage du magasin                 | A venir |
| 1    | 2 - 4    | M1     | 2     | Plusieurs clients qui s'ignorent et vont vers un objectif en contournant murs et rayons | A venir |
| 2    | 5 - 6    | M2     | 3     | Les contacts entre clients et la file d'attente aux caisses                             | A venir |
| 2    | 7        | M3     | 4     | La ressource limitee, l'entree progressive, les caisses et la sortie                    | A venir |
| 2    | 8        | M4     | 5     | Les indicateurs et la comparaison de configurations                                     | A venir |
| 3    | 9        |        |       | La validation chiffree du modele                                                        | A venir |
| 3    | 10       | M5     | 6     | Les evolutions : rythme d'entree, placement des produits, nombre de caisses, regles d'acces | A venir |
| 3    | 11 - 12  |        |       | Redaction du rapport, rendu du rapport et du code le 5 janvier 2027                     | A venir |
|      |          |        |       | Transparents (18 janvier 2027) et soutenance (19 janvier 2027)                          | A venir |
