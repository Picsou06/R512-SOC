import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

from simulation.model import StoreModel
from simulation.visualization import TEXT, draw_store

CELL = 0.5
MOVING_SPEED = 0.05
CROSSING_ANGLE = 45.0
HEAD_ON_ANGLE = 135.0
DIRECTION_BINS = 16
HOTSPOTS = 5


def samples(model):
	by_time = {}
	for number, client in enumerate(model.clients):
		trace = np.array(client.trajectory)
		velocity = np.zeros((len(trace), 2))
		if len(trace) > 1:
			velocity[1:] = np.diff(trace[:, 1:3], axis=0) / np.diff(trace[:, 0])[:, None]
		for (time, x, y, _), (vx, vy) in zip(trace, velocity):
			by_time.setdefault(round(time, 6), []).append((number, x, y, vx, vy))
	return by_time


def passage_maps(model, by_time):
	width = model.config["store"]["width"]
	height = model.config["store"]["height"]
	shape = (math.ceil(height / CELL), math.ceil(width / CELL))
	headings = np.zeros(shape + (DIRECTION_BINS,))
	overlap = np.zeros(shape)
	kinds = {"same direction": 0.0, "crossing": 0.0, "head-on": 0.0, "one stopped": 0.0}
	pairs = set()
	diameter = 2 * model.behavior["radius"]
	visits = {}

	def cell(x, y):
		return min(int(y / CELL), shape[0] - 1), min(int(x / CELL), shape[1] - 1)

	for time in sorted(by_time):
		present = by_time[time]
		for number, x, y, vx, vy in present:
			if math.hypot(vx, vy) > MOVING_SPEED:
				visits.setdefault((number, cell(x, y)), []).append(math.atan2(vy, vx))
		if len(present) < 2:
			continue
		data = np.array(present)
		offsets = data[:, None, 1:3] - data[None, :, 1:3]
		distance = np.hypot(offsets[..., 0], offsets[..., 1])
		for i, j in zip(*np.nonzero(np.triu(distance < diameter, k=1))):
			a, b = data[i], data[j]
			overlap[cell((a[1] + b[1]) / 2, (a[2] + b[2]) / 2)] += model.time_step
			pairs.add((int(a[0]), int(b[0])))
			kinds[pair_kind(a[3:5], b[3:5])] += model.time_step

	for (_, (i, j)), angles in visits.items():
		mean = math.atan2(np.mean(np.sin(angles)), np.mean(np.cos(angles)))
		headings[i, j, int((mean + math.pi) / (2 * math.pi) * DIRECTION_BINS) % DIRECTION_BINS] += 1
	return headings.sum(axis=2), crossing_pairs(headings), overlap, kinds, pairs


