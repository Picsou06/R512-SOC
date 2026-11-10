import math
import os
import threading
import time
from pathlib import Path

import solara
import solara.lab
from mesa.visualization.utils import force_update, update_counter

from simulation.client import MIN_TURN_SPEED, STATES, signed_angle
from simulation.model import StoreModel
from simulation.visualization import STATE_COLORS
from simulation.web_view import (Frame, collision_boxes_svg, distance_focus_svg, distance_map_svg,
								 distance_window, hover_targets, store_svg, trajectories_svg, waves_svg)

DEFAULT_CONFIG = "configs/reference.json"
MANY_CLIENTS = 10
FRAME_PERIOD = 0.1
SPEEDS = {"x0.5": 0.5, "x1": 1.0, "x2": 2.0, "x5": 5.0}


def _pace(time_step, factor):
	period = max(FRAME_PERIOD, time_step / factor)
	return period, max(1, round(period * factor / time_step))


def _create_model(path, distance_mode=False):
	try:
		return StoreModel(path, max_clients=1 if distance_mode else None), None
	except (OSError, ValueError, KeyError, TypeError) as e:
		return None, f"{type(e).__name__}: {e}"


def _collision_boxes(model):
	return bool(model and model.config.get("display", {}).get("collision_boxes", False))


def _modification_time(path):
	try:
		return os.path.getmtime(path)
	except OSError:
		return None


def _config_files():
	return sorted(str(p).replace(os.sep, "/") for p in Path("configs").rglob("*.json"))


def _client_svg(client, frame, radius, transition_ms, full_label):
	v = solara.v
	x, y = frame.x(client.position[0]), frame.y(client.position[1])
	color = STATE_COLORS[client.state]
	heading_x, heading_y = client.heading * radius * 0.85
	if client.state in ("picking", "paying"):
		detail = f"{client.wait:.0f} s"
	else:
		detail = f"{client.speed:.1f} m/s"
	if full_label:
		detail = f"{client.label} · {detail}"
	children = [
		v.Html(tag="circle", attributes={"r": radius, "fill": color,
										 "stroke": "#ff1744" if client.in_contact else "white",
										 "stroke-width": 0.12 if client.in_contact else 0.07}),
		v.Html(tag="line", attributes={"x1": 0, "y1": 0, "x2": round(heading_x, 3),
									   "y2": round(-heading_y, 3), "stroke": "white",
									   "stroke-width": 0.09, "stroke-linecap": "round"}),
		v.Html(tag="text", attributes={"y": -radius - 0.3,
									   "font-size": 0.45 if full_label else 0.36,
									   "text-anchor": "middle", "fill": color,
									   "stroke": "white", "stroke-width": 0.12,
									   "paint-order": "stroke",
									   "font-family": "Roboto, Arial, sans-serif",
									   "font-weight": "bold"},
			   children=[detail]),
	]
	return v.Html(
		tag="g",
		style_=f"transform: translate({x}px, {y}px); pointer-events: none; "
			   f"transition: transform {transition_ms}ms linear",
		children=children,
	)


@solara.component
def HoverZone(name, tag, attributes, hovered):
	zone = solara.v.Html(tag=tag, attributes=attributes)
	solara.v.use_event(zone, "mouseenter", lambda *_: hovered.set(name))
	solara.v.use_event(zone, "mouseleave", lambda *_: hovered.set(None))
	return zone


def _followed(model, distance_mode):
	"""Client suivi par la carte des distances (le seul client, tant qu'il est dans le magasin)."""
	if not distance_mode or not model.present_clients:
		return None
	client = model.present_clients[0]
	return client if client.field is not None else None


