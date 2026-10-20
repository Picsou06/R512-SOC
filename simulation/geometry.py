import math

import numpy as np


def balls_of_rectangle(zone, ball_radius):
	x0, y0 = zone["x"], zone["y"]
	step = ball_radius * math.sqrt(2)
	nx = max(1, math.ceil(zone["width"] / step))
	ny = max(1, math.ceil(zone["height"] / step))
	lx, ly = zone["width"] / nx, zone["height"] / ny
	centers = [(x0 + (i + 0.5) * lx, y0 + (j + 0.5) * ly) for i in range(nx) for j in range(ny)]
	return centers, ball_radius - min(lx, ly) / 2


class Obstacles:

	def __init__(self, zones, width, height, client_radius, ball_radius, one_way_zones=()):
		fillings = [balls_of_rectangle(z, ball_radius) for z in zones]
		self.balls = np.array([c for centers, _ in fillings for c in centers]).reshape(-1, 2)
		self.ball_radius = ball_radius
		self.thickness = max((overhang for _, overhang in fillings), default=0.0)
		self.min_distance = client_radius + ball_radius
		self.client_radius = client_radius
		self.width, self.height = width, height
		self.one_way_zones = list(one_way_zones)

	def push_out(self, position, iterations=10, tolerance=0.01):
		p = np.array(position, dtype=float)
		if len(self.balls):
			for _ in range(iterations):
				offsets = p - self.balls
				distances = np.hypot(offsets[:, 0], offsets[:, 1])
				j = int(np.argmin(distances))
				if distances[j] >= self.min_distance:
					break
				p = self.balls[j] + offsets[j] / max(distances[j], 1e-12) * self.min_distance
		r = self.client_radius
		p = np.clip(p, [r, r], [self.width - r, self.height - r])
		return p, self._normal(p, tolerance)

	def _normal(self, p, tolerance):
		r = self.client_radius
		normal = np.zeros(2)
		for gap, direction in ((p[0] - r, (1, 0)), (self.width - r - p[0], (-1, 0)),
							   (p[1] - r, (0, 1)), (self.height - r - p[1], (0, -1))):
			if gap < tolerance:
				normal += direction
		if len(self.balls):
			offsets = p - self.balls
			distances = np.hypot(offsets[:, 0], offsets[:, 1])
			near = distances < self.min_distance + tolerance
			normal += (offsets[near] / distances[near, None]).sum(axis=0)
		norm = np.linalg.norm(normal)
		return normal / norm if norm > 1e-12 else None

	def distance(self, point):
		x, y = point
		r = self.client_radius
		distances = [x - r, self.width - r - x, y - r, self.height - r - y]
		if len(self.balls):
			offsets = self.balls - np.asarray(point, dtype=float)
			distances.append(float(np.hypot(offsets[:, 0], offsets[:, 1]).min()) - self.min_distance)
		return min(distances)

	def respect_direction(self, old, new):
		move = new - old
		for (x0, y0, x1, y1), (sx, sy) in self.one_way_zones:
			if x0 < new[0] < x1 and y0 < new[1] < y1:
				wrong_way = move[0] * sx + move[1] * sy
				if wrong_way < 0:
					move = move - wrong_way * np.array([sx, sy])
		return old + move
