import math

import numpy as np
from mesa.experimental.continuous_space import ContinuousSpaceAgent

DISTANCE_LIBERATION = 0.05
POINT_ATTEINT = 0.15

ETATS = {
	"vers_produit": "Va au produit",
	"prise": "Prend le produit",
	"vers_caisse": "Va en caisse",
	"paiement": "Paie",
	"vers_sortie": "Sort",
	"sorti": "Sorti",
}


class Client(ContinuousSpaceAgent):

	def __init__(self, model, identifiant, depart, etapes):
		super().__init__(model.space, model)
		self.identifiant = identifiant
		self.position = np.array(depart, dtype=float)
		self.cap = np.array([0.0, 1.0])
		self.vitesse = 0.0
		self.etapes = list(etapes)
		self.etat = None
		self.trajet = []
		self.attente = 0.0
		self.articles = 0
		self.caisse = None
		self.normale = None
		self.cote = None
		self.libere = True
		self.nb_contacts = 0
		self.trajectoire = [(model.temps, *self.position, 0.0)]
		self.journal = [(model.temps, "entree")]
		self._etape_suivante()

	@property
	def en_contact(self):
		return self.normale is not None

	@property
	def libelle(self):
		return ETATS[self.etat]

	def _etape_suivante(self):
		if not self.etapes:
			self.etat = "sorti"
			self.journal.append((self.model.temps, "sorti"))
			return
		etape = self.etapes.pop(0)
		if etape["etat"] == "prise" and not self.model.prendre(etape["produit"]):
			self.journal.append((self.model.temps, "rupture"))
			return self._etape_suivante()
		if etape["etat"] == "prise":
			self.articles += 1
		if etape["etat"] == "vers_caisse":
			if not self.articles:
				self.etapes = [e for e in self.etapes if e["etat"] != "paiement"]
				return self._etape_suivante()
			self.caisse, trajet = self.model.choisir_caisse(self.position)
			etape = {**etape, "trajet": trajet}
		elif etape["etat"] == "paiement":
			etape = {**etape, "duree": self.model.duree_paiement(self.articles)}
		elif etape["etat"] == "vers_sortie":
			etape = {**etape, "trajet": self.model.trajet_sortie(self.position)}
		self.etat = etape["etat"]
		self.journal.append((self.model.temps, self.etat))
		if "trajet" in etape:
			self.trajet = [np.array(point, dtype=float) for point in etape["trajet"]]
		else:
			self.attente = etape["duree"]

	def step(self):
		dt = self.model.pas_de_temps
		if self.etat == "sorti":
			return
		if self.etat in ("prise", "paiement"):
			self.attente -= dt
			if self.attente <= 1e-9:
				if self.etat == "paiement":
					self.model.liberer_caisse(self.caisse)
				self._etape_suivante()
		elif self._avancer(dt):
			self._etape_suivante()
		self.trajectoire.append((self.model.temps + dt, *self.position, self.vitesse))

	def _avancer(self, dt):
		c = self.model.comportement
		obstacles = self.model.obstacles
		cible = self.trajet[0]
		distance = math.dist(self.position, cible)
		if len(self.trajet) > 1 and distance <= POINT_ATTEINT:
			self.trajet.pop(0)
			return False
		if distance <= 0.01:
			self.position = obstacles.respecter_sens(self.position, cible)
			self.vitesse = 0.0
			return True
		restant = distance + sum(math.dist(p, q) for p, q in zip(self.trajet, self.trajet[1:]))

		vitesse_voulue = min(c["vitesse_max"], math.sqrt(2 * c["deceleration"] * restant), restant / dt)
		if vitesse_voulue > self.vitesse:
			self.vitesse = min(vitesse_voulue, self.vitesse + c["acceleration"] * dt)
		else:
			self.vitesse = max(vitesse_voulue, self.vitesse - c["deceleration"] * dt)

		direction = (cible - self.position) / distance
		if self.normale is not None and np.dot(direction, self.normale) < 0:
			tangente = np.array([-self.normale[1], self.normale[0]])
			if self.cote is None:
				self.cote = 1.0 if np.dot(direction, tangente) >= 0 else -1.0
			direction = self.cote * tangente
		longueur_pas = self.vitesse * dt if len(self.trajet) > 1 else min(self.vitesse * dt, distance)
		voulue = obstacles.respecter_sens(self.position, self.position + direction * longueur_pas)
		nouvelle, self.normale = obstacles.repousser(voulue)
		if self.normale is not None and self.libere:
			self.nb_contacts += 1
			self.libere = False
		elif obstacles.distance(nouvelle) > DISTANCE_LIBERATION:
			self.libere = True
			self.cote = None
		deplacement = nouvelle - self.position
		if np.linalg.norm(deplacement) > 1e-9:
			self.cap = deplacement / np.linalg.norm(deplacement)
		self.position = nouvelle
		return False
