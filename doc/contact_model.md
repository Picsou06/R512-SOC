# Modèle de contact et correction des positions (M2)

## Modèle de contact (sous-étape 2.2)

Deux clients sont en contact quand la distance entre leurs centres est inférieure au
diamètre d'un client (2 × rayon, soit 0,5 m avec le rayon de référence de 0,25 m). C'est
la même condition qui servait déjà à repérer les superpositions dans la figure des zones
de passage de M1 (`passage_zones.py`) : ces superpositions deviennent, avec la correction
de position ci-dessous, de vrais contacts qui ne s'interpénètrent plus.

- **Intensité d'un contact** : le chevauchement qu'il faudrait corriger, en mètres :
  max(0, diamètre − distance). La correction de position le ramène à chaque pas de temps
  près de 0 ; son maximum sur une simulation est l'indicateur de vérification de 2.3 (« le
  chevauchement maximal restant » du cahier des charges).
- **Fréquence des contacts** : nombre de fois où deux clients passent de « écartés » à
  « en contact », compté par client. Unité : nombre de contacts (ou contacts/s rapporté à
  la durée de la simulation).

Ces deux grandeurs sont les indicateurs de satisfaction visés par la problématique (voir
`cdc.md`, section Indicateurs) ; cette page fixe leur formule et leur unité comme prévu
par le planning.

## Correction des positions (sous-étape 2.3)

Idée de Bertrand Maury, dans sa version la plus simple (cahier des charges, M2) : chaque
client avance comme il le souhaite, puis on écarte les paires de clients trop proches.
Pour chaque paire dont la distance est inférieure au diamètre, chacun des deux clients
est repoussé de la moitié du chevauchement, le long de la droite qui relie leurs centres,
puis sa position est reprojetée hors des murs et des rayons (`Obstacles.push_out`) pour
rester compatible avec les obstacles. Les allées à sens unique n'ont pas besoin d'un
traitement particulier : ce ne sont pas des obstacles physiques, seulement une contrainte
de direction pour le déplacement volontaire, donc l'écartement s'y applique normalement.

### Problème rencontré : blocage symétrique

Avec seulement cet écartement, `configs/tests/head_on.json` (deux clients lancés l'un
vers l'autre dans un couloir) ne se résout jamais : les deux chemins les plus courts
passent exactement sur la même ligne (le centre du couloir), donc le vecteur qui relie
leurs centres est purement longitudinal. L'écartement les repousse alors tout droit en
arrière, sans aucune composante latérale : rien ne les fait dévier pour se contourner,
alors que le couloir fait 3 m de large. Les deux clients restent figés à exactement un
diamètre l'un de l'autre.

Solutions algorithmiques envisagées :

| Solution | Principe | Choisie |
| --- | --- | --- |
| Biais latéral fixe dans l'écartement | Tourner le vecteur de poussée d'un petit angle constant, toujours dans le même sens | Non : règle arbitraire (pourquoi la droite plutôt que la gauche) |
| Décalage de la position de départ | Petit décalage latéral aléatoire à l'entrée de chaque client | Non : ne règle que la symétrie de départ, un réalignement plus loin dans le magasin reproduirait le blocage |
| Priorité par ordre d'arrivée | Le premier arrivé garde sa trajectoire, l'autre dévie | Non : demande de suivre qui est arrivé en premier, plus de code pour le même résultat |
| **Bruit aléatoire sur le cap voulu** | À chaque pas, perturber légèrement (±3°) la direction que le client cherche à suivre, avant de limiter le virage à l'accélération latérale | **Oui** |

Le bruit aléatoire est tiré avec le générateur du modèle (`model.random`, graine fixe),
donc la simulation reste reproductible. Il s'ajoute à chaque pas, pour tous les clients,
pas seulement en cas de blocage : au repoussement (`Obstacles.push_out`) qui limite déjà
toute pénétration dans un mur ou un rayon, ce bruit ne change donc rien à la vérification
de M1 (revérifiée sur `check_paths.py` après coup, résultat identique : 0 bloqué,
0 pénétration, 0 contresens sur les 37 431 trajets).

### Vérification

| Configuration | Résultat |
| --- | --- |
| `head_on.json` | Les deux clients se contournent et sortent (42,7 s et 40,2 s) |
| `narrow_passage.json` | 20 clients sur 20 sortent |
| `checkout_queue.json` | 6 clients sur 6 sortent |
| `reference.json` (300 clients) | 300 sur 300 sortent en 489,9 s simulées |
| `check_paths.py` sur `reference.json` | Résultats inchangés par rapport à M1 : 0 bloqué, 0 pénétration, 0 contresens |

## Mesure des indicateurs (sous-étape 2.4)

> Les chiffres de cette section datent d'avant la correction par passes répétées décrite
> plus bas (tâche 3.1), sur une version de la configuration de référence sans vraie file
> d'attente ni stock limité. Les chiffres à jour sont dans la table de la section suivante.

Les trois grandeurs définies ci-dessus sont maintenant mesurées pendant la simulation et
affichées en fin d'exécution par `run.py --simulate` : le chevauchement maximal restant
(`model.max_overlap`, mis à jour dans `_separate_clients`), la fréquence des contacts par
client (`client.client_contact_count`, incrémenté à chaque transition « écarté » →
« en contact »), et le temps d'attente en caisse (différence entre les horodatages
`to_checkout` et `paying` du journal de chaque client, déjà enregistré).

