"""Indicator curves for the report (sub-step 4.4): over time for one simulation, or as a
function of a parameter for several simulations. Every figure names its axes with their
units, has a legend and states the parameters of the simulation that produced it."""
import matplotlib.pyplot as plt
import numpy as np

from simulation.model import LOCAL_RADIUS

TEXT = "#2f3b45"
MUTED = "#6b7780"
COLORS = {"main": "#2b7bba", "second": "#e4572e", "third": "#3aa66a"}
WINDOW = 10.0


def moving_rate(times, counts, window):
	"""Events per second over the last `window` seconds, at each time."""
	times = np.asarray(times, dtype=float)
	total = np.concatenate([[0.0], np.cumsum(counts)])
	start = np.searchsorted(times, times - window, side="right")
	span = np.minimum(window, times - times[0] + (times[1] - times[0] if len(times) > 1 else 1.0))
	return (total[1:] - total[start]) / span


def moving_mean(values, times, window):
	"""Mean of `values` over the last `window` seconds, at each time."""
	times = np.asarray(times, dtype=float)
	total = np.concatenate([[0.0], np.cumsum(values)])
	start = np.searchsorted(times, times - window, side="right")
	index = np.arange(1, len(times) + 1)
	return (total[index] - total[start]) / (index - start)


def moving_max(values, times, window):
	"""Maximum of `values` over the last `window` seconds, at each time."""
	times = np.asarray(times, dtype=float)
	start = np.searchsorted(times, times - window, side="right")
	return np.array([values[a:b + 1].max() for b, a in enumerate(start)])


def parameters_text(model):
	b, p = model.behavior, model.parameters
	flow = model.config.get("client_flow")
	arrivals = (f"{model.total_clients} clients, one every {flow['interval']:g} s" if flow
				else f"{model.total_clients} clients")
	stocks = ", ".join(f"{r['id'].lower().replace('_', ' ')} {r['stock']}"
					   for r in model.config["resources"])
	checkouts = sum(c["open"] for c in model.config.get("checkouts", []))
	return (f"config “{model.config['name']}” · {arrivals} · {checkouts} open checkouts · "
			f"stock: {stocks}\n"
			f"time step {model.time_step:g} s · radius {b['radius']:g} m · "
			f"max speed {b['max_speed']:g} m/s · pick {b['pick_time']:g} s · "
			f"payment {p['payment_base_time']:g} s + {p['payment_time_per_item']:g} s per item · "
			f"free area {model.free_area():.0f} m²")


def _style(ax, title, ylabel):
	ax.set_title(title, loc="left", fontsize=10.5, color=TEXT)
	ax.set_xlabel("time (s)", color=TEXT)
	ax.set_ylabel(ylabel, color=TEXT)
	ax.set_xlim(left=0)
	ax.set_ylim(bottom=0)
	ax.grid(color="#e3e7ea", linewidth=0.6)
	ax.tick_params(colors=TEXT, labelsize=8.5)
	for side in ("top", "right"):
		ax.spines[side].set_visible(False)
	ax.legend(frameon=False, fontsize=8.5, loc="upper right")


