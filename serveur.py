import argparse
import os
import socket
import sys
from pathlib import Path

from watchfiles import PythonFilter, run_process

RACINE = Path(__file__).resolve().parent
SURVEILLES = [RACINE / "app.py", RACINE / "simulation"]


def commande_solara(port):
	return f"{Path(sys.executable).as_posix()} -m solara run app.py --port {port} --no-open --production"


def port_utilise(port):
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sonde:
		return sonde.connect_ex(("127.0.0.1", port)) == 0


def main():
	parser = argparse.ArgumentParser(description="Lance le site et le redemarre a chaque modification du code.")
	parser.add_argument("--port", type=int, default=8765, help="port du site (par defaut : 8765)")
	args = parser.parse_args()
	if port_utilise(args.port):
		sys.exit(f"Le port {args.port} est deja utilise : un autre serveur tourne sans doute. "
				 f"Arrete-le, ou choisis un autre port avec --port.")
	os.chdir(RACINE)
	print(f"Site sur http://localhost:{args.port}, redemarrage automatique quand le code change.")
	run_process(*SURVEILLES, target=commande_solara(args.port), target_type="command",
				watch_filter=PythonFilter())


if __name__ == "__main__":
	main()
