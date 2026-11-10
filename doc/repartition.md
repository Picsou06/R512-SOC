# Répartition du travail

Découpage de chaque étape du cahier des charges en sous-étapes, avec un responsable et
des dates. État au 3 novembre 2026.

Ces dates ont une semaine d'avance sur le planning du cahier des charges, pour garder de
la marge en cas de retard. Les échéances officielles ne changent pas et sont rappelées
dans les tableaux.

Chaque sous-étape est finie quand son résultat est sur le dépôt. Si une date risque de ne
pas être tenue, on le signale dès que possible, car plusieurs sous-étapes dépendent des
précédentes. Les dates sont de 2026, sauf en janvier (2027).

## M0 : le magasin seul

Terminé : le magasin est chargé depuis le JSON et affiché.

## M1 : des clients qui s'ignorent (jusqu'au 5 novembre)

Le déplacement est codé. Il reste à finir la vérification.

| Fait | N°  | Sous-étape                                                                                      | Responsable | Dates        |
| ---- | --- | ----------------------------------------------------------------------------------------------- | ----------- | ------------ |
| ☒    | 1.1 | Écrire le script qui lance un client depuis des positions de départ quelconques et contrôle son arrivée | Thomas      | 3 au 4 nov.  |
| ☒    | 1.2 | Coder une figure des zones de passage pour repérer les endroits où les trajets se croisent      | Clément     | 4 nov.       |
| ☒    | 1.3 | Analyser et corriger les cas où un client n'arrive pas ou entre dans un obstacle                | Evan        | 4 au 5 nov.  |
| ☒    | 1.4 | Noter les résultats de la vérification pour le rapport                                          | Clément     | 5 nov.       |

## M2 : les contacts et la file d'attente (6 au 15 novembre)

| Fait | N°  | Sous-étape                                                                                                  | Responsable | Dates         |
| ---- | --- | ----------------------------------------------------------------------------------------------------------- | ----------- | ------------- |
| ☒    | 2.1 | Créer les configurations de test : deux clients face à face, passage étroit, caisse avec plusieurs clients  | Clément     | 6 au 7 nov.   |
| ☐    | 2.2 | Fixer le modèle de contact et la définition de la fréquence et de l'intensité (formule et unité)            | Evan        | 6 au 7 nov.   |
| ☐    | 2.3 | Coder la correction des positions entre clients, compatible avec les obstacles et les sens uniques          | Evan        | 7 au 10 nov.  |
| ☐    | 2.4 | Mesurer le chevauchement maximal et les contacts, avec le temps d'attente en caisse                         | Evan        | 10 au 12 nov. |
| ☐    | 2.5 | Coder la file d'attente : un client servi à la fois, places dans l'allée, avancée d'une place à chaque client servi | Thomas      | 10 au 13 nov. |
| ☐    | 2.6 | Coder le choix de la caisse selon la distance et la longueur réelle de la file                              | Clément     | 13 au 14 nov. |
| ☐    | 2.7 | Contrôler que l'ordre de passage respecte l'ordre d'arrivée et consigner les résultats des tests            | Clément     | 14 au 15 nov. |

## M3 : le scénario complet (16 au 22 novembre)

Entrée progressive, stock, caisses et sortie sont déjà codés. Il reste à les relier à M2 et
à fixer la configuration de référence.

| Fait | N°  | Sous-étape                                                                                       | Responsable | Dates         |
| ---- | --- | ------------------------------------------------------------------------------------------------ | ----------- | ------------- |
| ☐    | 3.1 | Faire fonctionner tout le parcours avec les contacts et corriger les blocages dans les allées    | Evan        | 16 au 18 nov. |
| ☐    | 3.2 | Relier les files au parcours complet et corriger les blocages autour des caisses                 | Thomas      | 16 au 18 nov. |
| ☐    | 3.3 | Coder les contrôles automatiques : stock jamais négatif, une caisse par client, un client par caisse, tous sortis | Clément     | 16 au 18 nov. |
| ☐    | 3.4 | Lancer des simulations avec plusieurs valeurs de stock et de rythme d'entrée, et relever les résultats | Clément     | 19 au 20 nov. |
| ☐    | 3.5 | Choisir et figer la configuration de référence à partir de ces résultats                         | Evan        | 21 au 22 nov. |

## M4 : les indicateurs et la comparaison (23 au 29 novembre)

| Fait | N°  | Sous-étape                                                                                | Responsable | Dates         |
| ---- | --- | ----------------------------------------------------------------------------------------- | ----------- | ------------- |
| ☐    | 4.1 | Coder le script qui génère les variantes de configuration : largeur des allées, position de la ressource, nombre de passages | Clément     | 23 au 24 nov. |
| ☐    | 4.2 | Collecter les indicateurs au cours du temps : contacts, densité, débit, clients présents  | Thomas      | 23 au 25 nov. |
| ☐    | 4.3 | Coder les simulations répétées avec plusieurs graines et l'agrégation des résultats       | Evan        | 23 au 25 nov. |
| ☐    | 4.4 | Coder les courbes d'indicateurs, avec axes, unités, légende et paramètres                 | Thomas      | 25 au 27 nov. |
| ☐    | 4.5 | Coder les instantanés du magasin à des instants choisis                                   | Clément     | 25 au 26 nov. |
| ☐    | 4.6 | Lancer toutes les variantes et ranger les résultats et les figures                        | Clément     | 27 au 28 nov. |
| ☐    | 4.7 | Comparer à la référence et rédiger la première réponse à la problématique                 | Evan        | 28 au 29 nov. |

