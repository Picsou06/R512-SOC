from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Patch, Rectangle

from simulation.client import STATES
from simulation.config import DIRECTIONS, door_interval

FLOOR = "#f7f3ea"
TILE = "#e9e2d3"
WALL = "#2f3b45"
SHELF = "#c9a27a"
SHELF_EDGE = "#7a5638"
SHELF_LINE = "#e7cfb3"
CHECKOUT_OPEN = "#2b7bba"
CHECKOUT_CLOSED = "#b9c7d3"
CHECKOUT_BELT = "#1d3f5e"
GLASS = "#7fd0f0"
GLASS_EDGE = "#2a9fd6"
DOOR_COLORS = {"entrance": "#3aa66a", "exit": "#d9534f", "entrance_exit": GLASS}
DOOR_LABELS = {"entrance": "Entrance", "exit": "Exit", "entrance_exit": "Entrance / exit"}
RESOURCE = "#f2b134"
RESOURCE_EDGE = "#b5770c"
TEXT = "#2f3b45"
ONE_WAY = "#ffe082"
ONE_WAY_ARROW = "#b8860b"

STATE_COLORS = {
	"to_product": "#e4572e",
	"picking": "#f2b134",
	"to_checkout": "#6a4c93",
	"paying": "#2b7bba",
	"to_exit": "#3aa66a",
}


def draw_store(config, ax=None, report=True):
	if ax is None:
		_, ax = plt.subplots(figsize=(11, 9))

	width = config["store"]["width"]
	height = config["store"]["height"]

	ax.set_facecolor("white")
	ax.add_patch(Rectangle((0, 0), width, height, facecolor=FLOOR, edgecolor="none", zorder=0))
	for x in range(1, int(width)):
		ax.plot([x, x], [0, height], color=TILE, linewidth=0.6, zorder=0.5)
	for y in range(1, int(height)):
		ax.plot([0, width], [y, y], color=TILE, linewidth=0.6, zorder=0.5)

	for wall in config["walls"]:
		if wall["type"] == "shelf":
			_draw_shelf(ax, wall)
		elif wall["type"] == "wall":
			ax.add_patch(Rectangle((wall["x"], wall["y"]), wall["width"], wall["height"],
								   facecolor=WALL, edgecolor="none", zorder=4))
		else:
			_draw_one_way(ax, wall)

	for checkout in config.get("checkouts", []):
		_draw_checkout(ax, checkout)

	sides = {
		"bottom": ((0, 0), (1, 0), width),
		"top": ((0, height), (1, 0), width),
		"left": ((0, 0), (0, 1), height),
		"right": ((width, 0), (0, 1), height),
	}
	for side, (origin, direction, length) in sides.items():
		openings = [door_interval(d) for d in config["doors"] if d["wall"] == side]
		for start, end in _solid_segments(length, openings):
			_draw_segment(ax, origin, direction, start, end, color=WALL, linewidth=7,
						  solid_capstyle="projecting", zorder=5)

	for door in config["doors"]:
		_draw_door(ax, door, sides[door["wall"]])

	shelves = {w["id"]: w for w in config["walls"] if w["type"] == "shelf"}
	for resource in config["resources"]:
		_draw_resource(ax, resource, shelves[resource["shelf"]])

	margin = 1.5
	ax.set_xlim(-margin, width + margin)
	ax.set_ylim(-margin - 1, height + margin)
	ax.set_aspect("equal")
	if report:
		ax.set_xlabel("x (m)", color=TEXT)
		ax.set_ylabel("y (m)", color=TEXT)
		ax.tick_params(colors=TEXT, labelsize=9)
		for side in ("top", "right"):
			ax.spines[side].set_visible(False)
		for side in ("left", "bottom"):
			ax.spines[side].set_color("#b0b8bf")
	else:
		ax.set_xticks([])
		ax.set_yticks([])
		for spine in ax.spines.values():
			spine.set_visible(False)
		_draw_scale(ax, width)

	open_checkouts = sum(c["open"] for c in config.get("checkouts", []))
	if report:
		shelf_count = sum(w["type"] == "shelf" for w in config["walls"])
		ax.set_title(f"Store “{config['name']}”", loc="left", fontsize=15,
					 fontweight="bold", color=TEXT, pad=22)
		ax.text(0, 1.015, f"{width:g} m x {height:g} m  ·  {shelf_count} shelves  ·  "
						  f"{open_checkouts} open checkouts  ·  {len(config['doors'])} doors",
				transform=ax.transAxes, fontsize=10, color="#6b7780")

	handles = _legend(config)
	ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.08 if report else 0.0),
			  ncol=len(handles), frameon=False, fontsize=9, handlelength=1.6,
			  columnspacing=1.4, labelcolor=TEXT)
	return ax


