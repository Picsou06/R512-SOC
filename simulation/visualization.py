from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Patch, Rectangle

from simulation.client import ETATS
from simulation.config import SENS, intervalle_porte

SOL = "#f7f3ea"
CARRELAGE = "#e9e2d3"
MUR = "#2f3b45"
RAYON = "#c9a27a"
RAYON_BORD = "#7a5638"
RAYON_ETAGERE = "#e7cfb3"
CAISSE_OUVERTE = "#2b7bba"
CAISSE_FERMEE = "#b9c7d3"
CAISSE_TAPIS = "#1d3f5e"
VITRE = "#7fd0f0"
VITRE_BORD = "#2a9fd6"
COULEURS_PORTE = {"entree": "#3aa66a", "sortie": "#d9534f", "entree_sortie": VITRE}
LIBELLES_PORTE = {"entree": "Entree", "sortie": "Sortie", "entree_sortie": "Entree / sortie"}
RESSOURCE = "#f2b134"
RESSOURCE_BORD = "#b5770c"
TEXTE = "#2f3b45"
SENS_UNIQUE = "#ffe082"
SENS_UNIQUE_FLECHE = "#b8860b"

COULEURS_ETAT = {
	"vers_produit": "#e4572e",
	"prise": "#f2b134",
	"vers_caisse": "#6a4c93",
	"paiement": "#2b7bba",
	"vers_sortie": "#3aa66a",
}


def dessiner_magasin(config, ax=None, rapport=True):
	if ax is None:
		_, ax = plt.subplots(figsize=(11, 9))

	largeur = config["magasin"]["largeur"]
	hauteur = config["magasin"]["hauteur"]

	ax.set_facecolor("white")
	ax.add_patch(Rectangle((0, 0), largeur, hauteur, facecolor=SOL, edgecolor="none", zorder=0))
	for x in range(1, int(largeur)):
		ax.plot([x, x], [0, hauteur], color=CARRELAGE, linewidth=0.6, zorder=0.5)
	for y in range(1, int(hauteur)):
		ax.plot([0, largeur], [y, y], color=CARRELAGE, linewidth=0.6, zorder=0.5)

	for mur in config["murs"]:
		if mur["type"] == "rayon":
			_dessiner_rayon(ax, mur)
		elif mur["type"] == "mur":
			ax.add_patch(Rectangle((mur["x"], mur["y"]), mur["largeur"], mur["hauteur"],
								   facecolor=MUR, edgecolor="none", zorder=4))
		else:
			_dessiner_sens_unique(ax, mur)

	for caisse in config.get("caisses", []):
		_dessiner_caisse(ax, caisse)

	murs = {
		"bas": ((0, 0), (1, 0), largeur),
		"haut": ((0, hauteur), (1, 0), largeur),
		"gauche": ((0, 0), (0, 1), hauteur),
		"droite": ((largeur, 0), (0, 1), hauteur),
	}
	for mur, (origine, direction, longueur) in murs.items():
		ouvertures = [intervalle_porte(p) for p in config["portes"] if p["mur"] == mur]
		for debut, fin in _segments_pleins(longueur, ouvertures):
			_tracer_segment(ax, origine, direction, debut, fin, color=MUR, linewidth=7,
							solid_capstyle="projecting", zorder=5)

	for porte in config["portes"]:
		_dessiner_porte(ax, porte, murs[porte["mur"]])

	rayons = {m["id"]: m for m in config["murs"] if m["type"] == "rayon"}
	for ressource in config["ressources"]:
		_dessiner_ressource(ax, ressource, rayons[ressource["rayon"]])

	marge = 1.5
	ax.set_xlim(-marge, largeur + marge)
	ax.set_ylim(-marge - 1, hauteur + marge)
	ax.set_aspect("equal")
	if rapport:
		ax.set_xlabel("x (m)", color=TEXTE)
		ax.set_ylabel("y (m)", color=TEXTE)
		ax.tick_params(colors=TEXTE, labelsize=9)
		for cote in ("top", "right"):
			ax.spines[cote].set_visible(False)
		for cote in ("left", "bottom"):
			ax.spines[cote].set_color("#b0b8bf")
	else:
		ax.set_xticks([])
		ax.set_yticks([])
		for cote in ax.spines.values():
			cote.set_visible(False)
		_dessiner_echelle(ax, largeur)

	nb_caisses = sum(c["ouverte"] for c in config.get("caisses", []))
	if rapport:
		nb_rayons = sum(m["type"] == "rayon" for m in config["murs"])
		ax.set_title(f"Magasin « {config['nom']} »", loc="left", fontsize=15,
					 fontweight="bold", color=TEXTE, pad=22)
		ax.text(0, 1.015, f"{largeur:g} m x {hauteur:g} m  ·  {nb_rayons} rayons  ·  "
						  f"{nb_caisses} caisses ouvertes  ·  {len(config['portes'])} portes",
				transform=ax.transAxes, fontsize=10, color="#6b7780")

	legende = _legende(config)
	ax.legend(handles=legende, loc="upper center", bbox_to_anchor=(0.5, -0.08 if rapport else 0.0),
			  ncol=len(legende), frameon=False, fontsize=9, handlelength=1.6,
			  columnspacing=1.4, labelcolor=TEXTE)
	return ax


