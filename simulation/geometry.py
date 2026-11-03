import heapq
import math

import numpy as np

GRID_STEP = 0.2


def _moves():
	moves = []
	for di in range(-2, 3):
		for dj in range(-2, 3):
			if (di, dj) == (0, 0) or math.gcd(abs(di), abs(dj)) != 1:
				continue
			if abs(di) + abs(dj) == 1:
				crossed = []
			elif abs(di) == abs(dj):
				crossed = [(di, 0), (0, dj)]
			else:
				crossed = [(int(di / 2), int(dj / 2)), (di - int(di / 2), dj - int(dj / 2))]
			moves.append((di, dj, math.hypot(di, dj), crossed))
	return moves


MOVES = _moves()


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
		self.free, self.direction = self._grid()

	def _grid(self):
		nx = math.ceil(self.width / GRID_STEP)
		ny = math.ceil(self.height / GRID_STEP)
		xs = (np.arange(nx) + 0.5) * GRID_STEP
		ys = (np.arange(ny) + 0.5) * GRID_STEP
		x, y = np.meshgrid(xs, ys)
		r = self.client_radius
		free = (x >= r) & (x <= self.width - r) & (y >= r) & (y <= self.height - r)
		for cx, cy in self.balls:
			free &= np.hypot(x - cx, y - cy) >= self.min_distance
		direction = np.zeros((ny, nx, 2))
		for (x0, y0, x1, y1), sense in self.one_way_zones:
			direction[(x > x0) & (x < x1) & (y > y0) & (y < y1)] = sense
		return free, direction

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


def distance_field(free, direction, goals):
	ny, nx = free.shape
	free = free.ravel().tolist()
	sense = direction.reshape(-1, 2).tolist()
	d = [math.inf] * (nx * ny)
	queue = []
	for (i, j), value in goals.items():
		d[i * nx + j] = value
		heapq.heappush(queue, (value, i, j))
	while queue:
		dist, i, j = heapq.heappop(queue)
		k = i * nx + j
		if dist > d[k]:
			continue
		for di, dj, length, crossed in MOVES:
			a, b = i + di, j + dj
			if not (0 <= a < ny and 0 <= b < nx) or not free[a * nx + b]:
				continue
			if any(not free[(i + ci) * nx + j + cj] for ci, cj in crossed):
				continue
			if any(-dj * sense[c][0] - di * sense[c][1] < -1e-9 for c in (k, a * nx + b)):
				continue
			nd = dist + length * GRID_STEP
			if nd < d[a * nx + b]:
				d[a * nx + b] = nd
				heapq.heappush(queue, (nd, a, b))
	return np.array(d).reshape(ny, nx)


def _gradient(d, axis):
	forward = np.full(d.shape, np.nan)
	backward = np.full(d.shape, np.nan)
	with np.errstate(invalid="ignore"):
		difference = np.diff(d, axis=axis) / GRID_STEP
	head = [slice(None)] * 2
	tail = [slice(None)] * 2
	head[axis], tail[axis] = slice(None, -1), slice(1, None)
	forward[tuple(head)] = difference
	backward[tuple(tail)] = difference
	valid_f, valid_b = np.isfinite(forward), np.isfinite(backward)
	count = valid_f.astype(int) + valid_b
	total = np.where(valid_f, forward, 0.0) + np.where(valid_b, backward, 0.0)
	with np.errstate(invalid="ignore", divide="ignore"):
		gradient = np.where(count > 0, total / count, np.nan)
	gradient[~np.isfinite(d)] = np.nan
	return gradient


class DistanceField:

	def __init__(self, obstacles, goal_points):
		self.free = obstacles.free
		inside = [p for p in goal_points if self.free[self.cell(p)]]
		goals = {self._free_cell_near(point): 0.0 for point in inside or goal_points}
		self.d = distance_field(self.free, obstacles.direction, goals)
		self.gx = _gradient(self.d, axis=1)
		self.gy = _gradient(self.d, axis=0)

	def _center(self, cell):
		return (cell[1] + 0.5) * GRID_STEP, (cell[0] + 0.5) * GRID_STEP

	def cell(self, point):
		ny, nx = self.free.shape
		return (min(max(int(point[1] / GRID_STEP), 0), ny - 1),
				min(max(int(point[0] / GRID_STEP), 0), nx - 1))

	def _free_cell_near(self, point):
		i, j = self.cell(point)
		if self.free[i, j]:
			return i, j
		ii, jj = np.nonzero(self.free)
		centers_x, centers_y = (jj + 0.5) * GRID_STEP, (ii + 0.5) * GRID_STEP
		k = int(np.argmin(np.hypot(centers_x - point[0], centers_y - point[1])))
		return int(ii[k]), int(jj[k])

	def _interpolate(self, grid, point):
		ny, nx = grid.shape
		u, v = point[0] / GRID_STEP - 0.5, point[1] / GRID_STEP - 0.5
		j0, i0 = math.floor(u), math.floor(v)
		fu, fv = u - j0, v - i0
		total = weight = 0.0
		for i, j, w in ((i0, j0, (1 - fu) * (1 - fv)), (i0, j0 + 1, fu * (1 - fv)),
						(i0 + 1, j0, (1 - fu) * fv), (i0 + 1, j0 + 1, fu * fv)):
			if w > 0 and 0 <= i < ny and 0 <= j < nx and np.isfinite(grid[i, j]):
				total += w * grid[i, j]
				weight += w
		return total / weight if weight > 0 else math.nan

	def _nearest_reached(self, point, reach=3):
		i0, j0 = self.cell(point)
		best = None
		for i in range(i0 - reach, i0 + reach + 1):
			for j in range(j0 - reach, j0 + reach + 1):
				if 0 <= i < self.d.shape[0] and 0 <= j < self.d.shape[1] and np.isfinite(self.d[i, j]):
					value = self.d[i, j] + math.dist(point, self._center((i, j)))
					if best is None or value < best[0]:
						best = (value, (i, j))
		return best

	def value(self, point):
		value = self._interpolate(self.d, point)
		if math.isnan(value):
			best = self._nearest_reached(point)
			return best[0] if best else math.inf
		return value

	def direction(self, point):
		gx, gy = self._interpolate(self.gx, point), self._interpolate(self.gy, point)
		gradient = np.array([0.0 if math.isnan(gx) else gx, 0.0 if math.isnan(gy) else gy])
		norm = float(np.linalg.norm(gradient))
		if norm > 1e-9:
			return -gradient / norm
		best = self._nearest_reached(point)
		if best is None:
			return None
		to_cell = np.array(self._center(best[1])) - np.asarray(point, dtype=float)
		norm = float(np.linalg.norm(to_cell))
		return to_cell / norm if norm > 1e-9 else None
