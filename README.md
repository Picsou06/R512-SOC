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
│   ├── avis_prof.md             # Notes sur l'avis de l'enseignant
│   ├── repartition.md           # Repartition du travail
│   ├── verification_m1.md       # Resultats de la verification de M1 (pour le rapport)
│   ├── configs_test.md          # Description des configurations de test de M2
│   ├── contact_model.md         # Modele de contact et correction des positions (M2)
│   ├── files_caisses.md         # Choix de la caisse et controle des files (M2)
│   ├── resultats_m3.md          # Resultats des simulations selon le stock et le rythme d'entree (M3)
│   └── figures/                 # Figures citees dans la documentation
├── configs/
│   ├── reference.json           # Configuration de reference
│   └── tests/                   # Cas de test de M2 (face a face, passage etroit, file en caisse, deux caisses)
├── simulation/
│   ├── config.py                # Chargement / validation / duplication des configs JSON
│   ├── geometry.py              # Obstacles, carte des distances, contraintes de non-penetration
│   ├── client.py                # Agent client (deplacement, prise, paiement)
│   ├── model.py                 # Modele Mesa (magasin, clients, boucle de simulation)
│   ├── visualization.py         # Figures du rapport (matplotlib)
│   └── web_view.py              # Dessin SVG du magasin pour le site
├── .vscode/settings.json        # Indentation par tabulations
├── app.py                       # Interface Mesa / Solara dans le navigateur
├── server.py                    # Lance le site et le redemarre quand le code change
├── run.py                       # Export des figures, simulation sans interface
├── check_paths.py               # Verification des trajets depuis des positions quelconques
├── passage_zones.py             # Figures des zones de passage et de croisement des trajets
├── check_queues.py              # Verification des files aux caisses (ordre de passage, un client a la fois)
├── check_invariants.py          # Controles automatiques du scenario complet (stock, caisses, sortie)
├── aggregate.py                 # Simulations repetees (plusieurs graines) et agregation des indicateurs
├── sweep.py                     # Simulations pour plusieurs valeurs de stock et de rythme d'entree
└── requirements.txt
```

## Installation

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Utilisation

Interface de simulation (Mesa, dans le navigateur, avec Play / Pause / Step / Restart) :

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

Verifier qu'un client atteint chaque objectif depuis des positions quelconques, sans entrer
dans un obstacle (code de sortie 1 en cas d'echec) :

```powershell
.venv\Scripts\python check_paths.py configs/reference.json
```

Reperer les endroits ou les trajets se croisent (modele M1, clients qui s'ignorent) :
passages par case, croisements et superpositions entre clients, avec les zones les plus
fortes affichees dans le terminal :

```powershell
.venv\Scripts\python passage_zones.py configs/reference.json --output outputs/passage_zones.png
```

Verifier les files aux caisses : un seul client servi a la fois par caisse, ordre de
passage = ordre d'arrivee dans la file, une seule file par client (code de sortie 1 en cas
d'echec, `--seeds` pour repeter avec plusieurs graines) :

```powershell
.venv\Scripts\python check_queues.py configs/tests/checkout_queue.json --verbose
```

Controler les invariants du scenario complet a chaque pas de temps : stock jamais negatif
(et stock restant + articles pris = stock de depart), une seule caisse par client, un seul
client servi par caisse, aucun client perdu, et tous les clients sortis a la fin (code de
sortie 1 en cas d'echec) :

```powershell
.venv\Scripts\python check_invariants.py configs/reference.json configs/tests/*.json --seeds 3
```

Lancer le scenario complet pour plusieurs valeurs de stock (facteur applique au stock de
chaque produit) et de rythme d'entree (intervalle entre deux clients), avec les invariants
controles a chaque pas, et relever les resultats dans `outputs/sweep.csv` (une ligne par
simulation) et `outputs/sweep_mean.csv` (moyenne sur les graines) :

```powershell
.venv\Scripts\python sweep.py --stock-factors 0.5 1 2 4 --intervals 0.5 1 1.5 3 --seeds 2
```

Les configurations de test de M2 sont dans `configs/tests/` (voir
[`doc/configs_test.md`](doc/configs_test.md)).

Simuler une configuration avec plusieurs graines et agreger les indicateurs (temps passe
dans le magasin, contacts entre clients, chevauchement maximal, attente en caisse), avec
moyenne et ecart-type sur les graines :

```powershell
.venv\Scripts\python aggregate.py configs/reference.json --seeds 5
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

| Mois | Semaines | Modele | Phase | Contenu                                                                                     | Statut  |
| ---- | -------- | ------ | ----- | ------------------------------------------------------------------------------------------- | ------- |
| 1    | 1        | M0     | 1     | Le magasin seul, sans client : chargement du JSON, affichage du magasin                     | Fait    |
| 1    | 2 - 4    | M1     | 2     | Plusieurs clients qui s'ignorent et vont vers un objectif en contournant murs et rayons     | Fait    |
| 2    | 5 - 6    | M2     | 3     | Les contacts entre clients et la file d'attente aux caisses                                 | A venir |
| 2    | 7        | M3     | 4     | La ressource limitee, l'entree progressive, les caisses et la sortie                        | A venir |
| 2    | 8        | M4     | 5     | Les indicateurs et la comparaison de configurations                                         | A venir |
| 3    | 9        |        |       | La validation chiffree du modele                                                            | A venir |
| 3    | 10       | M5     | 6     | Les evolutions : rythme d'entree, placement des produits, nombre de caisses, regles d'acces | A venir |
| 3    | 11 - 12  |        |       | Redaction du rapport, rendu du rapport et du code le 5 janvier 2027                         | A venir |
|      |          |        |       | Transparents (18 janvier 2027) et soutenance (19 janvier 2027)                              | A venir |
