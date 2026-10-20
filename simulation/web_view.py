import math
from html import escape

from simulation.client import STATES
from simulation.config import DIRECTIONS, door_interval
from simulation.visualization import (
	CHECKOUT_BELT, CHECKOUT_CLOSED, CHECKOUT_OPEN, DOOR_COLORS, DOOR_LABELS, FLOOR, GLASS_EDGE,
	ONE_WAY, ONE_WAY_ARROW, RESOURCE, RESOURCE_EDGE, SHELF, SHELF_EDGE, SHELF_LINE, STATE_COLORS,
	TEXT, TILE, WALL, _solid_segments,
)

MARGIN = 1.5
BOTTOM_MARGIN = 3.0


class Frame:

	def __init__(self, config):
		self.width = config["store"]["width"]
		self.height = config["store"]["height"]
		self.view_width = self.width + 2 * MARGIN
		self.view_height = self.height + MARGIN + BOTTOM_MARGIN

	def x(self, x):
		return round(x + MARGIN, 3)

	def y(self, y):
		return round(self.height + MARGIN - y, 3)

	@property
	def view_box(self):
		return f"0 0 {self.view_width:g} {self.view_height:g}"


def store_svg(config, stocks=None):
	f = Frame(config)
	w, h = f.width, f.height
	parts = [
		"<defs>"
		'<pattern id="tiles" width="1" height="1" patternUnits="userSpaceOnUse">'
		f'<path d="M 1 0 L 0 0 0 1" fill="none" stroke="{TILE}" stroke-width="0.04"/>'
		"</pattern>"
		'<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">'
		'<feDropShadow dx="0.1" dy="0.1" stdDeviation="0.08" flood-opacity="0.25"/>'
		"</filter>"
		"</defs>",
		f'<rect x="{f.x(0)}" y="{f.y(h)}" width="{w}" height="{h}" fill="{FLOOR}"/>',
		f'<rect x="{f.x(0)}" y="{f.y(h)}" width="{w}" height="{h}" fill="url(#tiles)"/>',
	]

	for zone in config["walls"]:
		if zone["type"] == "wall":
			parts.append(_rect(f, zone, WALL, None, 0.05))
		elif zone["type"] == "one_way":
			parts.append(_one_way_svg(f, zone))

	for shelf in (z for z in config["walls"] if z["type"] == "shelf"):
		parts.append(_rect(f, shelf, SHELF, SHELF_EDGE, 0.15))
		vertical = shelf["height"] >= shelf["width"]
		length = shelf["height"] if vertical else shelf["width"]
		n = int(length // 0.8)
		for i in range(1, n):
			if vertical:
				yy = shelf["y"] + i * shelf["height"] / n
				parts.append(_line(f, shelf["x"] + 0.12, yy, shelf["x"] + shelf["width"] - 0.12, yy,
								   SHELF_LINE, 0.05))
			else:
				xx = shelf["x"] + i * shelf["width"] / n
				parts.append(_line(f, xx, shelf["y"] + 0.12, xx, shelf["y"] + shelf["height"] - 0.12,
								   SHELF_LINE, 0.05))

	for checkout in config.get("checkouts", []):
		color = CHECKOUT_OPEN if checkout["open"] else CHECKOUT_CLOSED
		parts.append(_rect(f, checkout, color, CHECKOUT_BELT, 0.12))
		belt = {"x": checkout["x"] + checkout["width"] * 0.3, "y": checkout["y"] + 0.25,
				"width": checkout["width"] * 0.4, "height": checkout["height"] * 0.55}
		parts.append(_rect(f, belt, CHECKOUT_BELT if checkout["open"] else "#8a9aa8", None, 0,
						   shadow=False))
		parts.append(_text(f, checkout["x"] + checkout["width"] / 2, checkout["y"] - 0.45,
						   checkout["id"].split("_")[-1], 0.42, bold=True))

	sides = {
		"bottom": ((0, 0), (1, 0), w),
		"top": ((0, h), (1, 0), w),
		"left": ((0, 0), (0, 1), h),
		"right": ((w, 0), (0, 1), h),
	}
	for side, ((ox, oy), (dx, dy), length) in sides.items():
		openings = [door_interval(d) for d in config["doors"] if d["wall"] == side]
		for start, end in _solid_segments(length, openings):
			parts.append(_line(f, ox + dx * start, oy + dy * start, ox + dx * end, oy + dy * end,
							   WALL, 0.35, cap="square"))

	for door in config["doors"]:
		(ox, oy), (dx, dy), _ = sides[door["wall"]]
		start, end = door_interval(door)
		a = (ox + dx * start, oy + dy * start)
		b = (ox + dx * end, oy + dy * end)
		color = DOOR_COLORS[door["type"]]
		parts.append(_line(f, *a, *b, color, 0.4, opacity=0.9))
		parts.append(_line(f, *a, *b, "white", 0.07, dashes="0.2 0.2"))
		for bx, by in (a, b):
			parts.append(f'<circle cx="{f.x(bx)}" cy="{f.y(by)}" r="0.12" fill="{GLASS_EDGE}"/>')
		middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
		offset = {"bottom": (0, -1.0), "top": (0, 1.0), "left": (-1.0, 0), "right": (1.0, 0)}
		ex, ey = offset[door["wall"]]
		parts.append(_text(f, middle[0] + ex, middle[1] + ey,
						   door.get("name", "").replace("_", " "), 0.42, color="currentColor"))

	shelves = {z["id"]: z for z in config["walls"] if z["type"] == "shelf"}
	for resource in config["resources"]:
		stock = resource["stock"] if stocks is None else stocks[resource["id"]]
		parts.append(_resource_svg(f, resource, shelves[resource["shelf"]], stock))

	x0 = w - 5
	y0 = -1.9
	parts.append(_line(f, x0, y0, w, y0, "currentColor", 0.08))
	for xx in (x0, w):
		parts.append(_line(f, xx, y0 - 0.2, xx, y0 + 0.2, "currentColor", 0.06))
	parts.append(_text(f, x0 + 2.5, y0 + 0.5, "5 m", 0.42, color="currentColor"))

	return "".join(parts)


def trajectories_svg(model, frame):
	parts = []
	for client in model.clients:
		if len(client.trajectory) < 2:
			continue
		points = client.trajectory[::2] + client.trajectory[-1:]
		trace = "M " + " L ".join(f"{frame.x(p[1])} {frame.y(p[2])}" for p in points)
		color = STATE_COLORS.get(client.state, "#888888")
		parts.append(f'<path d="{trace}" fill="none" stroke="{color}" stroke-width="0.1" '
					 f'stroke-opacity="0.7" stroke-linejoin="round" stroke-dasharray="0.25 0.15"/>')
	return "".join(parts)


def collision_boxes_svg(obstacles, frame):
	style = ('fill="none" stroke="#ff1744" stroke-width="0.04" stroke-dasharray="0.12 0.08" '
			 'opacity="0.9"')
	return "".join(f'<circle cx="{frame.x(cx)}" cy="{frame.y(cy)}" '
				   f'r="{obstacles.ball_radius}" {style}/>'
				   for cx, cy in obstacles.balls)


def legend(config):
	items = [("Shelf", f"background:{SHELF};border:1px solid {SHELF_EDGE}")]
	types = {z["type"] for z in config["walls"]}
	if "wall" in types:
		items.append(("Wall", f"background:{WALL}"))
	if "one_way" in types:
		items.append(("One way", f"background:{ONE_WAY};border:1px solid {ONE_WAY_ARROW}"))
	checkouts = config.get("checkouts", [])
	if any(c["open"] for c in checkouts):
		items.append(("Open checkout", f"background:{CHECKOUT_OPEN}"))
	if any(not c["open"] for c in checkouts):
		items.append(("Closed checkout", f"background:{CHECKOUT_CLOSED}"))
	for door_type in DOOR_COLORS:
		if any(d["type"] == door_type for d in config["doors"]):
			items.append((DOOR_LABELS[door_type], f"background:{DOOR_COLORS[door_type]};height:5px"))
	items.append(("Resource", f"background:{RESOURCE};border-radius:50%"))
	for state, color in STATE_COLORS.items():
		items.append((f"Client: {STATES[state].lower()}", f"background:{color};border-radius:50%"))
	return "".join(
		f'<span style="display:inline-flex;align-items:center;margin:0 10px 6px 0;'
		f'font-size:13px"><span style="display:inline-block;width:14px;height:12px;'
		f'margin-right:6px;{style}"></span>{escape(name)}</span>'
		for name, style in items
	)


def _one_way_svg(f, zone):
	sx, sy = DIRECTIONS[zone["direction"]]
	px, py = -sy, sx
	cx, cy = zone["x"] + zone["width"] / 2, zone["y"] + zone["height"] / 2
	tip = (cx + sx * 0.45, cy + sy * 0.45)
	base = (cx - sx * 0.25, cy - sy * 0.25)
	points = [tip, (base[0] + px * 0.3, base[1] + py * 0.3), (base[0] - px * 0.3, base[1] - py * 0.3)]
	arrow = " ".join(f"{f.x(x)},{f.y(y)}" for x, y in points)
	return (_rect(f, zone, ONE_WAY, None, 0.05, shadow=False).replace("/>", ' opacity="0.55"/>')
			+ f'<polygon points="{arrow}" fill="{ONE_WAY_ARROW}" opacity="0.9"/>')


def _resource_svg(f, resource, shelf, stock):
	x, y = resource["x"], resource["y"]
	x0, y0 = shelf["x"], shelf["y"]
	x1, y1 = x0 + shelf["width"], y0 + shelf["height"]
	if abs(x - x0) < 1e-9 or abs(x - x1) < 1e-9:
		face = (x, max(y0, y - 0.6), x, min(y1, y + 0.6))
	else:
		face = (max(x0, x - 0.6), y, min(x1, x + 0.6), y)
	label = f"{resource['id'].replace('_', ' ')} · stock {stock}"
	tx, ty = (x0 + x1) / 2, y1 + 1.6
	label_width = 0.24 * len(label) + 0.5
	return (
		_line(f, x, y, tx, ty - 0.35, RESOURCE_EDGE, 0.05)
		+ _line(f, *face, RESOURCE, 0.3)
		+ f'<circle cx="{f.x(x)}" cy="{f.y(y)}" r="0.7" fill="{RESOURCE}" opacity="0.2"/>'
		+ f'<polygon points="{_star(f.x(x), f.y(y), 0.42, 0.18)}" fill="{RESOURCE}" '
		  f'stroke="{RESOURCE_EDGE}" stroke-width="0.05"/>'
		+ f'<rect x="{f.x(tx - label_width / 2)}" y="{f.y(ty + 0.35)}" width="{label_width:.2f}" '
		  f'height="0.7" rx="0.15" fill="white" stroke="{RESOURCE}" stroke-width="0.05"/>'
		+ _text(f, tx, ty, label, 0.4)
	)


def _star(cx, cy, outer, inner):
	points = []
	for i in range(10):
		radius = outer if i % 2 == 0 else inner
		angle = -math.pi / 2 + i * math.pi / 5
		points.append(f"{cx + radius * math.cos(angle):.3f},{cy + radius * math.sin(angle):.3f}")
	return " ".join(points)


def _rect(f, zone, fill, edge, rounding, shadow=True):
	outline = f' stroke="{edge}" stroke-width="0.06"' if edge else ""
	effect = ' filter="url(#shadow)"' if shadow else ""
	return (f'<rect x="{f.x(zone["x"])}" y="{f.y(zone["y"] + zone["height"])}" '
			f'width="{zone["width"]}" height="{zone["height"]}" rx="{rounding}" '
			f'fill="{fill}"{outline}{effect}/>')


def _line(f, xa, ya, xb, yb, color, thickness, cap="round", dashes=None, opacity=1):
	extra = f' stroke-dasharray="{dashes}"' if dashes else ""
	return (f'<line x1="{f.x(xa)}" y1="{f.y(ya)}" x2="{f.x(xb)}" y2="{f.y(yb)}" stroke="{color}" '
			f'stroke-width="{thickness}" stroke-linecap="{cap}" opacity="{opacity}"{extra}/>')


def _text(f, x, y, content, size, bold=False, color=TEXT):
	weight = ' font-weight="bold"' if bold else ""
	return (f'<text x="{f.x(x)}" y="{f.y(y)}" font-size="{size}" fill="{color}" '
			f'text-anchor="middle" dominant-baseline="middle" '
			f'font-family="Roboto, Arial, sans-serif"{weight}>{escape(content)}</text>')
