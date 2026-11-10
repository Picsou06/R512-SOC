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
