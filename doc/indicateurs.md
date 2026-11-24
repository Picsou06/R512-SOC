# Indicateurs au cours du temps (M4)

Sous-étapes 4.2 (collecte) et 4.4 (courbes).

## Collecte (sous-étape 4.2)

À la fin de chaque pas de temps, `StoreModel._record` ajoute une ligne à `model.series`
(un tableau par indicateur, la liste est `SERIES` dans `simulation/model.py`) :

| Colonne             | Définition                                                                                  | Unité     |
| ------------------- | ------------------------------------------------------------------------------------------- | --------- |
| `time`              | Instant de fin du pas                                                                      | s         |
| `present`           | Clients dans le magasin                                                                    | clients   |
| `queuing`           | Clients dans une file de caisse (en attente ou en train de payer)                          | clients   |
| `exited`            | Clients sortis depuis le début (le débit en est la dérivée)                                | clients   |
| `contact_pairs`     | Paires écartées par la correction de position pendant le pas                               | paires    |
| `new_contacts`      | Clients qui passent de « écarté » à « en contact » pendant le pas (fréquence, voir [`contact_model.md`](contact_model.md)) | contacts  |
| `overlapping_pairs` | Paires qui se chevauchent avant correction                                                 | paires    |
| `total_intensity`   | Somme des chevauchements avant correction de ces paires (intensité)                        | m         |
| `max_intensity`     | Plus grand de ces chevauchements                                                           | m         |
| `density`           | Densité moyenne : clients présents / surface libre (magasin moins murs, rayons et caisses) | clients/m² |
| `local_density`     | Plus forte densité autour d'un client : clients à moins de 1 m de son centre (lui compris) / π × 1² | clients/m² |

Les grandeurs dérivées se calculent à partir de ces colonnes, sur une fenêtre glissante
(`simulation/indicators.py`) :

- fréquence des contacts = somme de `new_contacts` sur la fenêtre / durée de la fenêtre (contacts/s) ;
- intensité moyenne = somme de `total_intensity` / somme de `overlapping_pairs` sur la
  fenêtre, donc une moyenne sur les contacts et non sur les pas de temps, dont la plupart
  n'en ont aucun (m) ;
- débit à la sortie = augmentation de `exited` sur la fenêtre / durée (clients/min).

La densité moyenne seule ne suffit pas : sur la référence elle ne dépasse pas
0,08 client/m², alors que la densité locale atteint 1,9 client/m² (6 clients dans un disque
de 1 m de rayon), devant `TOILET_PAPER` et dans les files de caisse. C'est la densité locale
qui sert pour comparer les configurations et pour le diagramme fondamental (V.4).

Export pour l'agrégation (4.3, 4.6) : `model.save_series(chemin)` écrit un CSV avec une
ligne par pas de temps, ou en ligne de commande :

```powershell
.venv\Scripts\python run.py configs/reference.json --simulate --series results/reference.csv
```

## Courbes (sous-étape 4.4)

- `indicator_figure(model)` : les indicateurs en fonction du temps, en 5 panneaux (clients
  présents, densité, fréquence des contacts, intensité, débit). `run.py --simulate` la
  sauvegarde avec le suffixe `_indicators`.
- `parameter_figure(...)` : un indicateur en fonction d'un paramètre, sur plusieurs graines
  (moyenne ± écart-type, chaque simulation en point, la valeur de la référence en
  pointillé), pour la comparaison des variantes (4.6).

Chaque figure a des axes nommés avec leurs unités, une légende, et le bas de la figure
rappelle les paramètres de la simulation (configuration, flux de clients, caisses, stock,
pas de temps, rayon, vitesse, temps de prélèvement et de paiement).

## Valeurs sur la référence (graine 1)

| Indicateur                        | Valeur                                            |
| --------------------------------- | ------------------------------------------------- |
| Clients présents                  | pic de 54 vers 130 s, puis environ 28             |
| Densité moyenne / locale maximale | 0,08 / 1,9 client/m²                              |
| Fréquence des contacts            | 4 à 9 nouveaux contacts/s                         |
| Intensité moyenne des contacts    | 9 à 15 cm avant correction                        |
| Débit à la sortie                 | jusqu'à 66 clients/min, 40 clients/min en régime établi |

À vérifier : le chevauchement maximal avant correction atteint 25 à 26 cm (la moitié du
diamètre) presque en continu. Ce n'est pas le chevauchement restant (0,001 m après
correction), mais il est plus grand que ce qu'un client peut parcourir en un pas
(0,13 m). Il vient probablement de clients qui entrent sur une place déjà occupée près de
la porte d'entrée, ou de la poussée des clients voisins pendant la correction.
