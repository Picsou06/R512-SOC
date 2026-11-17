import argparse
import sys
from collections import Counter

from simulation.model import StoreModel

MAX_DURATION = 3600.0
MAX_PRINTED = 10


def check_step(model, initial_stocks):
	"""Errors at the current time: stocks, clients per checkout, checkouts per client."""
	errors = []
	t = model.current_time

	taken = Counter()
	for client in model.clients:
		taken.update(client.basket)
	for product, stock in model.stocks.items():
		if stock < 0:
			errors.append(f"{t:.1f} s: stock of {product} is {stock}")
		if stock + taken[product] != initial_stocks[product]:
			errors.append(f"{t:.1f} s: {product}: {stock} left + {taken[product]} taken "
						  f"!= {initial_stocks[product]} at start")

	# One checkout per client: a client is in at most one list (heading or queue) of one
	# checkout, and it is the checkout it chose.
	places = Counter()
	for checkout in model.queues:
		for client in model.heading[checkout] + model.queues[checkout]:
			places[client] += 1
			if client.checkout != checkout:
				errors.append(f"{t:.1f} s: {client.identifier} is in the line of {checkout} "
							  f"but chose {client.checkout}")
	for client, count in places.items():
		if count > 1:
			errors.append(f"{t:.1f} s: {client.identifier} is in {count} lines")
	for client in model.present_clients:
		in_line = client.state in ("to_checkout", "queuing", "paying")
		if in_line and places[client] != 1:
			errors.append(f"{t:.1f} s: {client.identifier} ({client.state}) is in "
						  f"{places[client]} lines")
		if not in_line and places[client]:
			errors.append(f"{t:.1f} s: {client.identifier} ({client.state}) is still in a line")

	# One client per checkout: at most one client pays, and it is the first of the line.
	paying = Counter(c.checkout for c in model.present_clients if c.state == "paying")
	for checkout, count in paying.items():
		if count > 1:
			errors.append(f"{t:.1f} s: {checkout} serves {count} clients")
		elif model.queues[checkout][0].state != "paying":
			errors.append(f"{t:.1f} s: {checkout}: the paying client is not the first of the line")

	# No client lost: waiting outside + present + exited = expected.
	counted = len(model.pending) + len(model.clients)
	if counted != model.total_clients:
		errors.append(f"{t:.1f} s: {counted} clients counted, {model.total_clients} expected")
	return errors


def run(config, seed, max_duration):
	model = StoreModel(config, rng=seed)
	initial_stocks = dict(model.stocks)
	errors = check_step(model, initial_stocks)
	while model.running and model.current_time < max_duration:
		model.step()
		errors += check_step(model, initial_stocks)

	exited = len(model.exited_clients)
	if exited != model.total_clients:
		errors.append(f"{model.total_clients - exited} clients did not leave "
					  f"after {model.current_time:.1f} s")

	served = Counter(client for _, _, client, event in model.checkout_log if event == "served")
	buyers = [c for c in model.clients if c.items]
	for client in buyers:
		if served[client.identifier] != 1:
			errors.append(f"{client.identifier} paid {served[client.identifier]} times")
	for client in model.clients:
		if not client.items and served[client.identifier]:
			errors.append(f"{client.identifier} paid without any item")

	out = sum(1 for c in model.clients for _, e in c.log if e == "out_of_stock")
	stocks = ", ".join(f"{p} {initial_stocks[p]} -> {s}" for p, s in model.stocks.items())
	print(f"{config} (seed {seed}): {exited}/{model.total_clients} clients left "
		  f"in {model.current_time:.1f} s")
	print(f"  stocks: {stocks}")
	print(f"  {len(buyers)} clients paid, {out} products missing, "
		  f"{model.total_clients - len(buyers)} clients left without buying")
	print(f"  {len(errors)} error(s)")
	for error in errors[:MAX_PRINTED]:
		print(f"    {error}")
	return not errors


def main():
	parser = argparse.ArgumentParser(
		description="Checks the invariants of a full simulation: stock never negative, one "
					"checkout per client, one client per checkout, all clients leave.")
	parser.add_argument("configs", nargs="*", default=["configs/reference.json"],
						help="configs to simulate (default: configs/reference.json)")
	parser.add_argument("--seeds", type=int, default=1, help="number of seeds per config")
	parser.add_argument("--max-duration", type=float, default=MAX_DURATION,
						help=f"simulated time limit in s (default: {MAX_DURATION:.0f})")
	args = parser.parse_args()

	results = [run(config, seed, args.max_duration)
			   for config in args.configs for seed in range(1, args.seeds + 1)]
	print(f"{sum(results)}/{len(results)} simulations without error")
	sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
	main()
