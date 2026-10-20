import copy
import json
from pathlib import Path

WALL_SIDES = ("bottom", "top", "left", "right")
DOOR_TYPES = ("entrance", "exit", "entrance_exit")
ENTRANCE_TYPES = ("entrance", "entrance_exit")
EXIT_TYPES = ("exit", "entrance_exit")
WALL_TYPES = ("shelf", "wall", "one_way")
DIRECTIONS = {"down": (0.0, -1.0), "up": (0.0, 1.0), "left": (-1.0, 0.0), "right": (1.0, 0.0)}
BEHAVIOR = ("radius", "max_speed", "acceleration", "deceleration", "pick_time")
PARAMETERS = ("time_step", "ball_radius", "checkout_distance", "payment_base_time",
			  "payment_time_per_item")


def load_config(path):
	with open(path, encoding="utf-8") as f:
		config = json.load(f)
	validate_config(config)
	return config


def save_config(config, path):
	validate_config(config)
	path = Path(path)
	path.parent.mkdir(parents=True, exist_ok=True)
	with open(path, "w", encoding="utf-8") as f:
		json.dump(config, f, indent="\t", ensure_ascii=False)
		f.write("\n")


def duplicate_config(source, destination, overrides=None):
	config = load_config(source)
	if overrides:
		config = _merge(config, overrides)
	save_config(config, destination)
	return config


def _merge(base, overrides):
	result = copy.deepcopy(base)
	for key, value in overrides.items():
		if isinstance(value, dict) and isinstance(result.get(key), dict):
			result[key] = _merge(result[key], value)
		else:
			result[key] = copy.deepcopy(value)
	return result


def validate_config(config):
	for key in ("name", "parameters", "client_behavior", "store", "doors", "walls",
				"resources", "clients"):
		if key not in config:
			raise ValueError(f"missing key: {key}")

	width = config["store"]["width"]
	height = config["store"]["height"]
	if width <= 0 or height <= 0:
		raise ValueError("the store must have a positive width and height")

	for wall in config["walls"]:
		if wall.get("type") not in WALL_TYPES:
			raise ValueError(f"wall {wall.get('id')}: unknown type {wall.get('type')!r} "
							 f"(expected: {', '.join(WALL_TYPES)})")
		if wall["type"] == "one_way" and wall.get("direction") not in DIRECTIONS:
			raise ValueError(f"wall {wall['id']}: unknown direction {wall.get('direction')!r} "
							 f"(expected: {', '.join(DIRECTIONS)})")

	obstacles = obstacles_of(config)
	for name, zone in obstacles:
		x0, y0, x1, y1 = rectangle(zone)
		if zone["width"] <= 0 or zone["height"] <= 0:
			raise ValueError(f"{name}: width and height must be positive")
		if x0 < 0 or y0 < 0 or x1 > width or y1 > height:
			raise ValueError(f"{name}: outside the store")
	for i, (name_a, a) in enumerate(obstacles):
		for name_b, b in obstacles[i + 1:]:
			if _overlap(rectangle(a), rectangle(b)):
				raise ValueError(f"{name_a} and {name_b} overlap")

	for key in ("checkouts", "walls"):
		ids = [z["id"] for z in config.get(key, [])]
		if len(ids) != len(set(ids)):
			raise ValueError(f"{key} identifiers must be unique")

	for zone in one_way_zones(config):
		x0, y0, x1, y1 = rectangle(zone)
		if zone["width"] <= 0 or zone["height"] <= 0:
			raise ValueError(f"one_way {zone['id']}: width and height must be positive")
		if x0 < 0 or y0 < 0 or x1 > width or y1 > height:
			raise ValueError(f"one_way {zone['id']}: outside the store")
		for name, obstacle in obstacles:
			if _overlap(rectangle(zone), rectangle(obstacle)):
				raise ValueError(f"one_way {zone['id']}: overlaps {name}")

	if not config["doors"]:
		raise ValueError("the store must have at least one door")
	for door in config["doors"]:
		name = door.get("name", "?")
		if door["type"] not in DOOR_TYPES:
			raise ValueError(f"door {name}: unknown type {door['type']!r}")
		if door["wall"] not in WALL_SIDES:
			raise ValueError(f"door {name}: unknown wall {door['wall']!r}")
		start, end = door_interval(door)
		wall_length = width if door["wall"] in ("bottom", "top") else height
		if door["width"] <= 0 or start < 0 or end > wall_length:
			raise ValueError(f"door {name}: does not fit on the {door['wall']} wall")
		x, y = door["x"], door["y"]
		on_wall = {
			"bottom": y == 0,
			"top": y == height,
			"left": x == 0,
			"right": x == width,
		}[door["wall"]]
		if not on_wall:
			raise ValueError(f"door {name}: ({x}, {y}) is not on the {door['wall']} wall")

	shelves = {w["id"]: w for w in config["walls"] if w["type"] == "shelf"}

	product_ids = [r["id"] for r in config["resources"]]
	if len(product_ids) != len(set(product_ids)):
		raise ValueError("resource identifiers must be unique")
	for resource in config["resources"]:
		x, y = resource["x"], resource["y"]
		if not (0 <= x <= width and 0 <= y <= height):
			raise ValueError(f"resource {resource['id']}: outside the store")
		if resource["stock"] < 0:
			raise ValueError(f"resource {resource['id']}: negative stock")
		shelf = shelves.get(resource.get("shelf"))
		if shelf is None:
			raise ValueError(f"resource {resource['id']}: unknown shelf {resource.get('shelf')!r}")
		if not on_edge(shelf, x, y):
			raise ValueError(f"resource {resource['id']}: ({x}, {y}) is not on the edge "
							 f"of shelf {shelf['id']}")

	for key in PARAMETERS:
		if config["parameters"].get(key, -1) < 0:
			raise ValueError(f"parameters: {key} missing or negative")
	for key in ("time_step", "ball_radius"):
		if config["parameters"][key] == 0:
			raise ValueError(f"parameters: {key} must be strictly positive")
	if not isinstance(config.get("display", {}).get("collision_boxes", False), bool):
		raise ValueError("display: collision_boxes must be true or false")
	for key in BEHAVIOR:
		if config["client_behavior"].get(key, -1) < 0:
			raise ValueError(f"client_behavior: {key} missing or negative")

	doors = {d["name"]: d for d in config["doors"]}
	client_ids = [c["id"] for c in config["clients"]]
	if len(client_ids) != len(set(client_ids)):
		raise ValueError("client identifiers must be unique")
	for client in config["clients"]:
		door = doors.get(client["door"])
		if door is None or door["type"] not in ENTRANCE_TYPES:
			raise ValueError(f"client {client['id']}: {client['door']!r} is not an entrance")
		_check_products(client["products"], product_ids, f"client {client['id']}")
		if client.get("arrival", 0.0) < 0:
			raise ValueError(f"client {client['id']}: negative arrival")
	flow = config.get("client_flow")
	if flow:
		if not isinstance(flow.get("count"), int) or flow["count"] < 0:
			raise ValueError("client_flow: count must be a positive integer")
		if flow.get("interval", -1) < 0 or flow.get("start", 0.0) < 0:
			raise ValueError("client_flow: interval and start must be positive")
		for name in flow.get("doors", []):
			door = doors.get(name)
			if door is None or door["type"] not in ENTRANCE_TYPES:
				raise ValueError(f"client_flow: {name!r} is not an entrance")
		if not any(d["type"] in ENTRANCE_TYPES for d in config["doors"]):
			raise ValueError("client_flow: the store has no entrance")
		if "products" not in flow:
			raise ValueError("client_flow: products missing")
		_check_products(flow["products"], product_ids, "client_flow")
	if (config["clients"] or flow) and not any(d["type"] in EXIT_TYPES for d in config["doors"]):
		raise ValueError("the store must have at least one exit")