def show_store(config, output=None):
	ax = draw_store(config)
	fig = ax.figure
	fig.tight_layout()
	if output:
		Path(output).parent.mkdir(parents=True, exist_ok=True)
		fig.savefig(output, dpi=150, bbox_inches="tight")
		plt.close(fig)
	else:
		plt.show()


def _draw_scale(ax, width):
	length = 5
	x0, y0 = width - length, -1.9
	ax.plot([x0, x0 + length], [y0, y0], color=TEXT, linewidth=2, solid_capstyle="butt")
	for x in (x0, x0 + length):
		ax.plot([x, x], [y0 - 0.2, y0 + 0.2], color=TEXT, linewidth=1.5)
	ax.text(x0 + length / 2, y0 + 0.45, f"{length} m", ha="center", va="bottom",
			fontsize=8.5, color=TEXT)


def _draw_shelf(ax, shelf):
	x, y, w, h = shelf["x"], shelf["y"], shelf["width"], shelf["height"]
	ax.add_patch(FancyBboxPatch((x + 0.12, y - 0.12), w, h, boxstyle="round,pad=0,rounding_size=0.15",
								facecolor="black", alpha=0.12, edgecolor="none", zorder=1))
	ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.15",
								facecolor=SHELF, edgecolor=SHELF_EDGE, linewidth=1.2, zorder=2))
	vertical = h >= w
	n = int((h if vertical else w) // 0.8)
	for i in range(1, n):
		if vertical:
			yy = y + i * h / n
			ax.plot([x + 0.12, x + w - 0.12], [yy, yy], color=SHELF_LINE, linewidth=1, zorder=2.5)
		else:
			xx = x + i * w / n
			ax.plot([xx, xx], [y + 0.12, y + h - 0.12], color=SHELF_LINE, linewidth=1, zorder=2.5)


def _draw_checkout(ax, checkout):
	x, y, w, h = checkout["x"], checkout["y"], checkout["width"], checkout["height"]
	color = CHECKOUT_OPEN if checkout["open"] else CHECKOUT_CLOSED
	ax.add_patch(FancyBboxPatch((x + 0.1, y - 0.1), w, h, boxstyle="round,pad=0,rounding_size=0.12",
								facecolor="black", alpha=0.12, edgecolor="none", zorder=1))
	ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.12",
								facecolor=color, edgecolor=CHECKOUT_BELT, linewidth=1.2, zorder=2))
	ax.add_patch(Rectangle((x + w * 0.3, y + 0.25), w * 0.4, h * 0.55,
						   facecolor=CHECKOUT_BELT if checkout["open"] else "#8a9aa8",
						   edgecolor="none", zorder=2.5))
	number = checkout["id"].split("_")[-1]
	ax.text(x + w / 2, y - 0.45, number, ha="center", va="center", fontsize=8,
			color=TEXT, fontweight="bold", zorder=3)