@solara.component
def StoreView(model, transition_ms, collision_boxes, distance_mode):
	update_counter.get()
	frame = solara.use_memo(lambda: Frame(model.config), dependencies=[id(model)])
	hovered = solara.use_reactive(None)
	targets = solara.use_memo(lambda: hover_targets(model, frame), dependencies=[id(model)])
	waves = solara.use_memo(
		lambda: waves_svg(targets[hovered.value][2](), frame) if hovered.value in targets else "",
		dependencies=[id(model), hovered.value])
	followed = _followed(model, distance_mode)
	view_box = frame.view_box
	distances = ""
	if followed is not None:
		window = distance_window(frame, followed.position)
		view_box = " ".join(f"{v:.3f}" for v in window)
		distances = (distance_map_svg(followed.field, frame, window)
					 + distance_focus_svg(followed.field, frame, followed.position))
		transition_ms = 0
	stocks = tuple(sorted(model.stocks.items()))
	background = solara.use_memo(lambda: store_svg(model.config, model.stocks),
								 dependencies=[id(model), stocks])
	ratio = frame.view_width / frame.view_height
	layer = "position:absolute;inset:0;width:100%;height:100%"

	few = model.total_clients <= MANY_CLIENTS
	radius = model.behavior["radius"]
	moving = [_client_svg(client, frame, radius, transition_ms, few).key(client.identifier)
			  for client in model.present_clients]
	zones = [HoverZone(name, tag, attributes, hovered).key(name)
			 for name, (tag, attributes, _) in targets.items()]

	solara.v.Html(
		tag="div",
		style_=f"position:relative;width:100%;max-width:calc((100vh - 140px) * {ratio:.4f});"
			   f"aspect-ratio:{ratio:.4f}",
		children=[
			solara.HTML(tag="div", style=layer, unsafe_innerHTML=(
				f'<svg viewBox="{view_box}" style="width:100%;height:100%;display:block">'
				f"{background}</svg>")),
			solara.HTML(tag="div", style=layer, unsafe_innerHTML=(
				f'<svg viewBox="{view_box}" style="width:100%;height:100%;display:block">'
				f"{waves}</svg>")),
			solara.HTML(tag="div", style=layer, unsafe_innerHTML=(
				f'<svg viewBox="{view_box}" style="width:100%;height:100%;display:block">'
				f"{distances}"
				f"{trajectories_svg(model, frame) if few else ''}"
				f"{collision_boxes_svg(model.obstacles, frame) if collision_boxes else ''}</svg>")),
			solara.v.Html(tag="svg", attributes={"viewBox": view_box},
						  style_=layer + (";opacity:0.55" if followed is not None else ""),
						  children=zones + moving),
		],
	)


def _distance_details(model, client):
	lines = [f"<b>Cost to goal d:</b> {client.field.value(client.position):.2f}"]
	wanted = client.field.direction(client.position)
	heading = client.heading
	if wanted is not None:
		gap = signed_angle(heading, wanted)
		lines.append(f"<b>Wanted direction −∇d:</b> "
					 f"{math.degrees(math.atan2(wanted[1], wanted[0])):.0f}°")
		lines.append(f"<b>Heading θ:</b> {math.degrees(math.atan2(heading[1], heading[0])):.0f}° "
					 f"(gap α {math.degrees(gap):.0f}°)")
	omega = model.behavior["lateral_acceleration"] / max(client.speed, MIN_TURN_SPEED)
	lines.append(f"<b>Max turn rate:</b> {math.degrees(omega):.0f}°/s at {client.speed:.2f} m/s")
	lines.append("<span style='opacity:0.7'>solid square: client cell · dashed: lowest "
				 "neighbour · blue arrow: −∇d</span>")
	return lines


@solara.component
def Information(model, distance_mode):
	update_counter.get()
	lines = [f"<b>Time:</b> {model.current_time:.1f} s"]
	followed = _followed(model, distance_mode)
	if followed is not None:
		lines += _distance_details(model, followed)
	if model.total_clients > MANY_CLIENTS:
		lines += _summary(model)
		solara.HTML(tag="div", unsafe_innerHTML="<br>".join(lines),
					style="line-height:1.8;font-size:14px")
		return
	for client in model.clients:
		if client.state == "exited":
			lines.append(f"<b>{client.identifier}:</b> left at {client.log[-1][0]:.1f} s")
		else:
			lines.append(f"<b>{client.identifier}:</b> {client.label.lower()}, "
						 f"{client.speed:.1f} m/s")
		lines.append(f"&nbsp;&nbsp;obstacle contacts: {client.contact_count}")
	solara.HTML(tag="div", unsafe_innerHTML="<br>".join(lines),
				style="line-height:1.8;font-size:14px")


def _summary(model):
	present = model.present_clients
	exited = model.exited_clients
	lines = [f"<b>Clients entered:</b> {len(model.clients)} / {model.total_clients}",
			 f"<b>In the store:</b> {len(present)}"]
	for state in STATE_COLORS:
		count = sum(1 for c in present if c.state == state)
		if count:
			lines.append(f"&nbsp;&nbsp;<span style='color:{STATE_COLORS[state]}'>&#9679;</span> "
						 f"{STATES[state].lower()}: {count}")
	lines.append(f"<b>Left:</b> {len(exited)}")
	if exited:
		durations = [c.log[-1][0] - c.log[0][0] for c in exited]
		with_items = sum(1 for c in exited if c.items)
		lines.append(f"&nbsp;&nbsp;with purchases: {with_items}, without product: {len(exited) - with_items}")
		lines.append(f"&nbsp;&nbsp;time in store: mean {sum(durations) / len(durations):.1f} s, "
					 f"max {max(durations):.1f} s")
	stocks = ", ".join(f"{name.replace('_', ' ')} {n}" for name, n in model.stocks.items())
	lines.append(f"<b>Stock:</b> {stocks}")
	lines.append(f"<b>Obstacle contacts:</b> {sum(c.contact_count for c in model.clients)}")
	return lines