def _check_products(products, product_ids, name):
	if not isinstance(products, list):
		raise ValueError(f"{name}: products must be a list")
	for product in products:
		choices = product if isinstance(product, list) else [product]
		if not choices:
			raise ValueError(f"{name}: empty choice list in products")
		for product_id in choices:
			if not isinstance(product_id, str):
				raise ValueError(f"{name}: {product_id!r} is not a product identifier")
			if product_id not in product_ids:
				raise ValueError(f"{name}: unknown product {product_id!r}")


def on_edge(zone, x, y, tolerance=1e-9):
	x0, y0, x1, y1 = rectangle(zone)
	inside = x0 - tolerance <= x <= x1 + tolerance and y0 - tolerance <= y <= y1 + tolerance
	on_a_side = min(abs(x - x0), abs(x - x1), abs(y - y0), abs(y - y1)) <= tolerance
	return inside and on_a_side


def obstacles_of(config):
	obstacles = [(f"{w['type']} {w['id']}", w) for w in config["walls"] if w["type"] != "one_way"]
	obstacles += [(f"checkout {c['id']}", c) for c in config.get("checkouts", [])]
	return obstacles


def one_way_zones(config):
	return [w for w in config["walls"] if w["type"] == "one_way"]


def _overlap(a, b, tolerance=1e-9):
	return (a[0] < b[2] - tolerance and b[0] < a[2] - tolerance
			and a[1] < b[3] - tolerance and b[1] < a[3] - tolerance)


def rectangle(zone):
	return zone["x"], zone["y"], zone["x"] + zone["width"], zone["y"] + zone["height"]


def door_interval(door):
	start = door["x"] if door["wall"] in ("bottom", "top") else door["y"]
	return start, start + door["width"]
