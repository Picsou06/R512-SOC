import mesa
from mesa.experimental.continuous_space import ContinuousSpace

from simulation.client import Client
from simulation.config import (DIRECTIONS, ENTRANCE_TYPES, EXIT_TYPES, load_config, obstacles_of,
							   one_way_zones, rectangle)
from simulation.geometry import DistanceField, Obstacles

OFFSET = 0.05
PRODUCT_SPREAD = 0.4
GOAL_SAMPLING = 0.1
SEED = 1


class StoreModel(mesa.Model):
	def __init__(self, config_path="configs/reference.json", rng=SEED, max_clients=None):
		super().__init__(rng=rng)
		self.config = load_config(config_path)
		self.behavior = self.config["client_behavior"]
		self.parameters = self.config["parameters"]
		self.time_step = self.parameters["time_step"]
		self.current_time = 0.0
		self.max_clients = max_clients

		width = self.config["store"]["width"]
		height = self.config["store"]["height"]
		self.space = ContinuousSpace([[0, width], [0, height]], torus=False, random=self.random)

		zones = [zone for _, zone in obstacles_of(self.config)]
		directions = [(rectangle(z), DIRECTIONS[z["direction"]]) for z in one_way_zones(self.config)]
		self.obstacles = Obstacles(zones, width, height, self.behavior["radius"],
								   self.parameters["ball_radius"], directions)

		self.stocks = {r["id"]: r["stock"] for r in self.config["resources"]}
		self.load = {c["id"]: 0 for c in self.config.get("checkouts", []) if c["open"]}
		self.fields = {}
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
		return arrivals[:self.max_clients]

	def _admit(self):
		while self.pending and self.pending[0][0] <= self.current_time + 1e-9:
			_, description = self.pending.pop(0)
			self.clients.append(self._create_client(description))

	def _create_client(self, description):
		doors = {d["name"]: d for d in self.config["doors"]}
		resources = {r["id"]: r for r in self.config["resources"]}
		shelves = {w["id"]: w for w in self.config["walls"] if w["type"] == "shelf"}

		start = self._door_point(doors[description["door"]])
		steps = []
		for product_id in self._draw_products(description["products"]):
			resource = resources[product_id]
			field = self._field(("product", product_id),
								lambda: self._product_goal(resource, shelves[resource["shelf"]]))
			steps.append({"state": "to_product", "field": field})
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

	def _field(self, key, goal):
		if key not in self.fields:
			self.fields[key] = DistanceField(self.obstacles, goal())
		return self.fields[key]

	def _segment(self, a, b):
		n = max(1, round(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 / GOAL_SAMPLING))
		return [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n + 1)]

	def _door_goal(self, door):
		d = self.behavior["radius"] + OFFSET
		width = self.config["store"]["width"]
		height = self.config["store"]["height"]
		margin = min(self.behavior["radius"] + 0.1, door["width"] / 2)
		start, end = margin, door["width"] - margin
		return {
			"bottom": self._segment((door["x"] + start, d), (door["x"] + end, d)),
			"top": self._segment((door["x"] + start, height - d), (door["x"] + end, height - d)),
			"left": self._segment((d, door["y"] + start), (d, door["y"] + end)),
			"right": self._segment((width - d, door["y"] + start), (width - d, door["y"] + end)),
		}[door["wall"]]

	def _door_point(self, door):
		goal = self._door_goal(door)
		return goal[self.random.randrange(len(goal))]

	def _product_goal(self, resource, shelf):
		x, y = resource["x"], resource["y"]
		d = self.behavior["radius"] + self.obstacles.thickness + OFFSET
		if abs(x - shelf["x"]) < 1e-9 or abs(x - (shelf["x"] + shelf["width"])) < 1e-9:
			x = x - d if abs(x - shelf["x"]) < 1e-9 else x + d
			low = max(y - PRODUCT_SPREAD, shelf["y"])
			high = min(y + PRODUCT_SPREAD, shelf["y"] + shelf["height"])
			return self._segment((x, low), (x, high))
		y = y - d if abs(y - shelf["y"]) < 1e-9 else y + d
		low = max(x - PRODUCT_SPREAD, shelf["x"])
		high = min(x + PRODUCT_SPREAD, shelf["x"] + shelf["width"])
		return self._segment((low, y), (high, y))

	def _checkout_point(self, checkout):
		return (checkout["x"] - self.parameters["checkout_distance"],
				checkout["y"] + checkout["height"] / 2)

	def _exits(self):
		return [d for d in self.config["doors"] if d["type"] in EXIT_TYPES]

	def _checkout_field(self, checkout):
		x, y = self._checkout_point(checkout)
		start = (x - self.parameters["checkout_distance"], y)
		return self._field(("checkout", checkout["id"]),
						   lambda: self._segment(start, (checkout["x"], y)))

	def exit_field(self):
		return self._field(("exit",), lambda: [p for door in self._exits() for p in self._door_goal(door)])

	def choose_checkout(self, start):
		penalty = self.payment_duration(1) * self.behavior["max_speed"]
		best = None
		for checkout in self.config.get("checkouts", []):
			if not checkout["open"]:
				continue
			field = self._checkout_field(checkout)
			there = field.value(start)
			back = self.exit_field().value(self._checkout_point(checkout))
			cost = there + back + penalty * self.load[checkout["id"]]
			if best is None or cost < best[0]:
				best = (cost, checkout["id"], field)
		if best is None:
			raise ValueError("no open checkout")
		_, checkout_id, field = best
		self.load[checkout_id] += 1
		return checkout_id, field

	def release_checkout(self, checkout_id):
		self.load[checkout_id] -= 1

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
