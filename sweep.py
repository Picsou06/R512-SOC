import argparse
import csv
import itertools
import os
import statistics
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from check_invariants import check_step
from simulation.config import load_config, save_config
from simulation.model import StoreModel

MAX_DURATION = 3600.0
STOCK_FACTORS = (0.5, 1.0, 2.0, 4.0)
INTERVALS = (0.5, 1.0, 1.5, 3.0)
COLUMNS = ("stock_factor", "interval", "seed", "total_stock", "clients", "exited", "duration",
		   "buyers", "without_product", "missing_products", "items_sold", "stock_left",
		   "time_in_store_mean", "time_in_store_max", "checkout_wait_mean", "checkout_wait_max",
		   "max_queue", "contacts_mean", "contacts_max", "max_overlap", "max_present", "errors", "not_exited")


def variant(base, stock_factor, interval):
	config = load_config(base)
	config["name"] = f"{config['name']}_stock{stock_factor:g}_interval{interval:g}"
	for resource in config["resources"]:
		resource["stock"] = round(resource["stock"] * stock_factor)
	config["client_flow"]["interval"] = interval
	return config


def simulate(job):
	"""Runs one variant and returns its indicators; the invariants of check_invariants.py are
	checked at every step."""
	base, stock_factor, interval, seed, max_duration, folder = job
	path = Path(folder) / f"stock{stock_factor:g}_interval{interval:g}.json"
	if not path.exists():
		save_config(variant(base, stock_factor, interval), path)
	model = StoreModel(path, rng=seed)
	initial_stocks = dict(model.stocks)
	errors = len(check_step(model, initial_stocks))
	max_queue = max_present = 0
	while model.running and model.current_time < max_duration:
		model.step()
		errors += len(check_step(model, initial_stocks))
		max_queue = max(max_queue, max((len(q) for q in model.queues.values()), default=0))
		max_present = max(max_present, len(model.present_clients))
	exited = model.exited_clients

	joined, waits = {}, []
	for time, _, client, event in model.checkout_log:
		if event == "joined":
			joined[client] = time
		elif event == "served":
			waits.append(time - joined[client])
	durations = [c.log[-1][0] - c.log[0][0] for c in exited] or [0.0]
	contacts = [c.client_contact_count for c in model.clients] or [0]
	return {
		"stock_factor": stock_factor, "interval": interval, "seed": seed,
		"total_stock": sum(initial_stocks.values()),
		"clients": model.total_clients, "exited": len(exited),
		"duration": round(model.current_time, 1),
		"buyers": sum(1 for c in model.clients if c.items),
		"without_product": sum(1 for c in model.clients if not c.items),
		"missing_products": sum(1 for c in model.clients for _, e in c.log if e == "out_of_stock"),
		"items_sold": sum(c.items for c in model.clients),
		"stock_left": sum(model.stocks.values()),
		"time_in_store_mean": round(statistics.mean(durations), 1),
		"time_in_store_max": round(max(durations), 1),
		"checkout_wait_mean": round(statistics.mean(waits), 1) if waits else 0.0,
		"checkout_wait_max": round(max(waits), 1) if waits else 0.0,
		"max_queue": max_queue,
		"contacts_mean": round(statistics.mean(contacts), 1),
		"contacts_max": max(contacts),
		"max_overlap": round(model.max_overlap, 4),
		"max_present": max_present,
		"errors": errors,
		"not_exited": model.total_clients - len(exited),
	}


def average(rows):
	"""One row per (stock, interval): mean over the seeds, max for the maxima and errors."""
	grouped = {}
	for row in rows:
		grouped.setdefault((row["stock_factor"], row["interval"]), []).append(row)
	result = []
	for key in sorted(grouped):
		group = grouped[key]
		row = {"stock_factor": key[0], "interval": key[1], "seed": len(group)}
		for column in COLUMNS[3:]:
			values = [r[column] for r in group]
			if column.endswith("_max") or column in ("max_queue", "max_overlap", "max_present",
													 "errors", "not_exited"):
				row[column] = max(values)
			else:
				row[column] = round(statistics.mean(values), 1)
		result.append(row)
	return result


def write_csv(rows, path):
	path.parent.mkdir(parents=True, exist_ok=True)
	with open(path, "w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=COLUMNS)
		writer.writeheader()
		writer.writerows(rows)
	print(f"Results saved: {path}")


def print_table(rows):
	headers = ("stock", "interval (s)", "stock units", "duration (s)", "buyers", "no product",
			   "time in store (s)", "checkout wait (s)", "max queue", "contacts/client",
			   "max present", "errors", "not exited")
	print("| " + " | ".join(headers) + " |")
	print("|" + "---|" * len(headers))
	for r in rows:
		cells = (f"x{r['stock_factor']:g}", f"{r['interval']:g}", f"{r['total_stock']:g}",
				 f"{r['duration']:g}", f"{r['buyers']:g}", f"{r['without_product']:g}",
				 f"{r['time_in_store_mean']:g} (max {r['time_in_store_max']:g})",
				 f"{r['checkout_wait_mean']:g} (max {r['checkout_wait_max']:g})",
				 f"{r['max_queue']}", f"{r['contacts_mean']:g}", f"{r['max_present']}",
				 f"{r['errors']}", f"{r['not_exited']}")
		print("| " + " | ".join(cells) + " |")


def main():
	parser = argparse.ArgumentParser(
		description="Simulates the full scenario for several stock values and entry intervals "
					"and records the results (invariants checked at every step).")
	parser.add_argument("config", nargs="?", default="configs/reference.json",
						help="base config (default: configs/reference.json)")
	parser.add_argument("--stock-factors", type=float, nargs="+", default=STOCK_FACTORS,
						help="factors applied to the stock of every product")
	parser.add_argument("--intervals", type=float, nargs="+", default=INTERVALS,
						help="time between two clients at the entrance, in s")
	parser.add_argument("--seeds", type=int, default=2, help="number of seeds per variant")
	parser.add_argument("--max-duration", type=float, default=MAX_DURATION,
						help=f"simulated time limit in s (default: {MAX_DURATION:.0f})")
	parser.add_argument("--jobs", type=int, default=os.cpu_count(), help="parallel simulations")
	parser.add_argument("--output", default="outputs/sweep.csv",
						help="CSV of every run; the mean per variant goes next to it")
	args = parser.parse_args()

	with tempfile.TemporaryDirectory() as folder:
		jobs = [(args.config, s, i, seed, args.max_duration, folder)
				for s, i in itertools.product(args.stock_factors, args.intervals)
				for seed in range(1, args.seeds + 1)]
		# Write the variants before the workers start, so that they never write the same file.
		for s, i in itertools.product(args.stock_factors, args.intervals):
			save_config(variant(args.config, s, i), Path(folder) / f"stock{s:g}_interval{i:g}.json")
		with ProcessPoolExecutor(max_workers=args.jobs) as pool:
			rows = []
			for row in pool.map(simulate, jobs):
				rows.append(row)
				print(f"stock x{row['stock_factor']:g}, interval {row['interval']:g} s, "
					  f"seed {row['seed']}: {row['exited']}/{row['clients']} left in "
					  f"{row['duration']} s, {row['errors']} invariant error(s)", flush=True)

	output = Path(args.output)
	write_csv(rows, output)
	means = average(rows)
	write_csv(means, output.with_name(output.stem + "_mean" + output.suffix))
	print_table(means)


if __name__ == "__main__":
	main()
