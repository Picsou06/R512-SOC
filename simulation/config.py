import copy
import json
from pathlib import Path

MURS = ("bas", "haut", "gauche", "droite")
TYPES_PORTE = ("entree", "sortie", "entree_sortie")
TYPES_ENTREE = ("entree", "entree_sortie")
TYPES_SORTIE = ("sortie", "entree_sortie")
TYPES_MUR = ("rayon", "mur", "sens_unique")
SENS = {"bas": (0.0, -1.0), "haut": (0.0, 1.0), "gauche": (-1.0, 0.0), "droite": (1.0, 0.0)}
COMPORTEMENT = ("rayon", "vitesse_max", "acceleration", "deceleration", "temps_prise")
PARAMETRES = ("pas_de_temps", "rayon_boules", "distance_caisse", "temps_paiement_fixe",
			  "temps_par_article")


def load_config(chemin):
	with open(chemin, encoding="utf-8") as f:
		config = json.load(f)
	validate_config(config)
	return config


def save_config(config, chemin):
	validate_config(config)
	chemin = Path(chemin)
	chemin.parent.mkdir(parents=True, exist_ok=True)
	with open(chemin, "w", encoding="utf-8") as f:
		json.dump(config, f, indent="\t", ensure_ascii=False)
		f.write("\n")


def duplicate_config(source, destination, overrides=None):
	config = load_config(source)
	if overrides:
		config = _fusionner(config, overrides)
	save_config(config, destination)
	return config


def _fusionner(base, overrides):
	resultat = copy.deepcopy(base)
	for cle, valeur in overrides.items():
		if isinstance(valeur, dict) and isinstance(resultat.get(cle), dict):
			resultat[cle] = _fusionner(resultat[cle], valeur)
		else:
			resultat[cle] = copy.deepcopy(valeur)
	return resultat


def validate_config(config):
	for cle in ("nom", "parametres", "comportement_client", "magasin", "portes", "murs",
				"ressources", "clients"):
		if cle not in config:
			raise ValueError(f"cle manquante : {cle}")

	largeur = config["magasin"]["largeur"]
	hauteur = config["magasin"]["hauteur"]
	if largeur <= 0 or hauteur <= 0:
		raise ValueError("le magasin doit avoir une largeur et une hauteur positives")

	for mur in config["murs"]:
		if mur.get("type") not in TYPES_MUR:
			raise ValueError(f"mur {mur.get('id')} : type inconnu {mur.get('type')!r} "
							 f"(attendu : {', '.join(TYPES_MUR)})")
		if mur["type"] == "sens_unique" and mur.get("sens") not in SENS:
			raise ValueError(f"mur {mur['id']} : sens inconnu {mur.get('sens')!r} "
							 f"(attendu : {', '.join(SENS)})")

	obstacles = obstacles_de(config)
	for nom, zone in obstacles:
		x0, y0, x1, y1 = rectangle(zone)
		if zone["largeur"] <= 0 or zone["hauteur"] <= 0:
			raise ValueError(f"{nom} : largeur et hauteur doivent etre positives")
		if x0 < 0 or y0 < 0 or x1 > largeur or y1 > hauteur:
			raise ValueError(f"{nom} : sort du magasin")
	for i, (nom_a, a) in enumerate(obstacles):
		for nom_b, b in obstacles[i + 1:]:
			if _se_chevauchent(rectangle(a), rectangle(b)):
				raise ValueError(f"{nom_a} et {nom_b} se chevauchent")

	for cle in ("caisses", "murs"):
		ids = [z["id"] for z in config.get(cle, [])]
		if len(ids) != len(set(ids)):
			raise ValueError(f"les identifiants de {cle} doivent etre uniques")

	for zone in sens_uniques(config):
		x0, y0, x1, y1 = rectangle(zone)
		if zone["largeur"] <= 0 or zone["hauteur"] <= 0:
			raise ValueError(f"sens_unique {zone['id']} : largeur et hauteur doivent etre positives")
		if x0 < 0 or y0 < 0 or x1 > largeur or y1 > hauteur:
			raise ValueError(f"sens_unique {zone['id']} : sort du magasin")
		for nom, obstacle in obstacles:
			if _se_chevauchent(rectangle(zone), rectangle(obstacle)):
				raise ValueError(f"sens_unique {zone['id']} : chevauche {nom}")

	if not config["portes"]:
		raise ValueError("le magasin doit avoir au moins une porte")
	for porte in config["portes"]:
		nom = porte.get("nom", "?")
		if porte["type"] not in TYPES_PORTE:
			raise ValueError(f"porte {nom} : type inconnu {porte['type']!r}")
		if porte["mur"] not in MURS:
			raise ValueError(f"porte {nom} : mur inconnu {porte['mur']!r}")
		debut, fin = intervalle_porte(porte)
		longueur_mur = largeur if porte["mur"] in ("bas", "haut") else hauteur
		if porte["largeur"] <= 0 or debut < 0 or fin > longueur_mur:
			raise ValueError(f"porte {nom} : ne tient pas sur le mur {porte['mur']}")
		x, y = porte["x"], porte["y"]
		sur_le_mur = {
			"bas": y == 0,
			"haut": y == hauteur,
			"gauche": x == 0,
			"droite": x == largeur,
		}[porte["mur"]]
		if not sur_le_mur:
			raise ValueError(f"porte {nom} : ({x}, {y}) n'est pas sur le mur {porte['mur']}")

	rayons = {m["id"]: m for m in config["murs"] if m["type"] == "rayon"}

	ids_produits = [r["id"] for r in config["ressources"]]
	if len(ids_produits) != len(set(ids_produits)):
		raise ValueError("les identifiants des ressources doivent etre uniques")
	for ressource in config["ressources"]:
		x, y = ressource["x"], ressource["y"]
		if not (0 <= x <= largeur and 0 <= y <= hauteur):
			raise ValueError(f"ressource {ressource['id']} : hors du magasin")
		if ressource["stock"] < 0:
			raise ValueError(f"ressource {ressource['id']} : stock negatif")
		rayon = rayons.get(ressource.get("rayon"))
		if rayon is None:
			raise ValueError(f"ressource {ressource['id']} : rayon inconnu {ressource.get('rayon')!r}")
		if not sur_le_bord(rayon, x, y):
			raise ValueError(f"ressource {ressource['id']} : ({x}, {y}) n'est pas sur le bord "
							 f"du rayon {rayon['id']}")

	for cle in PARAMETRES:
		if config["parametres"].get(cle, -1) < 0:
			raise ValueError(f"parametres : {cle} manquant ou negatif")
	for cle in ("pas_de_temps", "rayon_boules"):
		if config["parametres"][cle] == 0:
			raise ValueError(f"parametres : {cle} doit etre strictement positif")
	if not isinstance(config.get("affichage", {}).get("boites_collision", False), bool):
		raise ValueError("affichage : boites_collision doit valoir true ou false")
	for cle in COMPORTEMENT:
		if config["comportement_client"].get(cle, -1) < 0:
			raise ValueError(f"comportement_client : {cle} manquant ou negatif")

	portes = {p["nom"]: p for p in config["portes"]}
	ids_clients = [c["id"] for c in config["clients"]]
	if len(ids_clients) != len(set(ids_clients)):
		raise ValueError("les identifiants des clients doivent etre uniques")
	for client in config["clients"]:
		porte = portes.get(client["porte"])
		if porte is None or porte["type"] not in TYPES_ENTREE:
			raise ValueError(f"client {client['id']} : {client['porte']!r} n'est pas une entree")
		_verifier_produits(client["produits"], ids_produits, f"client {client['id']}")
		if client.get("arrivee", 0.0) < 0:
			raise ValueError(f"client {client['id']} : arrivee negative")
	flux = config.get("flux_clients")
	if flux:
		if not isinstance(flux.get("nombre"), int) or flux["nombre"] < 0:
			raise ValueError("flux_clients : nombre doit etre un entier positif")
		if flux.get("intervalle", -1) < 0 or flux.get("debut", 0.0) < 0:
			raise ValueError("flux_clients : intervalle et debut doivent etre positifs")
		for nom in flux.get("portes", []):
			porte = portes.get(nom)
			if porte is None or porte["type"] not in TYPES_ENTREE:
				raise ValueError(f"flux_clients : {nom!r} n'est pas une entree")
		if not any(p["type"] in TYPES_ENTREE for p in config["portes"]):
			raise ValueError("flux_clients : le magasin n'a pas d'entree")
		if "produits" not in flux:
			raise ValueError("flux_clients : produits manquant")
		_verifier_produits(flux["produits"], ids_produits, "flux_clients")
	if (config["clients"] or flux) and not any(p["type"] in TYPES_SORTIE for p in config["portes"]):
		raise ValueError("le magasin doit avoir au moins une sortie")


