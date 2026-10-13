import math

import numpy as np


def boules_du_rectangle(zone, rayon_boules):
	x0, y0 = zone["x"], zone["y"]
	pas = rayon_boules * math.sqrt(2)
	nx = max(1, math.ceil(zone["largeur"] / pas))
	ny = max(1, math.ceil(zone["hauteur"] / pas))
	lx, ly = zone["largeur"] / nx, zone["hauteur"] / ny
	centres = [(x0 + (i + 0.5) * lx, y0 + (j + 0.5) * ly) for i in range(nx) for j in range(ny)]
	return centres, rayon_boules - min(lx, ly) / 2


class Obstacles:

	def __init__(self, zones, largeur, hauteur, rayon_client, rayon_boules, sens_uniques=()):
		remplissages = [boules_du_rectangle(z, rayon_boules) for z in zones]
		self.boules = np.array([c for centres, _ in remplissages for c in centres]).reshape(-1, 2)
		self.rayon_boules = rayon_boules
		self.epaisseur = max((depassement for _, depassement in remplissages), default=0.0)
		self.distance_min = rayon_client + rayon_boules
		self.rayon_client = rayon_client
		self.largeur, self.hauteur = largeur, hauteur
		self.sens_uniques = list(sens_uniques)

	def repousser(self, position, iterations=10, tolerance=0.01):
		p = np.array(position, dtype=float)
		if len(self.boules):
			for _ in range(iterations):
				ecarts = p - self.boules
				distances = np.hypot(ecarts[:, 0], ecarts[:, 1])
				j = int(np.argmin(distances))
				if distances[j] >= self.distance_min:
					break
				p = self.boules[j] + ecarts[j] / max(distances[j], 1e-12) * self.distance_min
		r = self.rayon_client
		p = np.clip(p, [r, r], [self.largeur - r, self.hauteur - r])
		return p, self._normale(p, tolerance)

	def _normale(self, p, tolerance):
		r = self.rayon_client
		normale = np.zeros(2)
		for ecart, direction in ((p[0] - r, (1, 0)), (self.largeur - r - p[0], (-1, 0)),
								 (p[1] - r, (0, 1)), (self.hauteur - r - p[1], (0, -1))):
			if ecart < tolerance:
				normale += direction
		if len(self.boules):
			ecarts = p - self.boules
			distances = np.hypot(ecarts[:, 0], ecarts[:, 1])
			proches = distances < self.distance_min + tolerance
			normale += (ecarts[proches] / distances[proches, None]).sum(axis=0)
		norme = np.linalg.norm(normale)
		return normale / norme if norme > 1e-12 else None

	def distance(self, point):
		x, y = point
		r = self.rayon_client
		distances = [x - r, self.largeur - r - x, y - r, self.hauteur - r - y]
		if len(self.boules):
			ecarts = self.boules - np.asarray(point, dtype=float)
			distances.append(float(np.hypot(ecarts[:, 0], ecarts[:, 1]).min()) - self.distance_min)
		return min(distances)

	def respecter_sens(self, ancienne, nouvelle):
		deplacement = nouvelle - ancienne
		for (x0, y0, x1, y1), (sx, sy) in self.sens_uniques:
			if x0 < nouvelle[0] < x1 and y0 < nouvelle[1] < y1:
				contresens = deplacement[0] * sx + deplacement[1] * sy
				if contresens < 0:
					deplacement = deplacement - contresens * np.array([sx, sy])
		return ancienne + deplacement
