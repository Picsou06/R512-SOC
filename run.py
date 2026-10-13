import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from simulation.config import load_config
from simulation.model import MagasinModel
from simulation.visualization import afficher_magasin, figure_trajectoire, figure_vitesse


def main():
	parser = argparse.ArgumentParser(description="Affiche le magasin decrit par une config JSON.")
	parser.add_argument("config", nargs="?", default="configs/reference.json",
						help="chemin de la config (par defaut : configs/reference.json)")
	parser.add_argument("--sortie", help="exporte l'image dans ce fichier au lieu d'ouvrir une fenetre")
	parser.add_argument("--simuler", action="store_true",
						help="simule les clients jusqu'a leur sortie et trace trajectoire et vitesse")
	args = parser.parse_args()

	if not args.simuler:
		afficher_magasin(load_config(args.config), sortie=args.sortie)
		if args.sortie:
			print(f"Image exportee : {args.sortie}")
		return

	model = MagasinModel(args.config).simuler()
	if len(model.clients) <= 5:
		for client in model.clients:
			print(client.identifiant)
			for temps, etat in client.journal:
				print(f"  {temps:6.1f} s  {etat}")
	else:
		durees = [c.journal[-1][0] - c.journal[0][0] for c in model.clients_sortis]
		print(f"{len(model.clients_sortis)} clients sortis sur {model.nb_clients_total} "
			  f"en {model.temps:.1f} s")
		print(f"  sans produit (rupture de stock) : {sum(1 for c in model.clients if not c.articles)}")
		print(f"  temps dans le magasin : moyen {sum(durees) / len(durees):.1f} s, "
			  f"max {max(durees):.1f} s")
	figures = {"": figure_trajectoire(model), "_vitesse": figure_vitesse(model)}
	if args.sortie:
		sortie = Path(args.sortie)
		sortie.parent.mkdir(parents=True, exist_ok=True)
		for suffixe, fig in figures.items():
			chemin = sortie.with_name(sortie.stem + suffixe + sortie.suffix)
			fig.savefig(chemin, dpi=150, bbox_inches="tight")
			print(f"Image exportee : {chemin}")
	else:
		plt.show()


if __name__ == "__main__":
	main()
