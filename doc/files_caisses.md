# Choix de la caisse et contrôle des files (M2)

Sous-étapes 2.6 et 2.7. Mesures faites le 17 novembre 2026 sur le commit `2d05ebb` (file d'attente de Thomas,
sous-étape 2.5) plus les modifications décrites ici.

## Choix de la caisse (sous-étape 2.6)

Rappel du cahier des charges : *un client choisit sa caisse selon la distance et la
longueur de la file. Une file par caisse, premier arrivé, premier servi, sans changement
de file.*

### Avant

Le choix existait déjà, mais la file était comptée de façon approximative : un compteur
`load` par caisse, augmenté au choix et diminué à la fin du paiement, multiplié par une
pénalité fixe (le temps de paiement d'**un** article, converti en mètres). Un client qui
avait 5 articles comptait donc autant qu'un client qui en avait 1, et un client presque
fini de payer comptait autant qu'un client qui venait d'arriver.

### Maintenant

Chaque caisse ouverte a deux listes dans le modèle :

- `heading[caisse]` : les clients qui ont choisi cette caisse et qui sont en chemin ;
- `queues[caisse]` : la file de la 2.5, les clients arrivés au bout de la file, **dans
  l'ordre d'arrivée**. Le premier de la liste est celui qui paie ou le prochain servi.

Quand un client a fini ses courses, il calcule pour chaque caisse ouverte un coût en
secondes :

```
coût = (distance jusqu'à la caisse + distance de la caisse à la sortie) / vitesse max
       + somme des temps de paiement restants des clients déjà dans la file ou en chemin
```

- Les distances viennent des cartes des distances (`DistanceField`), donc elles tiennent
  compte des murs, des rayons et des allées à sens unique.
- Le temps de paiement restant d'un client est `wait` s'il est en train de payer (ce
  qu'il lui reste réellement), sinon (en chemin ou en attente dans la file) `payment_base_time + payment_time_per_item × articles`
  (son vrai nombre d'articles).
- Les clients en chemin sont comptés : sinon, plusieurs clients qui finissent leurs courses
  en même temps choisiraient tous la même caisse vide.

Le client prend la caisse de coût minimal et n'en change plus (pas de changement de file).
Tout est en secondes : on compare directement un temps de marche et un temps d'attente,
sans pénalité arbitraire à régler.

Le modèle garde un journal `checkout_log` de tous les événements de caisse, sous la forme
`(temps, caisse, client, événement)` avec quatre événements : `chosen` (choix de la caisse),
`joined` (arrivée au bout de la file, `join_queue`), `served` (début du paiement, quand le
client est le premier de la file et atteint la caisse) et `left` (fin du paiement,
`release_checkout`).

### Vérification sur `two_checkouts.json`

Nouvelle configuration de test (voir [`configs_test.md`](configs_test.md)) : la même que
`checkout_queue.json` avec deux caisses côte à côte et 8 clients, un par seconde. La caisse 2
est un peu plus près de la sortie, donc plus avantageuse quand les files sont vides.

| Temps  | Client     | Caisse 1 (marche + attente) | Caisse 2 (marche + attente) | Choix |
| ------ | ---------- | --------------------------- | --------------------------- | ----- |
| 9,5 s  | client_1   | 10,7 + 0,0 = 10,7 s         | 9,2 + 0,0 = **9,2 s**       | 2     |
| 10,9 s | client_2   | 11,0 + 0,0 = **11,0 s**     | 10,1 + 7,0 = 17,1 s         | 1     |
| 12,0 s | client_3   | 10,7 + 7,0 = 17,7 s         | 9,1 + 7,0 = **16,1 s**      | 2     |
| 13,0 s | client_4   | 11,0 + 7,0 = **18,0 s**     | 10,1 + 14,0 = 24,1 s        | 1     |
| 14,0 s | client_5   | 10,7 + 14,0 = 24,7 s        | 9,2 + 13,7 = **22,9 s**     | 2     |
| 15,0 s | client_6   | 10,8 + 14,0 = **24,8 s**    | 9,8 + 19,7 = 29,5 s         | 1     |
| 16,2 s | client_7   | 10,7 + 20,5 = 31,2 s        | 9,3 + 18,5 = **27,8 s**     | 2     |
| 17,2 s | client_8   | 10,5 + 19,5 = **30,0 s**    | 9,4 + 24,5 = 33,9 s         | 1     |

Les clients se répartissent 4 / 4. À 14,0 s, l'attente à la caisse 2 vaut 13,7 s et non
14,0 s : `client_1` est en train de payer et il ne lui reste que 6,7 s, c'est la
« longueur réelle » de la file. Avec la distance seule (attente forcée à 0), les 8 clients
vont tous à la caisse 2.

Sur la référence (graine 1), les 32 clients qui passent en caisse se répartissent 3, 6, 6,
8 et 9 sur les caisses 1, 3, 4, 5 et 6. Avec le stock limité, peu de clients passent en
caisse et ils arrivent étalés, donc les files restent courtes au moment du choix.

## Contrôle des files (sous-étape 2.7)

Rappel du cahier des charges : *une caisse ne sert jamais deux clients en même temps, et
l'ordre de passage respecte l'ordre d'arrivée dans la file.*

Commande :

```powershell
.venv\Scripts\python check_queues.py configs/tests/checkout_queue.json --verbose
.venv\Scripts\python check_queues.py configs/reference.json configs/tests/two_checkouts.json --seeds 5
```

Le script simule chaque configuration (avec plusieurs graines si on le demande) et relit
`checkout_log`. Il contrôle :

1. **Ordre de passage** : pour chaque caisse, la liste des `served` est la même que la
   liste des `joined` (premier arrivé, premier servi).
2. **Un client à la fois** : un `served` n'arrive jamais avant le `left` du client précédent
   de la même caisse.
3. **Une seule file par client** : chaque client a exactement un `chosen`, un `joined`, un
   `served` et un `left`, tous sur la même caisse.
4. **Tous les clients sortent.**

Le script renvoie le code 1 s'il trouve une erreur, pour pouvoir l'utiliser dans un
contrôle automatique (sous-étape 3.3).

On a d'abord vérifié que le script détecte bien les erreurs, sur des journaux écrits à la
main : un journal correct ne donne aucune erreur, deux clients servis dans l'ordre inverse
de leur arrivée donnent l'erreur d'ordre, et deux clients servis en même temps donnent
l'erreur « served while … is still paying ».

### Résultats

5 graines par configuration, avec la file de la 2.5 :

| Configuration          | Clients sortis | Ordre de passage | Un client à la fois | Une file par client | Attente dans la file (moyenne / max) |
| ---------------------- | -------------- | ---------------- | ------------------- | ------------------- | ------------------------------------ |
| `checkout_queue.json`  | 6 / 6          | respecté         | oui                 | oui                 | 17,8 à 19,2 s / 35,1 à 38,3 s        |
| `two_checkouts.json`   | 8 / 8          | respecté         | oui                 | oui                 | 9,8 à 10,0 s / 20,4 à 20,6 s         |
| `narrow_passage.json`  | 20 / 20        | respecté         | oui                 | oui                 | 62,6 à 63,1 s / 126,2 à 127,0 s      |
| `head_on.json`         | 2 / 2          | respecté         | oui                 | oui                 | 3,2 à 3,3 s / 6,4 à 6,5 s            |
| `reference.json`       | 300 / 300      | respecté         | oui                 | oui                 | 5,4 à 8,6 s / 19,4 à 23,4 s          |

**25 simulations sur 25 sans erreur.** Le contrôle de la vérification de M2 est rempli :
une caisse ne sert jamais deux clients en même temps et l'ordre de passage respecte
l'ordre d'arrivée dans la file.

Sur `checkout_queue.json`, le dernier client attend environ 37 s avant de payer : il y a 5
paiements de 7 s devant lui (35 s), plus le temps d'avancer d'une place à chaque client
servi. C'est cohérent avec l'ordre de grandeur annoncé dans
[`configs_test.md`](configs_test.md).

Avant de brancher la file de la 2.5, le même script trouvait des erreurs sur toutes les
configurations (par exemple, sur `checkout_queue.json`, `client_2` commençait à payer à
16,3 s alors que `client_1` n'avait pas fini) : il détecte donc bien l'absence de file.

On note aussi que l'ordre d'arrivée dans la file n'est pas forcément l'ordre d'entrée dans
le magasin : sur `checkout_queue.json`, l'ordre de passage est `client_1` à `client_4`, puis
`client_6` et `client_5`, car `client_6` arrive au bout de la file avant `client_5` (les
contacts près du rayon le font passer devant). Le cahier des charges parle de l'ordre
d'arrivée **dans la file**, c'est donc ce que contrôle le script, et non l'ordre
`client_1` à `client_6` annoncé dans [`configs_test.md`](configs_test.md).
