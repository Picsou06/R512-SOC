import math

import mesa
from mesa.experimental.continuous_space import ContinuousSpace

from simulation.client import Client
from simulation.config import (SENS, TYPES_ENTREE, TYPES_SORTIE, load_config, obstacles_de,
							   rectangle, sens_uniques)
from simulation.geometrie import Obstacles

DECALAGE = 0.05
JEU_PRODUIT = 0.4
GRAINE = 1


class MagasinModel(mesa.Model):
	def __init__(self, chemin_config="configs/reference.json", rng=GRAINE):
		super().__init__(rng=rng)
		self.config = load_config(chemin_config)
		self.comportement = self.config["comportement_client"]
		self.parametres = self.config["parametres"]
		self.pas_de_temps = self.parametres["pas_de_temps"]
		self.temps = 0.0

		largeur = self.config["magasin"]["largeur"]
		hauteur = self.config["magasin"]["hauteur"]
		self.space = ContinuousSpace([[0, largeur], [0, hauteur]], torus=False, random=self.random)

		zones = [zone for _, zone in obstacles_de(self.config)]
		sens = [(rectangle(z), SENS[z["sens"]]) for z in sens_uniques(self.config)]
		self.obstacles = Obstacles(zones, largeur, hauteur, self.comportement["rayon"],
								   self.parametres["rayon_boules"], sens)

		self.stocks = {r["id"]: r["stock"] for r in self.config["ressources"]}
		self.charge = {c["id"]: 0 for c in self.config.get("caisses", []) if c["ouverte"]}
		self.clients = []
		self.en_attente = self._arrivees()
		self.nb_clients_total = len(self.en_attente)
		self._faire_entrer()

	def _arrivees(self):
		arrivees = [(d.get("arrivee", 0.0), d) for d in self.config["clients"]]
		flux = self.config.get("flux_clients")
		if flux:
			entrees = flux.get("portes") or [p["nom"] for p in self.config["portes"]
											 if p["type"] in TYPES_ENTREE]
			pris = {d["id"] for d in self.config["clients"]}
			numero = 0
			for k in range(flux["nombre"]):
				numero += 1
				while f"client_{numero}" in pris:
					numero += 1
				description = {"id": f"client_{numero}", "porte": entrees[k % len(entrees)],
							   "produits": list(flux["produits"])}
				arrivees.append((flux.get("debut", 0.0) + k * flux["intervalle"], description))
		arrivees.sort(key=lambda a: a[0])
		return arrivees

	def _faire_entrer(self):
		while self.en_attente and self.en_attente[0][0] <= self.temps + 1e-9:
			_, description = self.en_attente.pop(0)
			self.clients.append(self._creer_client(description))

	def _creer_client(self, description):
		portes = {p["nom"]: p for p in self.config["portes"]}
		ressources = {r["id"]: r for r in self.config["ressources"]}
		rayons = {m["id"]: m for m in self.config["murs"] if m["type"] == "rayon"}

		depart = self._point_porte(portes[description["porte"]], aleatoire=True)
		etapes = []
		for id_produit in self._tirer_produits(description["produits"]):
			ressource = ressources[id_produit]
			point = self._point_produit(ressource, rayons[ressource["rayon"]])
			etapes.append({"etat": "vers_produit", "trajet": [point]})
			etapes.append({"etat": "prise", "duree": self.comportement["temps_prise"],
						   "produit": id_produit})
		etapes.append({"etat": "vers_caisse"})
		etapes.append({"etat": "paiement"})
		etapes.append({"etat": "vers_sortie"})
		return Client(self, description["id"], depart, etapes)

	def _tirer_produits(self, produits):
		return [self.random.choice(p) if isinstance(p, list) else p for p in produits]

	def prendre(self, id_produit):
		if self.stocks[id_produit] <= 0:
			return False
		self.stocks[id_produit] -= 1
		return True

	def duree_paiement(self, articles):
		return self.parametres["temps_paiement_fixe"] + self.parametres["temps_par_article"] * articles

	def _point_porte(self, porte, aleatoire=False):
		d = self.comportement["rayon"] + DECALAGE
		largeur = self.config["magasin"]["largeur"]
		hauteur = self.config["magasin"]["hauteur"]
		milieu = porte["largeur"] / 2
		if aleatoire:
			jeu = max(0.0, milieu - self.comportement["rayon"] - 0.1)
			milieu += self.random.uniform(-jeu, jeu)
		return {
			"bas": (porte["x"] + milieu, d),
			"haut": (porte["x"] + milieu, hauteur - d),
			"gauche": (d, porte["y"] + milieu),
			"droite": (largeur - d, porte["y"] + milieu),
		}[porte["mur"]]

	def _point_produit(self, ressource, rayon):
		x, y = ressource["x"], ressource["y"]
		d = self.comportement["rayon"] + self.obstacles.epaisseur + DECALAGE
		jeu = JEU_PRODUIT
		if abs(x - rayon["x"]) < 1e-9 or abs(x - (rayon["x"] + rayon["largeur"])) < 1e-9:
			y = min(max(y + self.random.uniform(-jeu, jeu), rayon["y"]), rayon["y"] + rayon["hauteur"])
			return (x - d, y) if abs(x - rayon["x"]) < 1e-9 else (x + d, y)
		x = min(max(x + self.random.uniform(-jeu, jeu), rayon["x"]), rayon["x"] + rayon["largeur"])
		return (x, y - d) if abs(y - rayon["y"]) < 1e-9 else (x, y + d)

	def _point_caisse(self, caisse):
		return (caisse["x"] - self.parametres["distance_caisse"],
				caisse["y"] + caisse["hauteur"] / 2)

	def _sorties(self):
		return [p for p in self.config["portes"] if p["type"] in TYPES_SORTIE]

	def choisir_caisse(self, depart):
		penalite = self.duree_paiement(1) * self.comportement["vitesse_max"]
		meilleur = None
		for caisse in self.config.get("caisses", []):
			if not caisse["ouverte"]:
				continue
			point = self._point_caisse(caisse)
			aller = math.dist(depart, point)
			for porte in self._sorties():
				retour = math.dist(point, self._point_porte(porte))
				cout = aller + retour + penalite * self.charge[caisse["id"]]
				if meilleur is None or cout < meilleur[0]:
					meilleur = (cout, caisse["id"], point)
		if meilleur is None:
			raise ValueError("aucune caisse ouverte")
		_, id_caisse, point = meilleur
		self.charge[id_caisse] += 1
		allee = self._allee_en(point)
		return id_caisse, (self._trajet_allee(allee)[:1] if allee else []) + [point]

	def liberer_caisse(self, id_caisse):
		self.charge[id_caisse] -= 1

	def trajet_sortie(self, depart):
		porte = min(self._sorties(), key=lambda p: math.dist(depart, self._point_porte(p)))
		point_porte = self._point_porte(porte, aleatoire=True)
		allees = sens_uniques(self.config)
		if not allees or self._allee_en(depart):
			return [point_porte]
		allee = min(allees, key=lambda z: math.dist(depart, self._trajet_allee(z)[0])
					+ math.dist(self._trajet_allee(z)[1], point_porte))
		return self._trajet_allee(allee) + [point_porte]

	def _allee_en(self, point):
		for zone in sens_uniques(self.config):
			x0, y0, x1, y1 = rectangle(zone)
			if x0 <= point[0] <= x1 and y0 <= point[1] <= y1:
				return zone
		return None

	def _trajet_allee(self, zone):
		sx, sy = SENS[zone["sens"]]
		centre = (zone["x"] + zone["largeur"] / 2, zone["y"] + zone["hauteur"] / 2)
		portee = abs(sx) * zone["largeur"] / 2 + abs(sy) * zone["hauteur"] / 2 + self.comportement["rayon"] + DECALAGE
		return [(centre[0] - sx * portee, centre[1] - sy * portee), centre]

	@property
	def clients_presents(self):
		return [c for c in self.clients if c.etat != "sorti"]

	@property
	def clients_sortis(self):
		return [c for c in self.clients if c.etat == "sorti"]

	def step(self):
		for client in self.clients_presents:
			client.step()
		self.temps = round(self.temps + self.pas_de_temps, 10)
		self._faire_entrer()
		if not self.en_attente and not self.clients_presents:
			self.running = False

	def simuler(self, duree_max=3600.0):
		while self.running and self.temps < duree_max:
			self.step()
		return self