def afficher_magasin(config, sortie=None):
	ax = dessiner_magasin(config)
	fig = ax.figure
	fig.tight_layout()
	if sortie:
		Path(sortie).parent.mkdir(parents=True, exist_ok=True)
		fig.savefig(sortie, dpi=150, bbox_inches="tight")
		plt.close(fig)
	else:
		plt.show()


def _dessiner_echelle(ax, largeur):
	longueur = 5
	x0, y0 = largeur - longueur, -1.9
	ax.plot([x0, x0 + longueur], [y0, y0], color=TEXTE, linewidth=2, solid_capstyle="butt")
	for x in (x0, x0 + longueur):
		ax.plot([x, x], [y0 - 0.2, y0 + 0.2], color=TEXTE, linewidth=1.5)
	ax.text(x0 + longueur / 2, y0 + 0.45, f"{longueur} m", ha="center", va="bottom",
			fontsize=8.5, color=TEXTE)


def _dessiner_rayon(ax, rayon):
	x, y, l, h = rayon["x"], rayon["y"], rayon["largeur"], rayon["hauteur"]
	ax.add_patch(FancyBboxPatch((x + 0.12, y - 0.12), l, h, boxstyle="round,pad=0,rounding_size=0.15",
								facecolor="black", alpha=0.12, edgecolor="none", zorder=1))
	ax.add_patch(FancyBboxPatch((x, y), l, h, boxstyle="round,pad=0,rounding_size=0.15",
								facecolor=RAYON, edgecolor=RAYON_BORD, linewidth=1.2, zorder=2))
	vertical = h >= l
	n = int((h if vertical else l) // 0.8)
	for i in range(1, n):
		if vertical:
			yy = y + i * h / n
			ax.plot([x + 0.12, x + l - 0.12], [yy, yy], color=RAYON_ETAGERE, linewidth=1, zorder=2.5)
		else:
			xx = x + i * l / n
			ax.plot([xx, xx], [y + 0.12, y + h - 0.12], color=RAYON_ETAGERE, linewidth=1, zorder=2.5)


def _dessiner_caisse(ax, caisse):
	x, y, l, h = caisse["x"], caisse["y"], caisse["largeur"], caisse["hauteur"]
	couleur = CAISSE_OUVERTE if caisse["ouverte"] else CAISSE_FERMEE
	ax.add_patch(FancyBboxPatch((x + 0.1, y - 0.1), l, h, boxstyle="round,pad=0,rounding_size=0.12",
								facecolor="black", alpha=0.12, edgecolor="none", zorder=1))
	ax.add_patch(FancyBboxPatch((x, y), l, h, boxstyle="round,pad=0,rounding_size=0.12",
								facecolor=couleur, edgecolor=CAISSE_TAPIS, linewidth=1.2, zorder=2))
	ax.add_patch(Rectangle((x + l * 0.3, y + 0.25), l * 0.4, h * 0.55,
						   facecolor=CAISSE_TAPIS if caisse["ouverte"] else "#8a9aa8",
						   edgecolor="none", zorder=2.5))
	numero = caisse["id"].split("_")[-1]
	ax.text(x + l / 2, y - 0.45, numero, ha="center", va="center", fontsize=8,
			color=TEXTE, fontweight="bold", zorder=3)


def _dessiner_porte(ax, porte, mur):
	origine, direction, _ = mur
	debut, fin = intervalle_porte(porte)
	couleur = COULEURS_PORTE[porte["type"]]
	_tracer_segment(ax, origine, direction, debut, fin, color=couleur, linewidth=9,
					solid_capstyle="butt", alpha=0.85, zorder=6)
	_tracer_segment(ax, origine, direction, debut, fin, color="white", linewidth=1.5,
					linestyle=(0, (2, 2)), zorder=7)
	for bord in (debut, fin):
		_tracer_segment(ax, origine, direction, bord - 0.05, bord + 0.05, color=VITRE_BORD
						if porte["type"] == "entree_sortie" else couleur, linewidth=11,
						solid_capstyle="butt", zorder=7)

	(ox, oy), (dx, dy) = origine, direction
	milieu = (debut + fin) / 2
	px, py = ox + dx * milieu, oy + dy * milieu
	decalage = {"bas": (0, -1.0), "haut": (0, 1.0), "gauche": (-1.0, 0), "droite": (1.0, 0)}
	ex, ey = decalage[porte["mur"]]
	ax.text(px + ex, py + ey, porte.get("nom", "").replace("_", " "), ha="center", va="center",
			fontsize=8, color=TEXTE, rotation=90 if porte["mur"] in ("gauche", "droite") else 0,
			zorder=7)


def _dessiner_ressource(ax, ressource, rayon):
	x, y = ressource["x"], ressource["y"]
	x0, y0, x1, y1 = rayon["x"], rayon["y"], rayon["x"] + rayon["largeur"], rayon["y"] + rayon["hauteur"]
	if abs(x - x0) < 1e-9 or abs(x - x1) < 1e-9:
		face = ([x, x], [max(y0, y - 0.6), min(y1, y + 0.6)])
	else:
		face = ([max(x0, x - 0.6), min(x1, x + 0.6)], [y, y])
	ax.plot(*face, color=RESSOURCE, linewidth=6, solid_capstyle="round", zorder=3)
	ax.add_patch(Circle((x, y), 0.7, facecolor=RESSOURCE, edgecolor="none", alpha=0.18, zorder=3))
	ax.plot(x, y, marker="*", markersize=15, color=RESSOURCE, markeredgecolor=RESSOURCE_BORD,
			markeredgewidth=1, linestyle="none", zorder=4)

	position_texte = ((x0 + x1) / 2, y1 + 1.3)
	ax.annotate(f"{ressource['id'].replace('_', ' ')} · stock {ressource['stock']}",
				(x, y), xytext=position_texte, textcoords="data", ha="center", va="bottom",
				fontsize=8.5, color=TEXTE, zorder=8,
				bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=RESSOURCE,
						  linewidth=1),
				arrowprops=dict(arrowstyle="-", color=RESSOURCE_BORD, linewidth=1,
								shrinkA=0, shrinkB=6))


