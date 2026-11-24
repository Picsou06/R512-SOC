import argparse
from statistics import mean, pstdev

from run import indicators
from simulation.model import StoreModel

MAX_DURATION = 3600.0
DEFAULT_SEEDS = 5


def run_indicators(config, seed, max_duration):
	model = StoreModel(config, rng=seed).simulate(max_duration)
	durations, contacts, waits = indicators(model)
	return {
		"time_in_store": mean(durations),
		"contacts": mean(contacts),
		"overlap": model.max_overlap,
		"checkout_wait": mean(waits) if waits else 0.0,
	}


def aggregate(config, seeds, max_duration):
	runs = [run_indicators(config, seed, max_duration) for seed in seeds]
	stats = {}
	for key in runs[0]:
		values = [run[key] for run in runs]
		stats[key] = (mean(values), pstdev(values))
	return stats


def main():
	parser = argparse.ArgumentParser(
		description="Runs a config with several seeds and aggregates the indicators (mean and "
					"standard deviation across seeds), so that comparing configurations does "
					"not depend on a single random draw.")
	parser.add_argument("configs", nargs="*", default=["configs/reference.json"],
						help="configs to simulate (default: configs/reference.json)")
	parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS, help="number of seeds per config")
	parser.add_argument("--max-duration", type=float, default=MAX_DURATION,
						help=f"simulated time limit in s (default: {MAX_DURATION:.0f})")
	args = parser.parse_args()

	for config in args.configs:
		stats = aggregate(config, range(1, args.seeds + 1), args.max_duration)
		print(f"{config} ({args.seeds} seeds):")
		for key, (m, s) in stats.items():
			print(f"  {key}: {m:.3f} +/- {s:.3f}")


if __name__ == "__main__":
	main()
