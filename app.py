import os
import threading
import time

import solara
import solara.lab
from mesa.visualization.utils import force_update, update_counter

from simulation.client import ETATS
from simulation.model import MagasinModel
from simulation.visualization import COULEURS_ETAT
from simulation.vue_web import Repere, legende, svg_boites_collision, svg_magasin, svg_trajectoires

CONFIG_PAR_DEFAUT = "configs/reference.json"
BEAUCOUP_DE_CLIENTS = 10
PERIODE_IMAGE = 0.1
VITESSES = {"x0.5": 0.5, "x1": 1.0, "x2": 2.0, "x5": 5.0}


def _cadence(pas_de_temps, facteur):
	periode = max(PERIODE_IMAGE, pas_de_temps / facteur)
	return periode, max(1, round(periode * facteur / pas_de_temps))


def _creer_modele(chemin):
	try:
		return MagasinModel(chemin), None
	except (OSError, ValueError, KeyError, TypeError) as e:
		return None, f"{type(e).__name__} : {e}"


def _boites_collision(modele):
	return bool(modele and modele.config.get("affichage", {}).get("boites_collision", False))


def _date_modification(chemin):
	try:
		return os.path.getmtime(chemin)
	except OSError:
		return None


def _svg_client(client, repere, rayon, duree_transition, etiquette):
	v = solara.v
	x, y = repere.x(client.position[0]), repere.y(client.position[1])
	couleur = COULEURS_ETAT[client.etat]
	cap_x, cap_y = client.cap * rayon * 0.85
	if client.etat in ("prise", "paiement"):
		detail = f"{client.attente:.0f} s"
	else:
		detail = f"{client.vitesse:.1f} m/s"
	if etiquette:
		detail = f"{client.libelle} · {detail}"
	enfants = [
		v.Html(tag="circle", attributes={"r": rayon, "fill": couleur,
										 "stroke": "#ff1744" if client.en_contact else "white",
										 "stroke-width": 0.12 if client.en_contact else 0.07}),
		v.Html(tag="line", attributes={"x1": 0, "y1": 0, "x2": round(cap_x, 3),
									   "y2": round(-cap_y, 3), "stroke": "white",
									   "stroke-width": 0.09, "stroke-linecap": "round"}),
		v.Html(tag="text", attributes={"y": -rayon - 0.3,
									   "font-size": 0.45 if etiquette else 0.36,
									   "text-anchor": "middle", "fill": couleur,
									   "stroke": "white", "stroke-width": 0.12,
									   "paint-order": "stroke",
									   "font-family": "Roboto, Arial, sans-serif",
									   "font-weight": "bold"},
			   children=[detail]),
	]
	return v.Html(
		tag="g",
		style_=f"transform: translate({x}px, {y}px); "
			   f"transition: transform {duree_transition}ms linear",
		children=enfants,
	)


@solara.component
def VueMagasin(model, duree_transition, boites_collision):
	update_counter.get()
	repere = solara.use_memo(lambda: Repere(model.config), dependencies=[id(model)])
	stocks = tuple(sorted(model.stocks.items()))
	fond = solara.use_memo(lambda: svg_magasin(model.config, model.stocks),
						   dependencies=[id(model), stocks])
	rapport = repere.vue_largeur / repere.vue_hauteur
	calque = "position:absolute;inset:0;width:100%;height:100%"

	peu = model.nb_clients_total <= BEAUCOUP_DE_CLIENTS
	rayon = model.comportement["rayon"]
	dynamique = [_svg_client(client, repere, rayon, duree_transition, peu).key(client.identifiant)
				 for client in model.clients_presents]

	solara.v.Html(
		tag="div",
		style_=f"position:relative;width:100%;max-width:calc((100vh - 140px) * {rapport:.4f});"
			   f"aspect-ratio:{rapport:.4f}",
		children=[
			solara.HTML(tag="div", style=calque, unsafe_innerHTML=(
				f'<svg viewBox="{repere.view_box}" style="width:100%;height:100%;display:block">'
				f"{fond}</svg>")),
			solara.HTML(tag="div", style=calque, unsafe_innerHTML=(
				f'<svg viewBox="{repere.view_box}" style="width:100%;height:100%;display:block">'
				f"{svg_trajectoires(model, repere) if peu else ''}"
				f"{svg_boites_collision(model.obstacles, repere) if boites_collision else ''}</svg>")),
			solara.v.Html(tag="svg", attributes={"viewBox": repere.view_box}, style_=calque,
						  children=dynamique),
		],
	)
	solara.HTML(tag="div", unsafe_innerHTML=legende(model.config),
				style="margin-top:8px;display:flex;flex-wrap:wrap")


@solara.component
def Informations(model):
	update_counter.get()
	lignes = [f"<b>Temps :</b> {model.temps:.1f} s"]
	if model.nb_clients_total > BEAUCOUP_DE_CLIENTS:
		lignes += _resume(model)
		solara.HTML(tag="div", unsafe_innerHTML="<br>".join(lignes),
					style="line-height:1.8;font-size:14px")
		return
	for client in model.clients:
		if client.etat == "sorti":
			lignes.append(f"<b>{client.identifiant} :</b> sorti en {client.journal[-1][0]:.1f} s")
		else:
			lignes.append(f"<b>{client.identifiant} :</b> {client.libelle.lower()}, "
						  f"{client.vitesse:.1f} m/s")
		lignes.append(f"&nbsp;&nbsp;contacts avec un obstacle : {client.nb_contacts}")
	solara.HTML(tag="div", unsafe_innerHTML="<br>".join(lignes),
				style="line-height:1.8;font-size:14px")


