import argparse
import sys
from collections import Counter, defaultdict

from simulation.model import StoreModel

MAX_DURATION = 3600.0


def events_by_checkout(model):
	found = defaultdict(list)
	for time, checkout, client, event in model.checkout_log:
		found[checkout].append((time, client, event))
	return found


def check_checkout(events):
	"""Erreurs d'une caisse : ordre de passage et un seul client servi a la fois."""
	errors = []
	joined = [client for _, client, event in events if event == "joined"]
	served = [client for _, client, event in events if event == "served"]
	if served != joined[:len(served)]:
		errors.append(f"service order {served} differs from arrival order {joined}")

	current = None
	for time, client, event in events:
		if event == "served":
			if current is not None:
				errors.append(f"{time:.1f} s: {client} served while {current} is still paying")
			current = client
		elif event == "left" and client == current:
			current = None
	return errors


def check_clients(model):
	"""Erreurs par client : une seule caisse, gardee du choix jusqu'au depart."""
	errors = []
	seen = defaultdict(list)
	for _, checkout, client, event in model.checkout_log:
		seen[client].append((checkout, event))
	for client, events in seen.items():
		checkouts = {checkout for checkout, _ in events}
		if len(checkouts) > 1:
			errors.append(f"{client} changed queue: {sorted(checkouts)}")
		count = Counter(event for _, event in events)
		if any(count[e] != 1 for e in ("chosen", "joined", "served", "left")):
			errors.append(f"{client}: events {dict(count)}")
	return errors


def waits(model):
	joined = {}
	found = []
	for time, _, client, event in model.checkout_log:
		if event == "joined":
			joined[client] = time
		elif event == "served":
			found.append(time - joined[client])
	return found


def run(config, seed, verbose):
	model = StoreModel(config, rng=seed).simulate(MAX_DURATION)
	by_checkout = events_by_checkout(model)
	errors = check_clients(model)
	for checkout in sorted(by_checkout):
		errors += [f"{checkout}: {e}" for e in check_checkout(by_checkout[checkout])]
	if len(model.exited_clients) != model.total_clients:
		errors.append(f"{model.total_clients - len(model.exited_clients)} clients did not leave")

	print(f"{config} (seed {seed}): {len(model.exited_clients)}/{model.total_clients} "
		  f"clients left in {model.current_time:.1f} s")
	for checkout in sorted(by_checkout):
		served = [client for _, client, event in by_checkout[checkout] if event == "served"]
		print(f"  {checkout}: {len(served)} clients")
		if verbose:
			print(f"    service order: {', '.join(served)}")
	found = waits(model)
	if found:
		print(f"  wait in queue: mean {sum(found) / len(found):.1f} s, max {max(found):.1f} s")
	print(f"  {len(errors)} error(s)")
	for error in errors[:10]:
		print(f"    {error}")
	return not errors


def main():
	parser = argparse.ArgumentParser(description="Checks the checkout queues: one client served at a time, in order of arrival.")
	parser.add_argument("configs", nargs="*", default=["configs/tests/checkout_queue.json"],
						help="configs to simulate (default: configs/tests/checkout_queue.json)")
	parser.add_argument("--seeds", type=int, default=1, help="number of seeds per config")
	parser.add_argument("--verbose", action="store_true", help="print the service order of each checkout")
	args = parser.parse_args()

	results = [run(config, seed, args.verbose)
			   for config in args.configs for seed in range(1, args.seeds + 1)]
	print(f"{sum(results)}/{len(results)} simulations without error")
	sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
	main()