def _verifier_produits(produits, ids_produits, nom):
	if not isinstance(produits, list):
		raise ValueError(f"{nom} : produits doit etre une liste")
	for produit in produits:
		choix = produit if isinstance(produit, list) else [produit]
		if not choix:
			raise ValueError(f"{nom} : liste de choix vide dans produits")
		for id_produit in choix:
			if not isinstance(id_produit, str):
				raise ValueError(f"{nom} : {id_produit!r} n'est pas un identifiant de produit")
			if id_produit not in ids_produits:
				raise ValueError(f"{nom} : produit inconnu {id_produit!r}")


def sur_le_bord(zone, x, y, tolerance=1e-9):
	x0, y0, x1, y1 = rectangle(zone)
	dedans = x0 - tolerance <= x <= x1 + tolerance and y0 - tolerance <= y <= y1 + tolerance
	sur_un_cote = min(abs(x - x0), abs(x - x1), abs(y - y0), abs(y - y1)) <= tolerance
	return dedans and sur_un_cote


def obstacles_de(config):
	obstacles = [(f"{m['type']} {m['id']}", m) for m in config["murs"] if m["type"] != "sens_unique"]
	obstacles += [(f"caisse {c['id']}", c) for c in config.get("caisses", [])]
	return obstacles


def sens_uniques(config):
	return [m for m in config["murs"] if m["type"] == "sens_unique"]


def _se_chevauchent(a, b, tolerance=1e-9):
	return (a[0] < b[2] - tolerance and b[0] < a[2] - tolerance
			and a[1] < b[3] - tolerance and b[1] < a[3] - tolerance)


def rectangle(zone):
	return zone["x"], zone["y"], zone["x"] + zone["largeur"], zone["y"] + zone["hauteur"]


def intervalle_porte(porte):
	debut = porte["x"] if porte["mur"] in ("bas", "haut") else porte["y"]
	return debut, debut + porte["largeur"]