def _resume(model):
	presents = model.clients_presents
	sortis = model.clients_sortis
	lignes = [f"<b>Clients entres :</b> {len(model.clients)} / {model.nb_clients_total}",
			  f"<b>Dans le magasin :</b> {len(presents)}"]
	for etat in COULEURS_ETAT:
		nombre = sum(1 for c in presents if c.etat == etat)
		if nombre:
			lignes.append(f"&nbsp;&nbsp;<span style='color:{COULEURS_ETAT[etat]}'>&#9679;</span> "
						  f"{ETATS[etat].lower()} : {nombre}")
	lignes.append(f"<b>Sortis :</b> {len(sortis)}")
	if sortis:
		durees = [c.journal[-1][0] - c.journal[0][0] for c in sortis]
		avec = sum(1 for c in sortis if c.articles)
		lignes.append(f"&nbsp;&nbsp;avec leurs achats : {avec}, sans produit : {len(sortis) - avec}")
		lignes.append(f"&nbsp;&nbsp;temps dans le magasin : moyen {sum(durees) / len(durees):.1f} s, "
					  f"max {max(durees):.1f} s")
	stocks = ", ".join(f"{nom.replace('_', ' ')} {n}" for nom, n in model.stocks.items())
	lignes.append(f"<b>Stock :</b> {stocks}")
	lignes.append(f"<b>Contacts avec un obstacle :</b> {sum(c.nb_contacts for c in model.clients)}")
	return lignes


@solara.component
def Page():
	initial, erreur_initiale = solara.use_memo(
		lambda: _creer_modele(CONFIG_PAR_DEFAUT), [])
	modele = solara.use_reactive(initial)
	chemin = solara.use_reactive(CONFIG_PAR_DEFAUT)
	boites_collision = solara.use_reactive(_boites_collision(initial))
	en_lecture = solara.use_reactive(False)
	vitesse = solara.use_reactive("x1")
	erreur = solara.use_reactive(erreur_initiale)

	def theme_sombre():
		solara.lab.theme.dark = True

	solara.use_effect(theme_sombre, [])

	def charger():
		nouveau, probleme = _creer_modele(chemin.value)
		erreur.set(probleme)
		if nouveau is not None:
			modele.set(nouveau)
			boites_collision.set(_boites_collision(nouveau))

	def surveiller_config():
		arret = threading.Event()

		def boucle():
			derniere = _date_modification(chemin.value)
			while not arret.wait(1.0):
				date = _date_modification(chemin.value)
				if date != derniere:
					derniere = date
					charger()

		threading.Thread(target=boucle, daemon=True).start()
		return arret.set

	solara.use_effect(surveiller_config, [chemin.value])

	def lire():
		if not en_lecture.value or modele.value is None:
			return None
		arret = threading.Event()
		model = modele.value
		facteur = VITESSES[vitesse.value]
		periode, pas_par_image = _cadence(model.pas_de_temps, facteur)

		def boucle():
			prochain = time.perf_counter()
			while not arret.is_set():
				for _ in range(pas_par_image):
					if model.running:
						model.step()
				force_update()
				if not model.running:
					en_lecture.set(False)
					return
				prochain += periode
				attente = prochain - time.perf_counter()
				if attente > 0:
					arret.wait(attente)
				else:
					prochain = time.perf_counter()

		threading.Thread(target=boucle, daemon=True).start()
		return arret.set

	solara.use_effect(lire, [en_lecture.value, vitesse.value, id(modele.value)])

	def un_pas():
		if modele.value is not None and modele.value.running:
			modele.value.step()
			force_update()

	def recommencer():
		en_lecture.set(False)
		charger()

	termine = modele.value is None or not modele.value.running
	pas_de_temps = modele.value.pas_de_temps if modele.value is not None else PERIODE_IMAGE
	duree_transition = round(_cadence(pas_de_temps, VITESSES[vitesse.value])[0] * 1000)

	solara.Title("Simulation de magasin")
	with solara.Columns([1, 3]):
		with solara.Column():
			with solara.Card("Controles"):
				with solara.Row():
					solara.Button("Pause" if en_lecture.value else "Lecture",
								  icon_name="mdi-pause" if en_lecture.value else "mdi-play",
								  on_click=lambda: en_lecture.set(not en_lecture.value),
								  disabled=termine, color="primary")
					solara.Button("Pas", icon_name="mdi-step-forward", on_click=un_pas,
								  disabled=en_lecture.value or termine)
					solara.Button("Rejouer", icon_name="mdi-restart", on_click=recommencer)
				solara.Text("Vitesse de lecture")
				solara.ToggleButtonsSingle(value=vitesse, values=list(VITESSES))
			with solara.Card("Configuration"):
				solara.InputText("Fichier", value=chemin, continuous_update=False)
				solara.Checkbox(label="Boites de collision", value=boites_collision)
				solara.Button("Charger", on_click=recommencer, text=True)
			with solara.Card("Informations"):
				if modele.value is not None:
					Informations(modele.value)
		with solara.Column():
			if erreur.value and modele.value is None:
				solara.Error(f"Configuration invalide : {erreur.value}. Corrige le fichier, "
							 f"la page se recharge toute seule.")
			elif erreur.value:
				solara.Error(f"Configuration invalide, le dernier magasin valide reste affiche. "
							 f"{erreur.value}")
			if modele.value is not None:
				VueMagasin(modele.value, duree_transition, boites_collision.value)
