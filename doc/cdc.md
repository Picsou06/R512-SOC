# Cahier des charges

Simulation de foule dans un magasin. Projet de modélisation mathématique,
BUT Informatique, IUT Nice Sophia Antipolis.

## Contexte

On simule des clients qui se déplacent dans un magasin lors d'un pic d'affluence
(par exemple l'ouverture des portes pour un produit en quantité limitée). Les clients
entrent petit à petit, vont chercher le produit, passent en caisse puis sortent. Ce
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

| Paramètre                        | Question associée                                             |
| --------------------------------- | -------------------------------------------------------------- |
| Largeur des allées               | Des allées plus larges réduisent-elles les contacts ?        |
| Position de la ressource limitée | Où placer le produit convoité pour limiter les bousculades ? |
| Nombre de points de passage       | Multiplier les passages fluidifie-t-il la circulation ?        |

Tous les paramètres sont regroupés dans un fichier de configuration : on doit pouvoir
jouer avec facilement, en changer un seul et relancer la simulation pour comparer.

## Évolutions prévues : paramètres supplémentaires

Une fois la problématique traitée, on ajoute d'autres paramètres pour répondre à des
questions plus proches de la gestion réelle d'un magasin. Le but reste le même : que les
clients soient contents, donc le moins écrasés possible.

La configuration de référence contient déjà une entrée progressive (un client toutes
les X secondes) et des caisses avant la sortie. Les évolutions font varier ces
paramètres et en ajoutent d'autres :

| Paramètre              | Ce qu'on fait varier                                             | Question associée                                                                 |
| ---------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Rythme d'entrée        | L'intervalle entre deux entrées, jusqu'à l'ouverture d'un coup (tous les clients à l'instant 0) | Vaut-il mieux ouvrir les portes d'un coup ou faire entrer les clients progressivement, et à quel rythme ? |
| Placement des produits | L'endroit où sont placés les produits dans le magasin, regroupés ou dispersés | Où placer les produits pour répartir les clients au lieu de les concentrer ?      |
| Nombre de caisses      | Le nombre de caisses ouvertes avant la sortie                    | Combien de caisses faut-il pour éviter l'engorgement à la sortie ?                |
| Règles d'accès         | Le nombre maximum de clients dans le magasin, un sens de circulation | Limiter l'accès réduit-il les contacts sans trop allonger l'attente ?             |

Ces évolutions passent après la problématique et sa validation : elles sont traitées
une par une, dans cet ordre, selon le temps restant. Chacune est comparée à la
configuration de référence avec les mêmes indicateurs.

## Indicateurs

- Fréquence des contacts entre clients.
- Intensité des contacts entre clients.

Ces deux indicateurs mesurent la satisfaction des clients : moins il y a de contacts
et moins ils sont intenses, plus les clients sont contents.

Comme les clients entrent petit à petit et passent en caisse, ils peuvent aussi
attendre. On suit donc également le temps d'attente (dehors et en caisse) et le temps
total passé dans le magasin : un client qui n'est pas bousculé mais qui attend très
longtemps n'est pas content non plus.

Leur définition exacte (formule et unité) sera fixée avec le modèle M2.

## Validation

Une simulation qui tourne n'est pas une simulation juste : la consigne impose une
validation appuyée sur des critères objectifs et chiffrés, pas sur une impression
visuelle. Les quatre vérifications ci-dessous sont obligatoires et devront figurer
dans le rapport, avec les écarts mesurés.

| Vérification                     | Ce qu'on mesure dans notre modèle |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Invariants                        | Clients présents + clients sortis = clients au départ. Stock restant + objets pris = stock de départ. Chevauchement maximal entre deux clients (interpénétration). Nombre de clients dans un rayon ou hors du magasin (doit valoir 0). |
| Sensibilité numérique           | Les indicateurs changent-ils quand on divise le pas de temps par 2, par 4 ? Quand on augmente le nombre de clients ? Les conclusions doivent rester les mêmes.                                                                             |
| Comparaison à un résultat connu | Diagramme fondamental d'une foule : débit (ou vitesse moyenne) en fonction de la densité, mesuré dans une allée et comparé aux courbes de la littérature.                                                                             |
| Cohérence des unités            | Toutes les grandeurs ont une unité et un ordre de grandeur réaliste (voir tableau suivant).                                                                                                                                               |

La quantité de mouvement et l'énergie ne sont pas conservées dans notre modèle (chaque
client avance par lui-même) : ces deux invariants ne s'appliquent pas, et le rapport
devra le dire.

Unités et ordres de grandeur :

| Grandeur            | Unité      | Ordre de grandeur attendu                  |
| ------------------- | ----------- | ------------------------------------------ |
| Longueurs           | m           | Allée : 1,5 à 3 m                        |
| Rayon d'un client   | m           | Environ 0,25 m                             |
| Temps, pas de temps | s           | Pas de temps : 0,1 s ou moins              |
| Vitesse             | m/s         | Marche : environ 1,3 m/s                   |
| Densité            | clients/m² | De 0 à 5 ou 6                             |
| Débit              | clients/s   | Environ 1 par mètre de largeur de passage |

