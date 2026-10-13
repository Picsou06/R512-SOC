# Cahier des charges

Simulation de foule dans un magasin — projet de modélisation mathématique,
BUT Informatique, IUT Nice Sophia Antipolis.

## Contexte

On simule des clients qui se déplacent dans un magasin lors d'un pic d'affluence
(par exemple l'ouverture des portes pour un produit en quantité limitée). Les clients
sont des agents (Python + Mesa) qui peuvent entrer en contact les uns avec les autres ;
le modèle de contact s'inspire des travaux de Bertrand Maury sur les mouvements de foule.

## Problématique

> Comment la largeur des allées, la position de la ressource limitée et le nombre de
> points de passage modifient-ils la fréquence et l'intensité des contacts entre clients
> lors d'un pic d'affluence, par rapport à une configuration de référence ?

Problématique validée par l'enseignant.

## Objectif

Trouver les aménagements du magasin pour lesquels les clients sont le plus satisfaits,
c'est-à-dire le moins écrasés possible : on cherche à réduire la fréquence et l'intensité
des contacts entre clients.

Chaque aménagement testé est comparé à une configuration de référence.

## Paramètres étudiés

Paramètres de la problématique :

| Paramètre                        | Question associée                                              |
| -------------------------------- | -------------------------------------------------------------- |
| Largeur des allées               | Des allées plus larges réduisent-elles les contacts ?          |
| Position de la ressource limitée | Où placer le produit convoité pour limiter les bousculades ?   |
| Nombre de points de passage      | Multiplier les passages fluidifie-t-il la circulation ?        |

Paramètres supplémentaires, à ajouter dans un second temps :

| Paramètre              | Question associée                                                                 |
| ---------------------- | --------------------------------------------------------------------------------- |
| Mode d'ouverture       | Que se passe-t-il si on ouvre le magasin d'un coup, ou si on fait entrer les clients petit à petit ? |
| Placement des produits | Comment la disposition des produits dans le magasin change-t-elle les contacts ?  |
| Nombre de caisses      | Combien de caisses faut-il pour éviter l'engorgement à la sortie ?                |

Tous ces paramètres doivent pouvoir être modifiés facilement pour jouer avec et
comparer les résultats.

## Indicateurs

- Fréquence des contacts entre clients.
- Intensité des contacts entre clients.

Ces deux indicateurs mesurent la satisfaction des clients : moins il y a de contacts
et moins ils sont intenses, plus les clients sont contents.

## Périmètre fonctionnel

| Phase | Contenu                                                                  |
| ----- | ------------------------------------------------------------------------ |
| 1     | Chargement du JSON, affichage du magasin                                 |
| 2     | Agents qui se déplacent vers un objectif en évitant les murs             |
| 3     | Gestion des contacts et désactivation                                    |
| 4     | Ressource limitée, prise d'objets, sortie                                |
| 5     | Collecte des indicateurs et comparaison de configurations                |
| 6     | Évolutions : file d'attente, entrée progressive, caisses, règles d'accès |

Les phases 1 à 5 répondent à la problématique. La phase 6 correspond aux paramètres
supplémentaires.