| Configuration | Contacts par client | Chevauchement maximal restant | Attente en caisse |
| --- | --- | --- | --- |
| `checkout_queue.json` (6 clients, 1 caisse) | moyenne 2,8, max 4 | 0,125 m | moyenne 5,1 s, max 5,6 s |
| `reference.json` (300 clients) | moyenne 9,0, max 20 | 0,122 m | moyenne 9,9 s, max 14,7 s |

Le chevauchement maximal restant (environ 12 cm, soit un quart du diamètre) n'est pas nul.
Sur `checkout_queue.json`, il apparaît quand un client double deux clients arrêtés
(« picking ») près d'un rayon : la correction doit à la fois l'écarter de l'autre client
et le repousser hors du rayon (`push_out`), et une seule passe par pas de temps ne suffit
pas toujours à satisfaire les deux dans une allée étroite. Le résidu reste alors entre 0,05
et 0,12 m pendant environ 0,6 s, le temps qu'il se faufile, puis disparaît. C'est une limite
connue de la correction la plus simple (une seule passe, cahier des charges M2), pas un
blocage ni une interpénétration qui grandit.

Le temps d'attente en caisse mesuré ici inclut encore le trajet vers la caisse : sur
`checkout_queue.json`, il n'y a qu'une seule caisse ouverte, donc plusieurs clients peuvent
se retrouver à payer en même temps dessus (rien ne l'interdit pour l'instant). La vraie
file d'attente, où une caisse ne sert qu'un client à la fois, est la tâche 2.5 : cette
mesure servira alors à vérifier que le temps d'attente correspond bien à l'ordre d'arrivée.

## Projection sur la configuration admissible (tâche 3.1)

### Problème rencontré : écrasement en foule dense

Sur le parcours complet (configuration de référence, M3), tous les clients vont d'abord
chercher le même produit (`TOILET_PAPER`), au même endroit du magasin. Beaucoup de clients
s'y retrouvent donc en contact mutuel en même temps, parfois une dizaine à la fois dans la
même allée.

La correction de la sous-étape 2.3 ne traite chaque paire en contact qu'une seule fois par
pas de temps, dans l'ordre où `numpy` renvoie les paires. Quand plus de deux clients sont en
contact en même temps, corriger une paire peut recréer ou aggraver le chevauchement d'une
paire déjà corrigée au même pas (un client repoussé vers un deuxième, qui n'a pas encore été
traité). Avec un pas de temps de 0,1 s et des clients proches de leur vitesse maximale, chacun
avance d'environ 0,13 m par pas, largement de quoi recréer un chevauchement qu'une seule passe
vient de corriger. Le résultat observé : un amas de clients qui s'interpénètrent nettement
plus que les quelques centimètres de résidu attendus en 2.4, le temps que la foule se
résorbe.