## Validation chiffrée (30 novembre au 6 décembre)

| Fait | N°  | Sous-étape                                                                                 | Responsable | Dates               |
| ---- | --- | -------------------------------------------------------------------------------------------- | ----------- | ------------------- |
| ☐    | V.1 | Remplir le tableau des unités et des ordres de grandeur à partir de la référence           | Clément     | 30 nov. au 1er déc. |
| ☐    | V.2 | Rassembler les courbes de diagramme fondamental de la littérature, avec leurs références   | Clément     | 30 nov. au 2 déc.   |
| ☐    | V.3 | Mesurer les invariants sur une simulation complète et relever les écarts                   | Thomas      | 30 nov. au 1er déc. |
| ☐    | V.4 | Construire le cas de l'allée et tracer le diagramme fondamental face à la littérature      | Thomas      | 2 au 4 déc.         |
| ☐    | V.5 | Refaire la comparaison avec le pas de temps divisé par 2 et par 4, et avec plus de clients, puis conclure | Evan        | 3 au 6 déc.         |
| ☐    | V.6 | Rédiger le bilan de la validation, sans oublier les invariants qui ne s'appliquent pas     | Thomas      | 5 au 6 déc.         |

## M5 : les paramètres supplémentaires (7 au 13 décembre)

Selon le temps restant, dans l'ordre du cahier des charges. Chaque ajout reprend la
comparaison de M4.

| Fait | N°  | Sous-étape                                                                                | Responsable | Dates         |
| ---- | --- | ----------------------------------------------------------------------------------------- | ----------- | ------------- |
| ☐    | 5.1 | Rythme d'entrée : varier l'intervalle jusqu'à l'ouverture d'un coup                       | Thomas      | 7 au 8 déc.   |
| ☐    | 5.2 | Placement des produits : produits regroupés ou dispersés, liste propre à chaque client    | Evan        | 8 au 10 déc.  |
| ☐    | 5.3 | Nombre de caisses : étendre le script de variantes aux caisses ouvertes et relever les résultats | Clément     | 10 au 11 déc. |
| ☐    | 5.4 | Règles d'accès : coder le nombre maximum de clients et étudier le sens de circulation     | Thomas      | 10 au 13 déc. |
| ☐    | 5.5 | Interpréter l'ensemble des évolutions par rapport à la référence                          | Evan        | 12 au 13 déc. |

## Rapport (en continu, puis 14 au 29 décembre)

Échéance officielle : mardi 5 janvier 2027 avant 23h59.

| Fait | N°  | Sous-étape                                                                      | Responsable | Dates          |
| ---- | --- | --------------------------------------------------------------------------------- | ----------- | -------------- |
| ☐    | R.1 | Préparer le modèle LaTeX, le plan et la bibliographie                           | Clément     | 6 au 12 nov.   |
| ☐    | R.2 | Rédiger le résumé, l'introduction et le contexte                                | Clément     | 14 au 16 déc.  |
| ☐    | R.3 | Rédiger la modélisation                                                         | Evan        | 14 au 20 déc.  |
| ☐    | R.4 | Rédiger la discrétisation numérique et l'implémentation                         | Thomas      | 14 au 20 déc.  |
| ☐    | R.5 | Mettre au propre la validation                                                  | Thomas      | 20 au 22 déc.  |
| ☐    | R.6 | Rédiger l'analyse des résultats, le bilan, les limites et les pistes d'amélioration | Evan        | 20 au 24 déc.  |
| ☐    | R.7 | Rédiger la conclusion, insérer les figures et vérifier les légendes             | Clément     | 24 au 26 déc.  |
| ☐    | R.8 | Relire tout le rapport à trois                                                  | Tous        | 26 au 28 déc.  |
| ☐    | R.9 | Finaliser le code et le README pour le rendu                                    | Thomas      | 26 au 28 déc.  |
| ☐    | R.10 | Produire le PDF final et déposer le rapport et le code sur Moodle              | Clément     | 29 déc.        |

## Soutenance (4 au 19 janvier)

Échéance officielle des transparents : lundi 18 janvier 2027 avant 18h00.

| Fait | N°  | Sous-étape                                                             | Responsable | Dates          |
| ---- | --- | ------------------------------------------------------------------------ | ----------- | -------------- |
| ☐    | S.1 | Préparer le modèle des transparents, le contexte et la problématique   | Clément     | 4 au 6 janv.   |
| ☐    | S.2 | Préparer les transparents sur l'implémentation, la validation et les animations | Thomas      | 4 au 8 janv.   |
| ☐    | S.3 | Préparer les transparents sur la modélisation et les résultats         | Evan        | 4 au 8 janv.   |
| ☐    | S.4 | Répéter à trois et ajuster, une première fois puis une seconde         | Tous        | 11 et 15 janv. |
| ☐    | S.5 | Déposer les transparents sur Moodle                                    | Clément     | 16 janv.       |
| ☐    | S.6 | Soutenance orale                                                       | Tous        | 19 janv.       |