## Figures à produire

Le rapport est un PDF : les animations n'y passent pas. Le code doit donc pouvoir
produire des figures fixes :

- des instantanés du magasin à des instants choisis ;
- des courbes d'indicateurs (contacts, densité, débit, nombre de clients présents) en
  fonction du temps ou d'un paramètre.

Chaque figure a des axes nommés avec leurs unités, une légende, et indique les paramètres
de la simulation qui l'a produite. Pas de capture d'écran de la fenêtre de simulation.
Les animations sont fournies avec le code et peuvent être montrées en soutenance.

## Livrables et échéances

Projet réalisé en groupe de 3 étudiants au maximum. Tous les rendus se font par dépôt
sur le Moodle du cours (pas de courriel). Pénalité de 2 points par jour de retard.

| Livrable                    | Échéance                                                   |
| --------------------------- | ------------------------------------------------------------ |
| Rapport final (PDF) et code | Mardi 5 janvier 2027, avant 23h59                            |
| Transparents de soutenance  | Lundi 18 janvier 2027, avant 18h00 (veille de la soutenance) |
| Soutenance orale            | Mardi 19 janvier 2027                                        |

Le rapport fait 15 à 20 pages hors annexes : résumé, introduction, développement
(modélisation, discrétisation numérique, implémentation, validation, analyse des
résultats), conclusion et références. Un point bonus est accordé s'il est rédigé en LaTeX.

## Périmètre fonctionnel

| Phase | Contenu                                                                      |
| ----- | ---------------------------------------------------------------------------- |
| 1     | Chargement du JSON, affichage du magasin                                     |
| 2     | Agents qui se déplacent vers un objectif en évitant les murs               |
| 3     | Gestion des contacts, file d'attente aux caisses et désactivation           |
| 4     | Ressource limitée, prise d'objets, entrée progressive, caisses, sortie      |
| 5     | Collecte des indicateurs et comparaison de configurations                    |
| 6     | Évolutions : rythme d'entrée, placement des produits, nombre de caisses, règles d'accès |

Les phases 1 à 5 répondent à la problématique. La phase 6 correspond aux paramètres
supplémentaires.

## Modélisations prévues (planning sur 3 mois)

Le projet avance par modèles successifs, du plus simple au plus complet. Chaque modèle
reprend le précédent et correspond à une phase du périmètre fonctionnel. On ne passe au
modèle suivant que lorsque le modèle en cours fonctionne et a été vérifié.

Le planning compte 12 semaines, soit 3 mois de 4 semaines, du lundi 12 octobre 2026
au rendu du rapport le mardi 5 janvier 2027. La soutenance a lieu deux semaines après.

### Vue d'ensemble

| Mois | Semaines | Dates                         | Modèle | Ce qu'on fait                                                                                   | Phase |
| ---- | -------- | ----------------------------- | ------- | ----------------------------------------------------------------------------------------------- | ----- |
| 1    | 1        | 12 au 18 octobre              | M0      | Le magasin seul, sans client                                                                    | 1     |
| 1    | 2 - 4    | 19 octobre au 8 novembre      | M1      | Plusieurs clients qui s'ignorent et vont vers un objectif en contournant les murs et les rayons | 2     |
| 2    | 5 - 6    | 9 au 22 novembre              | M2      | Les contacts entre clients et la file d'attente aux caisses                                     | 3     |
| 2    | 7        | 23 au 29 novembre             | M3      | La ressource limitée, l'entrée progressive, les caisses et la sortie                           | 4     |
| 2    | 8        | 30 novembre au 6 décembre    | M4      | Les indicateurs, les figures et la comparaison de configurations                                | 5     |
| 3    | 9        | 7 au 13 décembre             |         | La validation chiffrée du modèle                                                              |       |
| 3    | 10       | 14 au 20 décembre            | M5      | Les évolutions (paramètres supplémentaires), selon le temps restant                          | 6     |
| 3    | 11 - 12  | En continue pendant le projet |         | Rédaction du rapport, rendu du rapport et du code le 5 janvier                                 |       |
|      |          | 6 au 19 janvier               |         | Transparents (rendus le 18 janvier) et soutenance le 19 janvier                                 |       |

### Mois 1 : le magasin et les déplacements

**M0 : le magasin seul (semaine 1)**

- On modélise : un rectangle (les murs), des rayons rectangulaires, une entrée, une
  sortie et la position de la ressource, décrits dans un fichier JSON.
- Simplification : aucun client, rien ne bouge.
- Vérification : le magasin affiché correspond au fichier de configuration.

**M1 : des clients qui s'ignorent (semaines 2 à 4)**

- On modélise : plusieurs clients, représentés par des points, qui avancent à vitesse
  constante vers un objectif. Le temps avance par petits pas : à chaque pas,
  nouvelle position = position + vitesse × pas de temps.
