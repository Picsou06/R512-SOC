import math

import numpy as np
from mesa.experimental.continuous_space import ContinuousSpaceAgent

RELEASE_DISTANCE = 0.05
WAYPOINT_REACHED = 0.15

STATES = {
	"to_product": "Going to product",
	"picking": "Picking product",
	"to_checkout": "Going to checkout",
	"paying": "Paying",
	"to_exit": "Leaving",
	"exited": "Left",
}


class Client(ContinuousSpaceAgent):

	def __init__(self, model, identifier, start, steps):
		super().__init__(model.space, model)
		self.identifier = identifier
		self.position = np.array(start, dtype=float)
		self.heading = np.array([0.0, 1.0])
		self.speed = 0.0
		self.steps = list(steps)
		self.state = None
		self.route = []
		self.wait = 0.0
		self.items = 0
		self.checkout = None
		self.normal = None
		self.side = None
		self.released = True
		self.contact_count = 0
		self.trajectory = [(model.current_time, *self.position, 0.0)]
		self.log = [(model.current_time, "entered")]
		self._next_step()

	@property
	def in_contact(self):
		return self.normal is not None

	@property
	def label(self):
		return STATES[self.state]

	def _next_step(self):
		if not self.steps:
			self.state = "exited"
			self.log.append((self.model.current_time, "exited"))
			return
		step = self.steps.pop(0)
		if step["state"] == "picking" and not self.model.take(step["product"]):
			self.log.append((self.model.current_time, "out_of_stock"))
			return self._next_step()
		if step["state"] == "picking":
			self.items += 1
		if step["state"] == "to_checkout":
			if not self.items:
				self.steps = [s for s in self.steps if s["state"] != "paying"]
				return self._next_step()
			self.checkout, route = self.model.choose_checkout(self.position)
			step = {**step, "route": route}
		elif step["state"] == "paying":
			step = {**step, "duration": self.model.payment_duration(self.items)}
		elif step["state"] == "to_exit":
			step = {**step, "route": self.model.exit_route(self.position)}
		self.state = step["state"]
		self.log.append((self.model.current_time, self.state))
		if "route" in step:
			self.route = [np.array(point, dtype=float) for point in step["route"]]
		else:
			self.wait = step["duration"]

	def step(self):
		dt = self.model.time_step
		if self.state == "exited":
			return
		if self.state in ("picking", "paying"):
			self.wait -= dt
			if self.wait <= 1e-9:
				if self.state == "paying":
					self.model.release_checkout(self.checkout)
				self._next_step()
		elif self._move(dt):
			self._next_step()
		self.trajectory.append((self.model.current_time + dt, *self.position, self.speed))

	def _move(self, dt):
		b = self.model.behavior
		obstacles = self.model.obstacles
		target = self.route[0]
		distance = math.dist(self.position, target)
		if len(self.route) > 1 and distance <= WAYPOINT_REACHED:
			self.route.pop(0)
			return False
		if distance <= 0.01:
			self.position = obstacles.respect_direction(self.position, target)
			self.speed = 0.0
			return True
		remaining = distance + sum(math.dist(a, b) for a, b in zip(self.route, self.route[1:]))

		wanted_speed = min(b["max_speed"], math.sqrt(2 * b["deceleration"] * remaining), remaining / dt)
		if wanted_speed > self.speed:
			self.speed = min(wanted_speed, self.speed + b["acceleration"] * dt)
		else:
			self.speed = max(wanted_speed, self.speed - b["deceleration"] * dt)

		direction = (target - self.position) / distance
		if self.normal is not None and np.dot(direction, self.normal) < 0:
			tangent = np.array([-self.normal[1], self.normal[0]])
			if self.side is None:
				self.side = 1.0 if np.dot(direction, tangent) >= 0 else -1.0
			direction = self.side * tangent
		step_length = self.speed * dt if len(self.route) > 1 else min(self.speed * dt, distance)
		wanted = obstacles.respect_direction(self.position, self.position + direction * step_length)
		new, self.normal = obstacles.push_out(wanted)
		if self.normal is not None and self.released:
			self.contact_count += 1
			self.released = False
		elif obstacles.distance(new) > RELEASE_DISTANCE:
			self.released = True
			self.side = None
		move = new - self.position
		if np.linalg.norm(move) > 1e-9:
			self.heading = move / np.linalg.norm(move)
		self.position = new
		return False