@solara.component
def Page():
	initial, initial_error = solara.use_memo(
		lambda: _create_model(DEFAULT_CONFIG), [])
	model = solara.use_reactive(initial)
	path = solara.use_reactive(DEFAULT_CONFIG)
	collision_boxes = solara.use_reactive(_collision_boxes(initial))
	distance_mode = solara.use_reactive(False)
	playing = solara.use_reactive(False)
	speed = solara.use_reactive("x1")
	error = solara.use_reactive(initial_error)

	def dark_theme():
		solara.lab.theme.dark = True

	solara.use_effect(dark_theme, [])

	def load():
		new, problem = _create_model(path.value, distance_mode.value)
		error.set(problem)
		if new is not None:
			model.set(new)
			collision_boxes.set(_collision_boxes(new))

	def watch_config():
		stop = threading.Event()

		def loop():
			last = _modification_time(path.value)
			while not stop.wait(1.0):
				current = _modification_time(path.value)
				if current != last:
					last = current
					load()

		threading.Thread(target=loop, daemon=True).start()
		return stop.set

	solara.use_effect(watch_config, [path.value])

	def play():
		if not playing.value or model.value is None:
			return None
		stop = threading.Event()
		current = model.value
		factor = SPEEDS[speed.value]
		period, steps_per_frame = _pace(current.time_step, factor)

		def loop():
			next_frame = time.perf_counter()
			while not stop.is_set():
				for _ in range(steps_per_frame):
					if current.running:
						current.step()
				force_update()
				if not current.running:
					playing.set(False)
					return
				next_frame += period
				delay = next_frame - time.perf_counter()
				if delay > 0:
					stop.wait(delay)
				else:
					next_frame = time.perf_counter()

		threading.Thread(target=loop, daemon=True).start()
		return stop.set

	solara.use_effect(play, [playing.value, speed.value, id(model.value)])

	def one_step():
		if model.value is not None and model.value.running:
			model.value.step()
			force_update()

	def restart():
		playing.set(False)
		load()

	def switch_distance_mode(enabled):
		distance_mode.set(enabled)
		restart()

	finished = model.value is None or not model.value.running
	time_step = model.value.time_step if model.value is not None else FRAME_PERIOD
	transition_ms = round(_pace(time_step, SPEEDS[speed.value])[0] * 1000)

	solara.Title("Store simulation")
	solara.Style("""
		.v-checkbox {
			--v-input-control-height: 40px;
		}
		.v-checkbox .v-input__details {
			display: none !important;
		}
	""")
	with solara.Columns([1, 3]):
		with solara.Column():
			with solara.Card("Controls"):
				with solara.Row():
					solara.Button("Pause" if playing.value else "Play",
								  icon_name="mdi-pause" if playing.value else "mdi-play",
								  on_click=lambda: playing.set(not playing.value),
								  disabled=finished, color="primary")
					solara.Button("Step", icon_name="mdi-step-forward", on_click=one_step,
								  disabled=playing.value or finished)
					solara.Button("Restart", icon_name="mdi-restart", on_click=restart)
				solara.Text("Playback speed")
				solara.ToggleButtonsSingle(value=speed, values=list(SPEEDS))
			with solara.Card("Configuration"):
				solara.Select("File", values=_config_files(), value=path, dense=True)
				solara.Checkbox(label="Collision boxes", value=collision_boxes)
				solara.Checkbox(label="Distance map (1 client)", value=distance_mode.value,
								on_value=switch_distance_mode)
				with solara.CardActions():
					solara.Button("Load", on_click=restart, text=True)
			with solara.Card("Information"):
				if model.value is not None:
					Information(model.value, distance_mode.value)
		with solara.Column():
			if error.value and model.value is None:
				solara.Error(f"Invalid configuration: {error.value}. Fix the file, "
							 f"the page reloads by itself.")
			elif error.value:
				solara.Error(f"Invalid configuration, the last valid store is still shown. "
							 f"{error.value}")
			if model.value is not None:
				StoreView(model.value, transition_ms, collision_boxes.value, distance_mode.value)