- Les clients ne traversent pas les obstacles : ils suivent le plus court chemin
  jusqu'à leur objectif en contournant les murs et les rayons.
- Simplification : les clients n'ont pas d'épaisseur, ne se voient pas et peuvent se
  superposer.
- Vérification : chaque client atteint son objectif quelle que soit sa position de
  départ, sans jamais entrer dans un rayon. On observe déjà les endroits où les trajets
  se croisent, donc où les contacts auront lieu.

### Mois 2 : les contacts et le scénario complet

**M2 : les contacts entre clients et la file d'attente (semaines 5 et 6)**

- On modélise : chaque client devient un disque. Deux clients sont en contact quand
  leurs disques se touchent ; ils ne peuvent pas se superposer (idée du modèle de
  Bertrand Maury : chacun avance comme il le souhaite, puis on corrige les positions
  pour que personne ne se chevauche).
- On modélise aussi la file d'attente : comme les clients ne peuvent plus se superposer,
  une caisse ne sert qu'un client à la fois. Les suivants attendent leur tour l'un
  derrière l'autre dans l'allée de la caisse, et avancent d'une place à chaque client
  servi. Un client choisit sa caisse selon la distance et la longueur de la file.
- Simplification : tous les clients ont la même taille et la même vitesse ; la
  correction est la plus simple possible (on écarte les deux clients concernés) ;
  une file par caisse, premier arrivé, premier servi, sans changement de file.
- Vérification : deux clients lancés l'un vers l'autre se bloquent sans se traverser ;
  on mesure le chevauchement maximal restant. Une caisse ne sert jamais deux clients
  en même temps, et l'ordre de passage respecte l'ordre d'arrivée dans la file.
- On mesure pour la première fois la fréquence et l'intensité des contacts, ainsi que
  le temps d'attente en caisse.

**M3 : la ressource limitée, les caisses et la sortie (semaine 7)**

- On modélise : les clients entrent petit à petit, un toutes les X secondes. Tous
  veulent le même produit, disponible en quantité limitée. Un client qui atteint la
  ressource prend un objet (cela lui prend quelques secondes), choisit une caisse
  ouverte, attend son tour dans la file (modèle M2) et paie, puis se dirige vers la
  sortie et quitte le magasin (il est désactivé). S'il ne reste plus de produit, il repart sans passer en caisse.
- Simplification : une seule ressource, un rythme d'entrée fixe, des temps de prise et
  de paiement fixes.
- Vérification : le stock ne devient jamais négatif, chaque client passe par une seule
  caisse à la fois, une caisse ne sert qu'un client à la fois, et tous les clients
  finissent par sortir. C'est la **configuration de référence**.

**M4 : les indicateurs et la comparaison (semaine 8)**

- On modélise : rien de nouveau, on exploite le modèle M3.
- On fait varier un seul paramètre à la fois par rapport à la référence : largeur des
  allées, position de la ressource, nombre de points de passage.
- Chaque configuration est simulée plusieurs fois pour ne pas dépendre du hasard, puis
  on compare la fréquence et l'intensité des contacts à celles de la référence.
- Le code produit les figures du rapport : instantanés et courbes avec axes, unités et
  légendes.
- Résultat attendu : **une première réponse à la problématique**.

### Mois 3 : la validation, les évolutions et le rapport

**Validation chiffrée (semaine 9)**

- On ne modélise rien de nouveau : on vérifie que le modèle M3 est juste, avec les
  quatre vérifications de la section « Validation ».
- Invariants : on mesure les écarts sur une simulation complète.
- Sensibilité : on refait la comparaison du modèle M4 avec un pas de temps plus petit
  et avec plus de clients, et on regarde si les conclusions tiennent.
- Résultat connu : on trace le diagramme fondamental dans une allée et on le compare à
  la littérature.
- Cette étape passe avant les évolutions : elle est obligatoire, les évolutions non.

**M5 : les paramètres supplémentaires (semaine 10)**

Ajoutés un par un, dans cet ordre, selon le temps restant :

1. Rythme d'entrée : on fait varier l'intervalle entre deux entrées, jusqu'à
   l'ouverture d'un coup (tous les clients présents à l'instant 0).
2. Placement des produits : plusieurs produits à des endroits différents, chaque client
   a sa propre liste.
3. Nombre de caisses : on fait varier le nombre de caisses ouvertes.
4. Règles d'accès : nombre maximum de clients dans le magasin, sens de circulation.

Pour chaque ajout, on refait la comparaison du modèle M4.

**Rapport (semaines 11 et 12)**

- Bilan : quels aménagements réduisent le plus les contacts, donc rendent les clients
  le plus satisfaits.
- Limites des modèles utilisés et pistes d'amélioration.
- Rédaction du rapport, puis dépôt du rapport et du code le mardi 5 janvier 2027.

**Soutenance (du 6 au 19 janvier)**

- Préparation des transparents, à déposer le lundi 18 janvier avant 18h00.
- Soutenance orale le mardi 19 janvier 2027.