def _draw_door(ax, door, side):
	origin, direction, _ = side
	start, end = door_interval(door)
	color = DOOR_COLORS[door["type"]]
	_draw_segment(ax, origin, direction, start, end, color=color, linewidth=9,
				  solid_capstyle="butt", alpha=0.85, zorder=6)
	_draw_segment(ax, origin, direction, start, end, color="white", linewidth=1.5,
				  linestyle=(0, (2, 2)), zorder=7)
	for edge in (start, end):
		_draw_segment(ax, origin, direction, edge - 0.05, edge + 0.05, color=GLASS_EDGE
					  if door["type"] == "entrance_exit" else color, linewidth=11,
					  solid_capstyle="butt", zorder=7)

	(ox, oy), (dx, dy) = origin, direction
	middle = (start + end) / 2
	px, py = ox + dx * middle, oy + dy * middle
	offset = {"bottom": (0, -1.0), "top": (0, 1.0), "left": (-1.0, 0), "right": (1.0, 0)}
	ex, ey = offset[door["wall"]]
	ax.text(px + ex, py + ey, door.get("name", "").replace("_", " "), ha="center", va="center",
			fontsize=8, color=TEXT, rotation=90 if door["wall"] in ("left", "right") else 0,
			zorder=7)


def _draw_resource(ax, resource, shelf):
	x, y = resource["x"], resource["y"]
	x0, y0, x1, y1 = shelf["x"], shelf["y"], shelf["x"] + shelf["width"], shelf["y"] + shelf["height"]
	if abs(x - x0) < 1e-9 or abs(x - x1) < 1e-9:
		face = ([x, x], [max(y0, y - 0.6), min(y1, y + 0.6)])
	else:
		face = ([max(x0, x - 0.6), min(x1, x + 0.6)], [y, y])
	ax.plot(*face, color=RESOURCE, linewidth=6, solid_capstyle="round", zorder=3)
	ax.add_patch(Circle((x, y), 0.7, facecolor=RESOURCE, edgecolor="none", alpha=0.18, zorder=3))
	ax.plot(x, y, marker="*", markersize=15, color=RESOURCE, markeredgecolor=RESOURCE_EDGE,
			markeredgewidth=1, linestyle="none", zorder=4)

	text_position = ((x0 + x1) / 2, y1 + 1.3)
	ax.annotate(f"{resource['id'].replace('_', ' ')} · stock {resource['stock']}",
				(x, y), xytext=text_position, textcoords="data", ha="center", va="bottom",
				fontsize=8.5, color=TEXT, zorder=8,
				bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=RESOURCE,
						  linewidth=1),
				arrowprops=dict(arrowstyle="-", color=RESOURCE_EDGE, linewidth=1,
								shrinkA=0, shrinkB=6))


def _draw_one_way(ax, zone):
	ax.add_patch(Rectangle((zone["x"], zone["y"]), zone["width"], zone["height"],
						   facecolor=ONE_WAY, edgecolor="none", alpha=0.5, zorder=1))
	sx, sy = DIRECTIONS[zone["direction"]]
	cx, cy = zone["x"] + zone["width"] / 2, zone["y"] + zone["height"] / 2
	ax.annotate("", xy=(cx + sx * 0.5, cy + sy * 0.5), xytext=(cx - sx * 0.5, cy - sy * 0.5),
				arrowprops=dict(arrowstyle="-|>", color=ONE_WAY_ARROW, linewidth=2), zorder=2)


def _solid_segments(length, openings):
	segments = []
	position = 0.0
	for start, end in sorted(openings):
		if start > position:
			segments.append((position, start))
		position = max(position, end)
	if position < length:
		segments.append((position, length))
	return segments


def _draw_segment(ax, origin, direction, start, end, **style):
	(ox, oy), (dx, dy) = origin, direction
	ax.plot([ox + dx * start, ox + dx * end], [oy + dy * start, oy + dy * end], **style)


