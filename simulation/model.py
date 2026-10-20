import math

import mesa
from mesa.experimental.continuous_space import ContinuousSpace

from simulation.client import Client
from simulation.config import (DIRECTIONS, ENTRANCE_TYPES, EXIT_TYPES, load_config, obstacles_of,
							   one_way_zones, rectangle)
from simulation.geometry import Obstacles

OFFSET = 0.05
PRODUCT_SPREAD = 0.4
SEED = 1


class StoreModel(mesa.Model):
	def __init__(self, config_path="configs/reference.json", rng=SEED):
		super().__init__(rng=rng)
		self.config = load_config(config_path)
		self.behavior = self.config["client_behavior"]
		self.parameters = self.config["parameters"]
		self.time_step = self.parameters["time_step"]
		self.current_time = 0.0

		width = self.config["store"]["width"]
		height = self.config["store"]["height"]
		self.space = ContinuousSpace([[0, width], [0, height]], torus=False, random=self.random)

		zones = [zone for _, zone in obstacles_of(self.config)]
		directions = [(rectangle(z), DIRECTIONS[z["direction"]]) for z in one_way_zones(self.config)]
		self.obstacles = Obstacles(zones, width, height, self.behavior["radius"],
								   self.parameters["ball_radius"], directions)

		self.stocks = {r["id"]: r["stock"] for r in self.config["resources"]}
		self.load = {c["id"]: 0 for c in self.config.get("checkouts", []) if c["open"]}
		self.clients = []
		self.pending = self._arrivals()
		self.total_clients = len(self.pending)
		self._admit()

	def _arrivals(self):
		arrivals = [(d.get("arrival", 0.0), d) for d in self.config["clients"]]
		flow = self.config.get("client_flow")
		if flow:
			entrances = flow.get("doors") or [d["name"] for d in self.config["doors"]
											  if d["type"] in ENTRANCE_TYPES]
			taken = {d["id"] for d in self.config["clients"]}
			number = 0
			for k in range(flow["count"]):
				number += 1
				while f"client_{number}" in taken:
					number += 1
				description = {"id": f"client_{number}", "door": entrances[k % len(entrances)],
							   "products": list(flow["products"])}
				arrivals.append((flow.get("start", 0.0) + k * flow["interval"], description))
		arrivals.sort(key=lambda a: a[0])
		return arrivals

	def _admit(self):
		while self.pending and self.pending[0][0] <= self.current_time + 1e-9:
			_, description = self.pending.pop(0)
			self.clients.append(self._create_client(description))

	def _create_client(self, description):
		doors = {d["name"]: d for d in self.config["doors"]}
		resources = {r["id"]: r for r in self.config["resources"]}
		shelves = {w["id"]: w for w in self.config["walls"] if w["type"] == "shelf"}

		start = self._door_point(doors[description["door"]], random_offset=True)
		steps = []
		for product_id in self._draw_products(description["products"]):
			resource = resources[product_id]
			point = self._product_point(resource, shelves[resource["shelf"]])
			steps.append({"state": "to_product", "route": [point]})
			steps.append({"state": "picking", "duration": self.behavior["pick_time"],
						  "product": product_id})
		steps.append({"state": "to_checkout"})
		steps.append({"state": "paying"})
		steps.append({"state": "to_exit"})
		return Client(self, description["id"], start, steps)

	def _draw_products(self, products):
		return [self.random.choice(p) if isinstance(p, list) else p for p in products]

	def take(self, product_id):
		if self.stocks[product_id] <= 0:
			return False
		self.stocks[product_id] -= 1
		return True

	def payment_duration(self, items):
		return self.parameters["payment_base_time"] + self.parameters["payment_time_per_item"] * items

	def _door_point(self, door, random_offset=False):
		d = self.behavior["radius"] + OFFSET
		width = self.config["store"]["width"]
		height = self.config["store"]["height"]
		middle = door["width"] / 2
		if random_offset:
			spread = max(0.0, middle - self.behavior["radius"] - 0.1)
			middle += self.random.uniform(-spread, spread)
		return {
			"bottom": (door["x"] + middle, d),
			"top": (door["x"] + middle, height - d),
			"left": (d, door["y"] + middle),
			"right": (width - d, door["y"] + middle),
		}[door["wall"]]

	def _product_point(self, resource, shelf):
		x, y = resource["x"], resource["y"]
		d = self.behavior["radius"] + self.obstacles.thickness + OFFSET
		spread = PRODUCT_SPREAD
		if abs(x - shelf["x"]) < 1e-9 or abs(x - (shelf["x"] + shelf["width"])) < 1e-9:
			y = min(max(y + self.random.uniform(-spread, spread), shelf["y"]), shelf["y"] + shelf["height"])
			return (x - d, y) if abs(x - shelf["x"]) < 1e-9 else (x + d, y)
		x = min(max(x + self.random.uniform(-spread, spread), shelf["x"]), shelf["x"] + shelf["width"])
		return (x, y - d) if abs(y - shelf["y"]) < 1e-9 else (x, y + d)

	def _checkout_point(self, checkout):
		return (checkout["x"] - self.parameters["checkout_distance"],
				checkout["y"] + checkout["height"] / 2)

	def _exits(self):
		return [d for d in self.config["doors"] if d["type"] in EXIT_TYPES]

	def choose_checkout(self, start):
		penalty = self.payment_duration(1) * self.behavior["max_speed"]
		best = None
		for checkout in self.config.get("checkouts", []):
			if not checkout["open"]:
				continue
			point = self._checkout_point(checkout)
			there = math.dist(start, point)
			for door in self._exits():
				back = math.dist(point, self._door_point(door))
				cost = there + back + penalty * self.load[checkout["id"]]
				if best is None or cost < best[0]:
					best = (cost, checkout["id"], point)
		if best is None:
			raise ValueError("no open checkout")
		_, checkout_id, point = best
		self.load[checkout_id] += 1
		lane = self._lane_at(point)
		return checkout_id, (self._lane_route(lane)[:1] if lane else []) + [point]

	def release_checkout(self, checkout_id):
		self.load[checkout_id] -= 1

	def exit_route(self, start):
		door = min(self._exits(), key=lambda d: math.dist(start, self._door_point(d)))
		door_point = self._door_point(door, random_offset=True)
		lanes = one_way_zones(self.config)
		if not lanes or self._lane_at(start):
			return [door_point]
		lane = min(lanes, key=lambda z: math.dist(start, self._lane_route(z)[0])
				   + math.dist(self._lane_route(z)[1], door_point))
		return self._lane_route(lane) + [door_point]

	def _lane_at(self, point):
		for zone in one_way_zones(self.config):
			x0, y0, x1, y1 = rectangle(zone)
			if x0 <= point[0] <= x1 and y0 <= point[1] <= y1:
				return zone
		return None

	def _lane_route(self, zone):
		sx, sy = DIRECTIONS[zone["direction"]]
		center = (zone["x"] + zone["width"] / 2, zone["y"] + zone["height"] / 2)
		reach = abs(sx) * zone["width"] / 2 + abs(sy) * zone["height"] / 2 + self.behavior["radius"] + OFFSET
		return [(center[0] - sx * reach, center[1] - sy * reach), center]

	@property
	def present_clients(self):
		return [c for c in self.clients if c.state != "exited"]

	@property
	def exited_clients(self):
		return [c for c in self.clients if c.state == "exited"]

	def step(self):
		for client in self.present_clients:
			client.step()
		self.current_time = round(self.current_time + self.time_step, 10)
		self._admit()
		if not self.pending and not self.present_clients:
			self.running = False

	def simulate(self, max_duration=3600.0):
		while self.running and self.current_time < max_duration:
			self.step()
		return self
