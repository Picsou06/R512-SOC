import argparse
import os
import socket
import sys
from pathlib import Path

from watchfiles import PythonFilter, run_process

ROOT = Path(__file__).resolve().parent
WATCHED = [ROOT / "app.py", ROOT / "simulation"]


def solara_command(port):
	return f"{Path(sys.executable).as_posix()} -m solara run app.py --port {port} --no-open --production"


def port_in_use(port):
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
		return probe.connect_ex(("127.0.0.1", port)) == 0


def main():
	parser = argparse.ArgumentParser(description="Starts the website and restarts it whenever the code changes.")
	parser.add_argument("--port", type=int, default=8765, help="website port (default: 8765)")
	args = parser.parse_args()
	if port_in_use(args.port):
		sys.exit(f"Port {args.port} is already in use: another server is probably running. "
				 f"Stop it, or pick another port with --port.")
	os.chdir(ROOT)
	print(f"Website on http://localhost:{args.port}, restarts automatically when the code changes.")
	run_process(*WATCHED, target=solara_command(args.port), target_type="command",
				watch_filter=PythonFilter())


if __name__ == "__main__":
	main()