def _dessiner_sens_unique(ax, zone):
	ax.add_patch(Rectangle((zone["x"], zone["y"]), zone["largeur"], zone["hauteur"],
						   facecolor=SENS_UNIQUE, edgecolor="none", alpha=0.5, zorder=1))
	sx, sy = SENS[zone["sens"]]
	cx, cy = zone["x"] + zone["largeur"] / 2, zone["y"] + zone["hauteur"] / 2
	ax.annotate("", xy=(cx + sx * 0.5, cy + sy * 0.5), xytext=(cx - sx * 0.5, cy - sy * 0.5),
				arrowprops=dict(arrowstyle="-|>", color=SENS_UNIQUE_FLECHE, linewidth=2), zorder=2)


def _segments_pleins(longueur, ouvertures):
	segments = []
	position = 0.0
	for debut, fin in sorted(ouvertures):
		if debut > position:
			segments.append((position, debut))
		position = max(position, fin)
	if position < longueur:
		segments.append((position, longueur))
	return segments


def _tracer_segment(ax, origine, direction, debut, fin, **style):
	(ox, oy), (dx, dy) = origine, direction
	ax.plot([ox + dx * debut, ox + dx * fin], [oy + dy * debut, oy + dy * fin], **style)


def _legende(config):
	elements = [
		Line2D([], [], color=MUR, linewidth=5, label="Mur"),
		Patch(facecolor=RAYON, edgecolor=RAYON_BORD, label="Rayon"),
	]
	caisses = config.get("caisses", [])
	if any(c["ouverte"] for c in caisses):
		elements.append(Patch(facecolor=CAISSE_OUVERTE, edgecolor=CAISSE_TAPIS, label="Caisse ouverte"))
	if any(not c["ouverte"] for c in caisses):
		elements.append(Patch(facecolor=CAISSE_FERMEE, edgecolor=CAISSE_TAPIS, label="Caisse fermee"))
	if any(m["type"] == "sens_unique" for m in config["murs"]):
		elements.append(Patch(facecolor=SENS_UNIQUE, edgecolor=SENS_UNIQUE_FLECHE, label="Sens unique"))
	types_presents = {p["type"] for p in config["portes"]}
	for type_porte in COULEURS_PORTE:
		if type_porte in types_presents:
			elements.append(Line2D([], [], color=COULEURS_PORTE[type_porte], linewidth=6,
								   label=LIBELLES_PORTE[type_porte]))
	if config["ressources"]:
		elements.append(Line2D([], [], marker="*", markersize=13, color=RESSOURCE,
							   markeredgecolor=RESSOURCE_BORD, linestyle="none", label="Ressource"))
	return elements


