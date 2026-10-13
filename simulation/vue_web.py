import math
from html import escape

from simulation.client import ETATS
from simulation.config import SENS, intervalle_porte
from simulation.visualization import (
	CAISSE_FERMEE, CAISSE_OUVERTE, CAISSE_TAPIS, CARRELAGE, COULEURS_ETAT, COULEURS_PORTE,
	LIBELLES_PORTE, MUR, RAYON, RAYON_BORD, RAYON_ETAGERE, RESSOURCE, RESSOURCE_BORD, SENS_UNIQUE,
	SENS_UNIQUE_FLECHE, SOL, TEXTE, VITRE_BORD, _segments_pleins,
)

MARGE = 1.5
MARGE_BAS = 3.0


class Repere:

	def __init__(self, config):
		self.largeur = config["magasin"]["largeur"]
		self.hauteur = config["magasin"]["hauteur"]
		self.vue_largeur = self.largeur + 2 * MARGE
		self.vue_hauteur = self.hauteur + MARGE + MARGE_BAS

	def x(self, x):
		return round(x + MARGE, 3)

	def y(self, y):
		return round(self.hauteur + MARGE - y, 3)

	@property
	def view_box(self):
		return f"0 0 {self.vue_largeur:g} {self.vue_hauteur:g}"


def svg_magasin(config, stocks=None):
	r = Repere(config)
	l, h = r.largeur, r.hauteur
	morceaux = [
		"<defs>"
		'<pattern id="carrelage" width="1" height="1" patternUnits="userSpaceOnUse">'
		f'<path d="M 1 0 L 0 0 0 1" fill="none" stroke="{CARRELAGE}" stroke-width="0.04"/>'
		"</pattern>"
		'<filter id="ombre" x="-20%" y="-20%" width="140%" height="140%">'
		'<feDropShadow dx="0.1" dy="0.1" stdDeviation="0.08" flood-opacity="0.25"/>'
		"</filter>"
		"</defs>",
		f'<rect x="{r.x(0)}" y="{r.y(h)}" width="{l}" height="{h}" fill="{SOL}"/>',
		f'<rect x="{r.x(0)}" y="{r.y(h)}" width="{l}" height="{h}" fill="url(#carrelage)"/>',
	]

	for zone in config["murs"]:
		if zone["type"] == "mur":
			morceaux.append(_rect(r, zone, MUR, None, 0.05))
		elif zone["type"] == "sens_unique":
			morceaux.append(_svg_sens_unique(r, zone))

	for rayon in (m for m in config["murs"] if m["type"] == "rayon"):
		morceaux.append(_rect(r, rayon, RAYON, RAYON_BORD, 0.15))
		vertical = rayon["hauteur"] >= rayon["largeur"]
		longueur = rayon["hauteur"] if vertical else rayon["largeur"]
		n = int(longueur // 0.8)
		for i in range(1, n):
			if vertical:
				yy = rayon["y"] + i * rayon["hauteur"] / n
				morceaux.append(_ligne(r, rayon["x"] + 0.12, yy, rayon["x"] + rayon["largeur"] - 0.12, yy,
									   RAYON_ETAGERE, 0.05))
			else:
				xx = rayon["x"] + i * rayon["largeur"] / n
				morceaux.append(_ligne(r, xx, rayon["y"] + 0.12, xx, rayon["y"] + rayon["hauteur"] - 0.12,
									   RAYON_ETAGERE, 0.05))

	for caisse in config.get("caisses", []):
		couleur = CAISSE_OUVERTE if caisse["ouverte"] else CAISSE_FERMEE
		morceaux.append(_rect(r, caisse, couleur, CAISSE_TAPIS, 0.12))
		tapis = {"x": caisse["x"] + caisse["largeur"] * 0.3, "y": caisse["y"] + 0.25,
				 "largeur": caisse["largeur"] * 0.4, "hauteur": caisse["hauteur"] * 0.55}
		morceaux.append(_rect(r, tapis, CAISSE_TAPIS if caisse["ouverte"] else "#8a9aa8", None, 0,
							  ombre=False))
		morceaux.append(_texte(r, caisse["x"] + caisse["largeur"] / 2, caisse["y"] - 0.45,
							   caisse["id"].split("_")[-1], 0.42, gras=True))

	murs = {
		"bas": ((0, 0), (1, 0), l),
		"haut": ((0, h), (1, 0), l),
		"gauche": ((0, 0), (0, 1), h),
		"droite": ((l, 0), (0, 1), h),
	}
	for mur, ((ox, oy), (dx, dy), longueur) in murs.items():
		ouvertures = [intervalle_porte(p) for p in config["portes"] if p["mur"] == mur]
		for debut, fin in _segments_pleins(longueur, ouvertures):
			morceaux.append(_ligne(r, ox + dx * debut, oy + dy * debut, ox + dx * fin, oy + dy * fin,
								   MUR, 0.35, bout="square"))

	for porte in config["portes"]:
		(ox, oy), (dx, dy), _ = murs[porte["mur"]]
		debut, fin = intervalle_porte(porte)
		a = (ox + dx * debut, oy + dy * debut)
		b = (ox + dx * fin, oy + dy * fin)
		couleur = COULEURS_PORTE[porte["type"]]
		morceaux.append(_ligne(r, *a, *b, couleur, 0.4, opacite=0.9))
		morceaux.append(_ligne(r, *a, *b, "white", 0.07, tirets="0.2 0.2"))
		for bx, by in (a, b):
			morceaux.append(f'<circle cx="{r.x(bx)}" cy="{r.y(by)}" r="0.12" fill="{VITRE_BORD}"/>')
		milieu = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
		decalage = {"bas": (0, -1.0), "haut": (0, 1.0), "gauche": (-1.0, 0), "droite": (1.0, 0)}
		ex, ey = decalage[porte["mur"]]
		morceaux.append(_texte(r, milieu[0] + ex, milieu[1] + ey,
							   porte.get("nom", "").replace("_", " "), 0.42, couleur="currentColor"))

	rayons = {m["id"]: m for m in config["murs"] if m["type"] == "rayon"}
	for ressource in config["ressources"]:
		stock = ressource["stock"] if stocks is None else stocks[ressource["id"]]
		morceaux.append(_svg_ressource(r, ressource, rayons[ressource["rayon"]], stock))

	x0 = l - 5
	y0 = -1.9
	morceaux.append(_ligne(r, x0, y0, l, y0, "currentColor", 0.08))
	for xx in (x0, l):
		morceaux.append(_ligne(r, xx, y0 - 0.2, xx, y0 + 0.2, "currentColor", 0.06))
	morceaux.append(_texte(r, x0 + 2.5, y0 + 0.5, "5 m", 0.42, couleur="currentColor"))

	return "".join(morceaux)


def svg_trajectoires(model, repere):
	morceaux = []
	for client in model.clients:
		if len(client.trajectoire) < 2:
			continue
		points = client.trajectoire[::2] + client.trajectoire[-1:]
		trace = "M " + " L ".join(f"{repere.x(p[1])} {repere.y(p[2])}" for p in points)
		couleur = COULEURS_ETAT.get(client.etat, "#888888")
		morceaux.append(f'<path d="{trace}" fill="none" stroke="{couleur}" stroke-width="0.1" '
						f'stroke-opacity="0.7" stroke-linejoin="round" stroke-dasharray="0.25 0.15"/>')
	return "".join(morceaux)


def svg_boites_collision(obstacles, repere):
	style = ('fill="none" stroke="#ff1744" stroke-width="0.04" stroke-dasharray="0.12 0.08" '
			 'opacity="0.9"')
	return "".join(f'<circle cx="{repere.x(cx)}" cy="{repere.y(cy)}" '
				   f'r="{obstacles.rayon_boules}" {style}/>'
				   for cx, cy in obstacles.boules)


def legende(config):
	elements = [("Rayon", f"background:{RAYON};border:1px solid {RAYON_BORD}")]
	types = {m["type"] for m in config["murs"]}
	if "mur" in types:
		elements.append(("Mur", f"background:{MUR}"))
	if "sens_unique" in types:
		elements.append(("Sens unique", f"background:{SENS_UNIQUE};border:1px solid {SENS_UNIQUE_FLECHE}"))
	caisses = config.get("caisses", [])
	if any(c["ouverte"] for c in caisses):
		elements.append(("Caisse ouverte", f"background:{CAISSE_OUVERTE}"))
	if any(not c["ouverte"] for c in caisses):
		elements.append(("Caisse fermee", f"background:{CAISSE_FERMEE}"))
	for type_porte in COULEURS_PORTE:
		if any(p["type"] == type_porte for p in config["portes"]):
			elements.append((LIBELLES_PORTE[type_porte],
							 f"background:{COULEURS_PORTE[type_porte]};height:5px"))
	elements.append(("Ressource", f"background:{RESSOURCE};border-radius:50%"))
	for etat, couleur in COULEURS_ETAT.items():
		elements.append((f"Client : {ETATS[etat].lower()}", f"background:{couleur};border-radius:50%"))
	return "".join(
		f'<span style="display:inline-flex;align-items:center;margin:0 10px 6px 0;'
		f'font-size:13px"><span style="display:inline-block;width:14px;height:12px;'
		f'margin-right:6px;{style}"></span>{escape(nom)}</span>'
		for nom, style in elements
	)


def _svg_sens_unique(r, zone):
	sx, sy = SENS[zone["sens"]]
	px, py = -sy, sx
	cx, cy = zone["x"] + zone["largeur"] / 2, zone["y"] + zone["hauteur"] / 2
	pointe = (cx + sx * 0.45, cy + sy * 0.45)
	base = (cx - sx * 0.25, cy - sy * 0.25)
	points = [pointe, (base[0] + px * 0.3, base[1] + py * 0.3), (base[0] - px * 0.3, base[1] - py * 0.3)]
	fleche = " ".join(f"{r.x(x)},{r.y(y)}" for x, y in points)
	return (_rect(r, zone, SENS_UNIQUE, None, 0.05, ombre=False).replace("/>", ' opacity="0.55"/>')
			+ f'<polygon points="{fleche}" fill="{SENS_UNIQUE_FLECHE}" opacity="0.9"/>')


def _svg_ressource(r, ressource, rayon, stock):
	x, y = ressource["x"], ressource["y"]
	x0, y0 = rayon["x"], rayon["y"]
	x1, y1 = x0 + rayon["largeur"], y0 + rayon["hauteur"]
	if abs(x - x0) < 1e-9 or abs(x - x1) < 1e-9:
		face = (x, max(y0, y - 0.6), x, min(y1, y + 0.6))
	else:
		face = (max(x0, x - 0.6), y, min(x1, x + 0.6), y)
	texte = f"{ressource['id'].replace('_', ' ')} · stock {stock}"
	tx, ty = (x0 + x1) / 2, y1 + 1.6
	largeur_texte = 0.24 * len(texte) + 0.5
	return (
		_ligne(r, x, y, tx, ty - 0.35, RESSOURCE_BORD, 0.05)
		+ _ligne(r, *face, RESSOURCE, 0.3)
		+ f'<circle cx="{r.x(x)}" cy="{r.y(y)}" r="0.7" fill="{RESSOURCE}" opacity="0.2"/>'
		+ f'<polygon points="{_etoile(r.x(x), r.y(y), 0.42, 0.18)}" fill="{RESSOURCE}" '
		  f'stroke="{RESSOURCE_BORD}" stroke-width="0.05"/>'
		+ f'<rect x="{r.x(tx - largeur_texte / 2)}" y="{r.y(ty + 0.35)}" width="{largeur_texte:.2f}" '
		  f'height="0.7" rx="0.15" fill="white" stroke="{RESSOURCE}" stroke-width="0.05"/>'
		+ _texte(r, tx, ty, texte, 0.4)
	)


def _etoile(cx, cy, grand, petit):
	points = []
	for i in range(10):
		rayon = grand if i % 2 == 0 else petit
		angle = -math.pi / 2 + i * math.pi / 5
		points.append(f"{cx + rayon * math.cos(angle):.3f},{cy + rayon * math.sin(angle):.3f}")
	return " ".join(points)


def _rect(r, zone, remplissage, bord, arrondi, ombre=True):
	contour = f' stroke="{bord}" stroke-width="0.06"' if bord else ""
	filtre = ' filter="url(#ombre)"' if ombre else ""
	return (f'<rect x="{r.x(zone["x"])}" y="{r.y(zone["y"] + zone["hauteur"])}" '
			f'width="{zone["largeur"]}" height="{zone["hauteur"]}" rx="{arrondi}" '
			f'fill="{remplissage}"{contour}{filtre}/>')


def _ligne(r, xa, ya, xb, yb, couleur, epaisseur, bout="round", tirets=None, opacite=1):
	extra = f' stroke-dasharray="{tirets}"' if tirets else ""
	return (f'<line x1="{r.x(xa)}" y1="{r.y(ya)}" x2="{r.x(xb)}" y2="{r.y(yb)}" stroke="{couleur}" '
			f'stroke-width="{epaisseur}" stroke-linecap="{bout}" opacity="{opacite}"{extra}/>')


def _texte(r, x, y, contenu, taille, gras=False, couleur=TEXTE):
	poids = ' font-weight="bold"' if gras else ""
	return (f'<text x="{r.x(x)}" y="{r.y(y)}" font-size="{taille}" fill="{couleur}" '
			f'text-anchor="middle" dominant-baseline="middle" '
			f'font-family="Roboto, Arial, sans-serif"{poids}>{escape(contenu)}</text>')