def _legend(config):
	handles = [
		Line2D([], [], color=WALL, linewidth=5, label="Wall"),
		Patch(facecolor=SHELF, edgecolor=SHELF_EDGE, label="Shelf"),
	]
	checkouts = config.get("checkouts", [])
	if any(c["open"] for c in checkouts):
		handles.append(Patch(facecolor=CHECKOUT_OPEN, edgecolor=CHECKOUT_BELT, label="Open checkout"))
	if any(not c["open"] for c in checkouts):
		handles.append(Patch(facecolor=CHECKOUT_CLOSED, edgecolor=CHECKOUT_BELT, label="Closed checkout"))
	if any(w["type"] == "one_way" for w in config["walls"]):
		handles.append(Patch(facecolor=ONE_WAY, edgecolor=ONE_WAY_ARROW, label="One way"))
	door_types = {d["type"] for d in config["doors"]}
	for door_type in DOOR_COLORS:
		if door_type in door_types:
			handles.append(Line2D([], [], color=DOOR_COLORS[door_type], linewidth=6,
								  label=DOOR_LABELS[door_type]))
	if config["resources"]:
		handles.append(Line2D([], [], marker="*", markersize=13, color=RESOURCE,
							  markeredgecolor=RESOURCE_EDGE, linestyle="none", label="Resource"))
	return handles


def trajectory_figure(model):
	fig, ax = plt.subplots(figsize=(11, 9))
	draw_store(model.config, ax)
	for client in model.clients:
		trace = np.array(client.trajectory)
		points = trace[:, 1:3].reshape(-1, 1, 2)
		segments = np.concatenate([points[:-1], points[1:]], axis=1)
		lines = LineCollection(segments, cmap="viridis", linewidth=3, zorder=9,
							   norm=plt.Normalize(0, model.behavior["max_speed"]))
		lines.set_array(trace[1:, 3])
		ax.add_collection(lines)
		for time, state in client.log if len(model.clients) <= 5 else []:
			if state in ("picking", "paying"):
				i = int(np.argmin(np.abs(trace[:, 0] - time)))
				ax.plot(trace[i, 1], trace[i, 2], "o", color="white", markeredgecolor=TEXT,
						markersize=7, zorder=10)
				ax.annotate(f"t = {time:.1f} s", (trace[i, 1], trace[i, 2]), xytext=(-10, 0),
							textcoords="offset points", ha="right", va="center", fontsize=8,
							color=TEXT, zorder=10,
							bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none",
									  alpha=0.85))
	bar = fig.colorbar(lines, ax=ax, shrink=0.6, pad=0.02)
	bar.set_label("speed (m/s)")
	b, p = model.behavior, model.parameters
	ax.text(0, -0.2, f"time step {model.time_step} s · radius {b['radius']} m · "
					 f"max speed {b['max_speed']} m/s · acceleration {b['acceleration']} m/s² · "
					 f"braking {b['deceleration']} m/s² · pick {b['pick_time']} s · "
					 f"payment {p['payment_base_time']} s + {p['payment_time_per_item']} s per item",
			transform=ax.transAxes, fontsize=8, color="#6b7780")
	return fig


def speed_figure(model):
	fig, ax = plt.subplots(figsize=(10, 4))
	for client in model.clients[:1]:
		trace = np.array(client.trajectory)
		ax.plot(trace[:, 0], trace[:, 3], color=TEXT, linewidth=1.5, label=client.identifier)
		log = client.log + [(trace[-1, 0], "end")]
		for (start, state), (end, _) in zip(log[1:], log[2:]):
			if state in STATE_COLORS:
				ax.axvspan(start, end, color=STATE_COLORS[state], alpha=0.15, linewidth=0)
				ax.text((start + end) / 2, model.behavior["max_speed"] * 1.08,
						STATES[state], ha="center", fontsize=8, color=STATE_COLORS[state])
	ax.set_xlabel("time (s)")
	ax.set_ylabel("speed (m/s)")
	ax.set_ylim(0, model.behavior["max_speed"] * 1.2)
	ax.set_xlim(left=0)
	for side in ("top", "right"):
		ax.spines[side].set_visible(False)
	ax.set_title(f"Speed of {model.clients[0].identifier} over time (time step {model.time_step} s)",
				 loc="left", fontsize=11, color=TEXT)
	fig.tight_layout()
	return fig
