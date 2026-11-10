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
