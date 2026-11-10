import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt

from simulation.config import load_config
from simulation.model import StoreModel
from simulation.visualization import show_store, speed_figure, trajectory_figure


def checkout_wait(client):
	by_state = {state: time for time, state in client.log}
	return by_state.get("to_checkout"), by_state.get("paying")


def main():
	parser = argparse.ArgumentParser(description="Shows the store described by a JSON config.")
	parser.add_argument("config", nargs="?", default="configs/reference.json",
						help="path to the config (default: configs/reference.json)")
	parser.add_argument("--output", help="save the image to this file instead of opening a window")
	parser.add_argument("--simulate", action="store_true",
						help="simulate the clients until they leave and plot trajectory and speed")
	args = parser.parse_args()

	if not args.simulate:
		show_store(load_config(args.config), output=args.output)
		if args.output:
			print(f"Image saved: {args.output}")
		return

	model = StoreModel(args.config).simulate()
	if not model.exited_clients:
		sys.exit("No client left the store: nothing to plot.")
	if len(model.clients) <= 5:
		for client in model.clients:
			print(client.identifier)
			for time, state in client.log:
				print(f"  {time:6.1f} s  {state}")
	else:
		durations = [c.log[-1][0] - c.log[0][0] for c in model.exited_clients]
		contacts = [c.client_contact_count for c in model.clients]
		waits = [end - start for c in model.exited_clients
				 for start, end in [checkout_wait(c)] if end is not None]
		print(f"{len(model.exited_clients)} clients left out of {model.total_clients} "
			  f"in {model.current_time:.1f} s")
		print(f"  without product (out of stock): {sum(1 for c in model.clients if not c.items)}")
		print(f"  time in store: mean {sum(durations) / len(durations):.1f} s, "
			  f"max {max(durations):.1f} s")
		print(f"  client contacts: mean {sum(contacts) / len(contacts):.1f}, max {max(contacts)}, "
			  f"maximum remaining overlap {model.max_overlap:.3f} m")
		if waits:
			print(f"  checkout wait: mean {sum(waits) / len(waits):.1f} s, max {max(waits):.1f} s")
	figures = {"": trajectory_figure(model), "_speed": speed_figure(model)}
	if args.output:
		output = Path(args.output)
		output.parent.mkdir(parents=True, exist_ok=True)
		for suffix, fig in figures.items():
			path = output.with_name(output.stem + suffix + output.suffix)
			fig.savefig(path, dpi=150, bbox_inches="tight")
			print(f"Image saved: {path}")
	else:
		plt.show()


if __name__ == "__main__":
	main()