### Solution : approcher la configuration admissible par passes répétées

Idée de Bertrand Maury : après que chaque client a avancé comme il le souhaite, la position
retenue n'est pas la position voulue mais la configuration la plus proche qui respecte
toutes les contraintes d'exclusion à la fois (aucun client dans un autre, aucun client dans
un obstacle), pas seulement les contraintes prises une par une. Calculer exactement cette
configuration est un problème d'optimisation sous contraintes (une projection sur
l'ensemble des configurations admissibles), que le cahier des charges ne demande pas de
détailler ici.

La version implémentée l'approche sans le résoudre exactement : on répète la correction de
2.3 (écarter chaque paire encore trop proche, puis reprojeter hors des obstacles) jusqu'à ce
qu'il n'y ait plus aucune paire en chevauchement, au lieu de s'arrêter après une seule passe
(`StoreModel._separate_clients`, jusqu'à `MAX_SEPARATION_SWEEPS` passes, limite jamais
atteinte dans nos configurations de test). Chaque passe recalcule les distances à partir des
positions déjà corrigées par la passe précédente, donc un client repoussé contre un deuxième
voit cette nouvelle gêne traitée avant la fin du pas de temps. C'est une configuration
admissible proche de la projection exacte, pas la projection elle-même.

### Vérification

| Configuration | Résultat |
| --- | --- |
| `head_on.json` | Les deux clients se contournent et sortent |
| `narrow_passage.json` | 20 clients sur 20 sortent, chevauchement maximal 0,001 m |
| `checkout_queue.json` | 6 clients sur 6 sortent, chevauchement maximal 0,001 m |
| `two_checkouts.json` | 8 clients sur 8 sortent, chevauchement maximal 0,001 m |
| `reference.json` (300 clients) | 300 sur 300 sortent, chevauchement maximal 0,005 m |

Sur `reference.json`, le chevauchement maximal restant passe de 0,247 m (une seule passe)
à 0,005 m (passes répétées), et le temps maximal passé dans le magasin par un client de
382,9 s à 58,7 s : les clients bloqués dans l'amas en sortent beaucoup plus vite. Sur les
3581 pas de temps où au moins une passe a eu lieu, la limite de `MAX_SEPARATION_SWEEPS`
(20 passes) n'est atteinte que 2 fois, sans que le chevauchement y dépasse 0,005 m.

### Mesure des indicateurs, configuration de référence actuelle

| Configuration | Contacts par client | Chevauchement maximal restant | Attente en caisse |
| --- | --- | --- | --- |
| `checkout_queue.json` (6 clients, 1 caisse) | moyenne 2,3, max 3 | 0,001 m | moyenne 22,1 s, max 39,3 s |
| `reference.json` (300 clients) | moyenne 7,1, max 22 | 0,005 m | moyenne 13,4 s, max 21,6 s |

Ces chiffres ne se comparent pas directement à ceux de la section précédente : la
configuration de référence a maintenant la vraie file d'attente (2.5 à 2.7) et le stock
limité (M3), qui changent aussi la fréquence des contacts et le temps d'attente, pas
seulement la correction de position.

### Limite restante

La vitesse enregistrée dans la trajectoire de chaque client (`client.speed`) reste la
vitesse voulue avant projection, pas la vitesse effective après correction de position.
Dans le modèle de Maury, c'est la vitesse projetée qui devrait servir de vitesse réelle du
client. Ça n'a pas d'effet sur les indicateurs de contact mesurés ici, mais ça comptera pour
le diagramme fondamental (vitesse en fonction de la densité, tâche V.4) : à traiter à ce
moment-là.