def figure_trajectoire(model):
	fig, ax = plt.subplots(figsize=(11, 9))
	dessiner_magasin(model.config, ax)
	for client in model.clients:
		trace = np.array(client.trajectoire)
		points = trace[:, 1:3].reshape(-1, 1, 2)
		segments = np.concatenate([points[:-1], points[1:]], axis=1)
		lignes = LineCollection(segments, cmap="viridis", linewidth=3, zorder=9,
								norm=plt.Normalize(0, model.comportement["vitesse_max"]))
		lignes.set_array(trace[1:, 3])
		ax.add_collection(lignes)
		for temps, etat in client.journal if len(model.clients) <= 5 else []:
			if etat in ("prise", "paiement"):
				i = int(np.argmin(np.abs(trace[:, 0] - temps)))
				ax.plot(trace[i, 1], trace[i, 2], "o", color="white", markeredgecolor=TEXTE,
						markersize=7, zorder=10)
				ax.annotate(f"t = {temps:.1f} s", (trace[i, 1], trace[i, 2]), xytext=(-10, 0),
							textcoords="offset points", ha="right", va="center", fontsize=8,
							color=TEXTE, zorder=10,
							bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none",
									  alpha=0.85))
	barre = fig.colorbar(lignes, ax=ax, shrink=0.6, pad=0.02)
	barre.set_label("vitesse (m/s)")
	c, p = model.comportement, model.parametres
	ax.text(0, -0.2, f"pas de temps {model.pas_de_temps} s · rayon {c['rayon']} m · "
					 f"vitesse max {c['vitesse_max']} m/s · acceleration {c['acceleration']} m/s² · "
					 f"freinage {c['deceleration']} m/s² · prise {c['temps_prise']} s · "
					 f"paiement {p['temps_paiement_fixe']} s + {p['temps_par_article']} s par article",
			transform=ax.transAxes, fontsize=8, color="#6b7780")
	return fig


def figure_vitesse(model):
	fig, ax = plt.subplots(figsize=(10, 4))
	for client in model.clients[:1]:
		trace = np.array(client.trajectoire)
		ax.plot(trace[:, 0], trace[:, 3], color=TEXTE, linewidth=1.5, label=client.identifiant)
		journal = client.journal + [(trace[-1, 0], "fin")]
		for (debut, etat), (fin, _) in zip(journal[1:], journal[2:]):
			if etat in COULEURS_ETAT:
				ax.axvspan(debut, fin, color=COULEURS_ETAT[etat], alpha=0.15, linewidth=0)
				ax.text((debut + fin) / 2, model.comportement["vitesse_max"] * 1.08,
						ETATS[etat], ha="center", fontsize=8, color=COULEURS_ETAT[etat])
	ax.set_xlabel("temps (s)")
	ax.set_ylabel("vitesse (m/s)")
	ax.set_ylim(0, model.comportement["vitesse_max"] * 1.2)
	ax.set_xlim(left=0)
	for cote in ("top", "right"):
		ax.spines[cote].set_visible(False)
	ax.set_title(f"Vitesse de {model.clients[0].identifiant} en fonction du temps "
				 f"(pas de temps {model.pas_de_temps} s)", loc="left", fontsize=11, color=TEXTE)
	fig.tight_layout()
	return fig
