"""Matplotlib visualization embedded in the Tkinter application."""

from __future__ import annotations

import tkinter as tk
from collections import defaultdict
from typing import Sequence

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from algorithms import ScheduleResult

ALGORITHM_COLORS = {
    "FCFS": "#2563eb",
    "SSTF": "#059669",
    "SCAN": "#d97706",
    "C-SCAN": "#7c3aed",
}


class DiskMovementPlot:
    def __init__(self, parent: tk.Misc) -> None:
        self.figure = Figure(figsize=(9.0, 5.2), dpi=100, facecolor="#ffffff")
        self.axes = self.figure.subplots(2, 2).flatten()
        self.figure.subplots_adjust(hspace=0.36, wspace=0.22, top=0.91, bottom=0.12)
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()
        self.clear()

    def clear(self) -> None:
        for axes in self.axes:
            axes.clear()
            axes.set_title("Run a simulation to view the head path", fontsize=9, color="#64748b")
            axes.set_xlabel("Traversal step", fontsize=8)
            axes.set_ylabel("Cylinder", fontsize=8)
            axes.grid(axis="y", color="#e2e8f0", linewidth=0.7)
        self.figure.suptitle("Disk-head movement", fontsize=13, fontweight="bold", color="#0f172a")
        self.canvas.draw_idle()

    def draw(
        self,
        results: Sequence[ScheduleResult],
        min_cylinder: int,
        max_cylinder: int,
        direction: str,
    ) -> None:
        for axes, result in zip(self.axes, results):
            axes.clear()
            color = ALGORITHM_COLORS[result.algorithm]
            positions = result.movement_sequence
            x_positions = list(range(len(positions)))

            axes.axhline(min_cylinder, color="#94a3b8", linestyle=":", linewidth=1)
            axes.axhline(max_cylinder, color="#94a3b8", linestyle=":", linewidth=1)
            axes.text(0.99, min_cylinder, f" min {min_cylinder}", transform=axes.get_yaxis_transform(),
                      ha="right", va="bottom", fontsize=7, color="#64748b")
            axes.text(0.99, max_cylinder, f" max {max_cylinder}", transform=axes.get_yaxis_transform(),
                      ha="right", va="bottom", fontsize=7, color="#64748b")

            for edge_index, (start, end) in enumerate(zip(positions, positions[1:])):
                is_jump = edge_index in result.circular_jumps
                axes.plot(
                    [edge_index, edge_index + 1],
                    [start, end],
                    color=color,
                    linestyle="--" if is_jump else "-",
                    linewidth=1.8,
                    zorder=2,
                )
                if is_jump:
                    axes.annotate(
                        "wrap",
                        ((edge_index + 0.5), (start + end) / 2),
                        fontsize=7,
                        color=color,
                        ha="center",
                        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1},
                    )

            axes.scatter(x_positions, positions, color=color, s=22, zorder=3)
            axes.scatter([0], [result.initial_head], color="#111827", marker="D", s=38,
                         label="Initial head", zorder=5)

            labels_by_step: dict[int, list[str]] = defaultdict(list)
            for order, step in enumerate(result.service_steps, start=1):
                labels_by_step[step].append(str(order))
            for step, order_labels in labels_by_step.items():
                axes.annotate(
                    ",".join(order_labels),
                    (step, positions[step]),
                    xytext=(0, 7),
                    textcoords="offset points",
                    ha="center",
                    fontsize=6.5,
                    color="#0f172a",
                )

            axes.set_title(
                f"{result.algorithm}  |  total {result.total_movement}  |  avg {result.average_seek_distance:.1f}",
                fontsize=9,
                fontweight="bold",
                color="#0f172a",
            )
            axes.set_xlabel("Traversal step (labels show service order)", fontsize=7)
            axes.set_ylabel("Cylinder", fontsize=8)
            axes.set_xlim(-0.4, max(1, len(positions) - 0.6))
            axes.set_ylim(min_cylinder - 8, max_cylinder + 8)
            axes.grid(axis="y", color="#e2e8f0", linewidth=0.7)
            axes.tick_params(labelsize=7)

            if len(positions) > 1:
                first_edge = next(
                    (
                        index
                        for index, (start, end) in enumerate(zip(positions, positions[1:]))
                        if start != end and index not in result.circular_jumps
                    ),
                    None,
                )
                if first_edge is not None:
                    start = positions[first_edge]
                    end = positions[first_edge + 1]
                    axes.annotate(
                        "",
                        xy=(first_edge + 0.72, start + (end - start) * 0.72),
                        xytext=(first_edge + 0.42, start + (end - start) * 0.42),
                        arrowprops={"arrowstyle": "->", "color": color, "lw": 1.4},
                    )

        self.figure.suptitle(
            f"Disk-head paths  |  Initial direction: {'higher' if direction == 'up' else 'lower'} cylinders",
            fontsize=12,
            fontweight="bold",
            color="#0f172a",
        )
        self.figure.text(
            0.5,
            0.025,
            "Solid paths show head travel; dashed C-SCAN segments show the boundary-to-boundary wrap. "
            "Numbers mark request service order.",
            ha="center",
            fontsize=8,
            color="#475569",
        )
        self.canvas.draw_idle()
