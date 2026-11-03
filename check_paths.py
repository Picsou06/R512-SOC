import argparse
import math
import random
import sys
from collections import Counter
from multiprocessing import Pool

import numpy as np

from simulation.client import Client
from simulation.model import StoreModel

MAX_DURATION = 300.0
GRID_SPACING = 1.0
RANDOM_STARTS = 4000
NEAR_OBSTACLE_GAP = 0.03
SEED = 1
MAX_PENETRATION = 1e-6
MAX_WRONG_WAY = 0.001

model = None
fields = None


def goal_fields(store):
	found = {r["id"]: store.product_field(r) for r in store.config["resources"]}
	for checkout in store.config.get("checkouts", []):
		if checkout["open"]:
			found[checkout["id"]] = store.checkout_field(checkout)
	found["exit"] = store.exit_field()
	return found


def init_worker(config_path):
	global model, fields
	model = StoreModel(config_path, max_clients=0)
	fields = goal_fields(model)


def in_one_way_zone(store, point):
	return any(x0 < point[0] < x1 and y0 < point[1] < y1
			   for (x0, y0, x1, y1), _ in store.obstacles.one_way_zones)


def wrong_way_move(store, position, move):
	worst = 0.0
	for (x0, y0, x1, y1), (sx, sy) in store.obstacles.one_way_zones:
		if x0 < position[0] < x1 and y0 < position[1] < y1:
			worst = max(worst, -(move[0] * sx + move[1] * sy))
	return worst


def run_trip(task):
	goal, start, angle = task
	field = fields[goal]
	if math.isinf(field.value(start)):
		return {"goal": goal, "start": start, "status": "no_path", "penetration": 0.0, "wrong_way": 0.0}
	client = Client(model, "probe", start, [{"state": "to_product", "field": field}])
	client.heading = np.array([math.cos(angle), math.sin(angle)])
	penetration = wrong_way = elapsed = 0.0
	while client.state != "exited" and elapsed < MAX_DURATION:
		before = client.position.copy()
		client.step()
		elapsed += model.time_step
		penetration = max(penetration, -model.obstacles.distance(client.position))
		wrong_way = max(wrong_way, wrong_way_move(model, client.position, client.position - before))
	status = "arrived" if client.state == "exited" else "stuck"
	client.remove()
	return {"goal": goal, "start": start, "status": status, "penetration": penetration,
			"wrong_way": wrong_way}


def start_positions(store, generator):
	width = store.config["store"]["width"]
	height = store.config["store"]["height"]
	obstacles = store.obstacles
	starts = [(float(x), float(y)) for x in np.arange(GRID_SPACING / 2, width, GRID_SPACING)
			  for y in np.arange(GRID_SPACING / 2, height, GRID_SPACING)]
	starts += [(generator.uniform(0, width), generator.uniform(0, height)) for _ in range(RANDOM_STARTS)]
	if len(obstacles.balls):
		for _ in range(RANDOM_STARTS):
			x, y = obstacles.balls[generator.randrange(len(obstacles.balls))]
			angle = generator.uniform(0, 2 * math.pi)
			distance = obstacles.min_distance + generator.uniform(0, NEAR_OBSTACLE_GAP)
			starts.append((float(x + distance * math.cos(angle)), float(y + distance * math.sin(angle))))
	return [s for s in starts if obstacles.distance(s) >= 0]


def main():
	parser = argparse.ArgumentParser(description="Checks that a client reaches every goal from any start.")
	parser.add_argument("config", nargs="?", default="configs/reference.json",
						help="path to the config (default: configs/reference.json)")
	args = parser.parse_args()

	store = StoreModel(args.config, max_clients=0)
	goals = list(goal_fields(store))
	generator = random.Random(SEED)
	starts = start_positions(store, generator)
	tasks = [(goal, start, generator.uniform(-math.pi, math.pi)) for start in starts for goal in goals]
	with Pool(initializer=init_worker, initargs=(args.config,)) as pool:
		results = pool.map(run_trip, tasks, chunksize=50)

	failures = {
		"stuck": [r for r in results if r["status"] == "stuck"],
		"inside an obstacle": [r for r in results if r["penetration"] > MAX_PENETRATION],
		"no path to the exit": [r for r in results if r["status"] == "no_path" and r["goal"] == "exit"],
		"against a one-way zone": [r for r in results if r["wrong_way"] > MAX_WRONG_WAY
								   and not in_one_way_zone(store, r["start"])],
	}
	print(f"{len(tasks)} trips from {len(starts)} starts to {len(goals)} goals")
	print(f"status: {dict(Counter(r['status'] for r in results))}")
	print(f"no path by goal: {dict(Counter(r['goal'] for r in results if r['status'] == 'no_path'))}")
	print(f"deepest penetration: {max(r['penetration'] for r in results):.4f} m")
	for label, trips in failures.items():
		print(f"{label}: {len(trips)}")
		for trip in trips[:5]:
			print(f"  {trip['goal']} from ({trip['start'][0]:.2f}, {trip['start'][1]:.2f})")
	if any(failures.values()):
		sys.exit(1)


if __name__ == "__main__":
	main()