def pair_kind(u, v):
	if min(np.linalg.norm(u), np.linalg.norm(v)) <= MOVING_SPEED:
		return "one stopped"
	angle = math.degrees(math.acos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
	if angle < CROSSING_ANGLE:
		return "same direction"
	return "crossing" if angle < HEAD_ON_ANGLE else "head-on"


def crossing_pairs(headings):
	bin_angle = 360.0 / DIRECTION_BINS
	crossings = np.zeros(headings.shape[:2])
	for a in range(DIRECTION_BINS):
		for b in range(a + 1, DIRECTION_BINS):
			gap = min(b - a, DIRECTION_BINS - (b - a)) * bin_angle
			if gap >= CROSSING_ANGLE:
				crossings += headings[..., a] * headings[..., b]
	return crossings


def hotspots(grid, count=HOTSPOTS, spacing=2.0):
	found = []
	for k in np.argsort(grid, axis=None)[::-1]:
		i, j = np.unravel_index(k, grid.shape)
		if grid[i, j] <= 0 or len(found) == count:
			break
		x, y = (j + 0.5) * CELL, (i + 0.5) * CELL
		if all(math.dist((x, y), (fx, fy)) >= spacing for fx, fy, _ in found):
			found.append((x, y, float(grid[i, j])))
	return found


def nearest_element(config, x, y):
	elements = [(r["id"], r["x"], r["y"]) for r in config["resources"]]
	for zone in config["walls"] + config.get("checkouts", []):
		elements.append((zone["id"], zone["x"] + zone["width"] / 2, zone["y"] + zone["height"] / 2))
	for door in config["doors"]:
		elements.append((door["name"], door["x"] + (door["width"] / 2 if door["wall"] in ("bottom", "top") else 0),
						 door["y"] + (door["width"] / 2 if door["wall"] in ("left", "right") else 0)))
	return min(elements, key=lambda e: math.dist((x, y), e[1:]))[0]


def map_figure(model, grid, title, label, colormap, log=False, marks=()):
	fig, ax = plt.subplots(figsize=(11, 9))
	draw_store(model.config, ax)
	width = model.config["store"]["width"]
	height = model.config["store"]["height"]
	shown = np.ma.masked_less_equal(grid, 0)
	norm = LogNorm(vmin=max(shown.min(), 1e-3), vmax=shown.max()) if log and shown.count() else None
	image = ax.imshow(shown, origin="lower", extent=(0, grid.shape[1] * CELL, 0, grid.shape[0] * CELL),
					  cmap=colormap, norm=norm, alpha=0.8, interpolation="nearest", zorder=0.8)
	ax.set_xlim(-1.5, width + 1.5)
	ax.set_ylim(-2.5, height + 1.5)
	for rank, (x, y, _) in enumerate(marks, start=1):
		ax.plot(x, y, "o", markersize=17, markerfacecolor="none", markeredgecolor=TEXT,
				markeredgewidth=1.8, zorder=11)
		ax.text(x + 0.55, y + 0.55, str(rank), fontsize=10, fontweight="bold", color=TEXT, zorder=11,
				bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9))
	ax.set_title(title, loc="left", fontsize=15, fontweight="bold", color=TEXT, pad=22)
	bar = fig.colorbar(image, ax=ax, shrink=0.6, pad=0.02)
	bar.set_label(label)
	b, p = model.behavior, model.parameters
	flow = model.config.get("client_flow") or {}
	ax.text(0, -0.2, f"model M1 (clients ignore each other) · {model.total_clients} clients"
					 + (f", one every {flow['interval']} s" if flow.get("interval") else "")
					 + f" · cells {CELL} m x {CELL} m · time step {model.time_step} s · "
					   f"radius {b['radius']} m · max speed {b['max_speed']} m/s · "
					   f"pick {b['pick_time']} s · payment {p['payment_base_time']} s "
					   f"+ {p['payment_time_per_item']} s per item",
			transform=ax.transAxes, fontsize=8, color="#6b7780")
	return fig


def main():
	parser = argparse.ArgumentParser(description="Maps where the trajectories cross (model M1).")
	parser.add_argument("config", nargs="?", default="configs/reference.json",
						help="path to the config (default: configs/reference.json)")
	parser.add_argument("--output", default="outputs/passage_zones.png",
						help="base name of the images (default: outputs/passage_zones.png)")
	parser.add_argument("--clients", type=int, help="simulate only the first clients")
	args = parser.parse_args()

	model = StoreModel(args.config, max_clients=args.clients).simulate()
	passages, crossings, overlap, kinds, pairs = passage_maps(model, samples(model))

	print(f"{model.total_clients} clients, {len(model.exited_clients)} left in {model.current_time:.1f} s")
	print(f"pairs of clients that overlap at least once: {len(pairs)}")
	print(f"overlap duration: {sum(kinds.values()):.1f} pair.s")
	for kind, duration in kinds.items():
		print(f"  {kind}: {duration:.1f} pair.s ({duration / max(sum(kinds.values()), 1e-9):.0%})")
	print("main overlap zones:")
	overlap_spots = hotspots(overlap)
	for rank, (x, y, value) in enumerate(overlap_spots, start=1):
		print(f"  {rank}. ({x:.2f}, {y:.2f}) near {nearest_element(model.config, x, y)}: {value:.1f} pair.s")
	print("main crossing zones:")
	crossing_spots = hotspots(crossings)
	for rank, (x, y, value) in enumerate(crossing_spots, start=1):
		print(f"  {rank}. ({x:.2f}, {y:.2f}) near {nearest_element(model.config, x, y)}: "
			  f"{value:.0f} crossing pairs")

	figures = {
		"_passages": map_figure(model, passages, "Passages per cell",
								"clients passing through the cell", "YlGnBu"),
		"_crossings": map_figure(model, crossings, "Where trajectories cross",
								 f"pairs of passages crossing at more than {CROSSING_ANGLE:g}°",
								 "magma_r", log=True, marks=crossing_spots),
		"_overlaps": map_figure(model, overlap, "Where clients would touch",
								"time two clients overlap (pair.s)", "Reds", log=True,
								marks=overlap_spots),
	}
	output = Path(args.output)
	output.parent.mkdir(parents=True, exist_ok=True)
	for suffix, fig in figures.items():
		path = output.with_name(output.stem + suffix + output.suffix)
		fig.savefig(path, dpi=150, bbox_inches="tight")
		plt.close(fig)
		print(f"Image saved: {path}")


if __name__ == "__main__":
	main()
