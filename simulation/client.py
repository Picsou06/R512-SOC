import math

import numpy as np
from mesa.experimental.continuous_space import ContinuousSpaceAgent

RELEASE_DISTANCE = 0.05
ARRIVAL_DISTANCE = 0.1
MIN_TURN_SPEED = 0.3

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
		self.field = None
		self.wait = 0.0
		self.items = 0
		self.checkout = None
		self.normal = None
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
			self.checkout, field = self.model.choose_checkout(self.position)
			step = {**step, "field": field}
		elif step["state"] == "paying":
			step = {**step, "duration": self.model.payment_duration(self.items)}
		elif step["state"] == "to_exit":
			step = {**step, "field": self.model.exit_field()}
		self.state = step["state"]
		self.log.append((self.model.current_time, self.state))
		if "field" in step:
			self.field = step["field"]
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
		remaining = self.field.value(self.position)
		if remaining <= ARRIVAL_DISTANCE:
			self.speed = 0.0
			return True

		# 1-3. direction voulue -grad(d), cap tourne au plus de a_lat / v * dt
		wanted = self.field.direction(self.position)
		gap = 0.0 if wanted is None else _signed_angle(self.heading, wanted)
		max_turn = b["lateral_acceleration"] / max(self.speed, MIN_TURN_SPEED) * dt
		self.heading = _rotate(self.heading, max(-max_turn, min(max_turn, gap)))

		# 4. vitesse : freinage avant la cible, ralentissement si le cap est mal aligne
		wanted_speed = min(b["max_speed"], math.sqrt(2 * b["deceleration"] * remaining), remaining / dt)
		wanted_speed *= max(0.0, math.cos(gap))
		if wanted_speed > self.speed:
			self.speed = min(wanted_speed, self.speed + b["acceleration"] * dt)
		else:
			self.speed = max(wanted_speed, self.speed - b["deceleration"] * dt)

		# 5-6. deplacement suivant le cap, puis on repousse hors des boules
		wanted_position = obstacles.respect_direction(self.position,
													  self.position + self.heading * self.speed * dt)
		new, self.normal = obstacles.push_out(wanted_position)
		if self.normal is not None:
			self.speed = min(self.speed, float(np.linalg.norm(new - self.position)) / dt)
			if self.released:
				self.contact_count += 1
				self.released = False
		elif obstacles.distance(new) > RELEASE_DISTANCE:
			self.released = True
		self.position = new
		return False


def _signed_angle(u, v):
	return math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])


def _rotate(u, angle):
	c, s = math.cos(angle), math.sin(angle)
	return np.array([c * u[0] - s * u[1], s * u[0] + c * u[1]])
