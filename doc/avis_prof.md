# Avis de l'enseignant (13 octobre 2026)

Prise de notes de l'échange avec l'enseignant pendant la séance, remise au propre.

## La question de fond

On a le magasin (les allées, les rayons, les produits) et des clients qui peuvent se
déplacer à l'intérieur. La question raisonnable à se poser est : **comment représenter
l'interaction entre le client et les éléments du magasin ?**

On ne peut pas traiter d'un côté les éléments du magasin et de l'autre les clients : il
faut modéliser comment ils se contraignent mutuellement.

## Représentation proposée

- **Le client** est représenté par une boule (un disque de rayon r).
- **Le magasin** est une boîte.
- La contrainte essentielle : **le client reste dans la boîte**.
- **Obstacle rond** (centre P, rayon R) : le client de centre X ne doit pas le
  pénétrer, soit `dist(X, P) ≥ r + R`. *(Une partie de l'explication n'a pas été
  entendue.)*
- **Obstacles réels** :
  - un obstacle peut être vu comme un segment ;
  - un obstacle réel quelconque peut être vu comme une union de boules ;
  - autre piste évoquée : le plan séparateur (un plan qui sépare le client de
    l'obstacle).
- **Question à traiter** : comment prendre en compte ces contraintes numériquement ?

## Le client

- Il a un objectif, une entrée, une sortie et un point de départ.
- Il a une vitesse, il change de direction et il doit pouvoir s'arrêter.
- On peut lui imaginer d'autres trajectoires que la plus directe.
- Les clients peuvent aussi bloquer le passage (avec les bras, par exemple).

## Démarche conseillée (du plus simple au plus complet)

1. Un client **sans obstacle**, avec seulement ses limitations physiques (vitesse,
   accélération, freinage).
2. Un client et **un obstacle fixe circulaire**.
3. **Plusieurs obstacles** : une fois qu'on sait gérer un obstacle, en gérer un ou
   plusieurs revient au même.
4. **Plusieurs clients**.

Tout au long du projet : **réfléchir à la stratégie du client**.

## Questions sur la stratégie du client

- Peut-on prouver que « accélérer à fond, freiner à fond » est une bonne stratégie ?
  On ne saura peut-être pas le prouver nous-mêmes, mais on peut s'aider d'une IA.
- Le client frôle-t-il l'obstacle (ou la ligne d'obstacles), ou prend-il un virage
  arrondi quand il change de direction ?
- **Les clients ne sont pas des pilotes de F1** : leur déplacement doit rester humain.

## Ce qui a été noté au tableau

Le tableau décrit une progression de modélisation, en cinq parties lues de gauche à
droite. Au-dessus des parties 3 à 5 : **« Stratégie du client ? »**, la question de fond
(comment le client choisit sa trajectoire).

1. **Le magasin complet** : un magasin avec deux rayons rectangulaires et un obstacle de
   forme irrégulière. Un client contourne un obstacle rond en pointillés. Note :
   *interaction client ↔ éléments du magasin*.
2. **Client sans obstacle** : « Contraintes » est barré et remplacé par **« Limitations
   physiques du client »**.
   - *Magasin brut* : un carré vide de côté n, avec plusieurs trajectoires possibles qui
     partent du bord gauche, font une boucle et ressortent.
   - Le bonhomme est remplacé par un **cercle** : le client est un disque (ou un point).
   - Une trajectoire pas à pas, en points successifs, vers une cible X.
3. **Un client et des obstacles circulaires** : un obstacle de centre P, le client en x.
   - Condition de non-collision : **dist(x, P) ≥ r + R** (r : rayon du client, R : rayon
     de l'obstacle).
   - Question : *comment la prendre en compte mathématiquement ?*
4. **Plusieurs clients avec obstacles** : **« Obstacle réel = union de boules »**. Un
   rayon est dessiné rempli de petits cercles : une forme quelconque est approchée par
   des disques, ce qui permet de réutiliser la condition de la partie 3.
5. **Obstacles = segments** : un rayon plein peut être modélisé seulement par ses bords
   (un rectangle hachuré équivaut à un rectangle vide). Il faut alors calculer la
   distance point-segment, ou l'intersection, entre le client et chaque bord.

En résumé : client seul avec ses limitations physiques, puis contrainte de distance avec
un obstacle rond, puis deux façons de représenter les vrais obstacles (**union de
boules** ou **segments**). La stratégie de déplacement reste la question ouverte.

## Ce qui est implémenté

- **Union de boules** (seul modèle d'obstacles, réglé par `ball_radius` dans `parameters`) : chaque rayon et
  chaque caisse est rempli d'une grille de disques de rayon `ball_radius` (25 cm par
  défaut), comme le rayon rempli de petits cercles au tableau. Les cases de la grille
  mesurent au plus R√2 de côté, donc l'union des disques recouvre tout le rectangle et
  ne déborde que d'environ 12 cm. Contrainte appliquée à chaque pas :
  `dist(x, P) ≥ r + R` pour toutes les boules P. Si le pas voulu la viole, la position
  est projetée sur le bord de la boule la plus pénétrée, plusieurs fois de suite (une
  boule peut repousser le client dans sa voisine).
- **Contournement en mode `rush` (foncer)** : quand le client touche un obstacle et que sa
  cible est derrière, il longe l'obstacle, toujours dans le même sens jusqu'à s'en
  dégager (algorithme « bug »). S'il choisissait le côté à chaque pas, il resterait
  bloqué quand la cible est pile derrière le rayon.
- **Boîtes de collision** (`"display": {"collision_boxes": true}`, ou la case à cocher
  sur le site) : dessine en pointillés rouges la forme de collision de chaque obstacle,
  c'est-à-dire ses boules. La forme de collision du client est son
  disque. Il y a contact quand le disque du client touche un pointillé.

## Ouverture

Les mêmes idées s'appliquent à une course de voitures : les problèmes sont similaires
et les stratégies complémentaires.