def indicator_figure(model, window=WINDOW):
	"""Curves over time of one simulation: clients present, density, contact frequency and
	intensity, throughput at the exit. Rates are averaged over the last `window` seconds."""
	s = {key: np.asarray(values, dtype=float) for key, values in model.series.items()}
	if not len(s["time"]):
		raise ValueError("the model has no recorded time step: simulate it first")
	t = s["time"]
	fig = plt.figure(figsize=(12, 10))
	grid = fig.add_gridspec(3, 2)
	present, density = fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])
	frequency, intensity = fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])
	throughput = fig.add_subplot(grid[2, :])

	present.plot(t, s["present"], color=COLORS["main"], linewidth=1.5, label="in the store")
	present.plot(t, s["queuing"], color=COLORS["second"], linewidth=1.2,
				 label="in a checkout line (waiting or paying)")
	_style(present, "Clients present", "clients")

	density.plot(t, moving_max(s["local_density"], t, window), color=COLORS["second"],
				 linewidth=1.2, label=f"highest local density, within {LOCAL_RADIUS:g} m "
									  f"of a client (max over {window:g} s)")
	density.plot(t, s["density"], color=COLORS["main"], linewidth=1.5,
				 label="mean density: clients present / free area")
	_style(density, "Density", "density (clients/m²)")

	frequency.plot(t, moving_rate(t, s["new_contacts"], window), color=COLORS["main"],
				   linewidth=1.5, label=f"new client contacts per s (mean over {window:g} s)")
	frequency.plot(t, moving_mean(s["contact_pairs"], t, window), color=COLORS["second"],
				   linewidth=1.2, label=f"pairs in contact (mean over {window:g} s)")
	_style(frequency, "Contact frequency", "contacts/s, or pairs")

	# Mean over the contacts of the window, not over the time steps (most have none).
	pairs = moving_rate(t, s["overlapping_pairs"], window)
	total = moving_rate(t, s["total_intensity"], window)
	with np.errstate(invalid="ignore", divide="ignore"):
		mean = np.where(pairs > 0, total / pairs, np.nan)
	intensity.plot(t, 100 * moving_max(s["max_intensity"], t, window), color=COLORS["second"],
				   linewidth=1.2, label=f"maximum over the last {window:g} s")
	intensity.plot(t, 100 * mean, color=COLORS["main"], linewidth=1.5,
				   label=f"mean over the contacts of the last {window:g} s")
	_style(intensity, "Contact intensity (overlap before correction)", "intensity (cm)")
	intensity.legend(frameon=False, fontsize=8.5, loc="lower center")

	exits = np.diff(np.concatenate([[0.0], s["exited"]]))
	throughput.plot(t, 60 * moving_rate(t, exits, 6 * window), color=COLORS["main"],
					linewidth=1.5, label=f"clients leaving per min (mean over {6 * window:g} s)")
	_style(throughput, "Throughput at the exit", "throughput (clients/min)")

	fig.suptitle(f"Indicators over time, config “{model.config['name']}”", x=0.01,
				 ha="left", fontsize=14, fontweight="bold", color=TEXT)
	fig.text(0.01, 0.005, parameters_text(model), fontsize=8, color=MUTED, va="bottom")
	fig.tight_layout(rect=(0, 0.04, 1, 0.97))
	return fig


def parameter_figure(parameter, unit, values, samples, indicator, indicator_unit,
					 reference=None, parameters=""):
	"""An indicator as a function of a parameter, over several simulations per value (one
	per seed): mean and standard deviation, with each simulation as a dot.

	`samples[k]` lists the indicator of each simulation run with `values[k]`. `reference`,
	when given, is the parameter value of the reference config, marked on the axis."""
	fig, ax = plt.subplots(figsize=(8, 5))
	values = np.asarray(values, dtype=float)
	means = np.array([np.mean(v) for v in samples])
	stds = np.array([np.std(v) for v in samples])
	for x, ys in zip(values, samples):
		ax.plot([x] * len(ys), ys, "o", color=COLORS["main"], alpha=0.3, markersize=4,
				markeredgewidth=0)
	ax.errorbar(values, means, yerr=stds, color=COLORS["main"], linewidth=1.5, capsize=4,
				marker="o", label=f"mean ± standard deviation ({len(samples[0])} seeds)")
	if reference is not None:
		ax.axvline(reference, color=COLORS["second"], linestyle="--", linewidth=1,
				   label="reference config")
	ax.set_xlabel(f"{parameter} ({unit})", color=TEXT)
	ax.set_ylabel(f"{indicator} ({indicator_unit})", color=TEXT)
	ax.set_title(f"{indicator.capitalize()} as a function of {parameter}", loc="left",
				 fontsize=12, fontweight="bold", color=TEXT)
	ax.set_ylim(bottom=0)
	ax.grid(color="#e3e7ea", linewidth=0.6)
	for side in ("top", "right"):
		ax.spines[side].set_visible(False)
	ax.legend(frameon=False, fontsize=9)
	if parameters:
		fig.text(0.01, 0.005, parameters, fontsize=8, color=MUTED, va="bottom")
	fig.tight_layout(rect=(0, 0.05 if parameters else 0, 1, 1))
	return fig
