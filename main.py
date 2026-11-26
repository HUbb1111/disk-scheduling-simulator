"""Tkinter desktop interface for the disk scheduling simulator."""

from __future__ import annotations

import re
import tkinter as tk
from collections import Counter
from tkinter import messagebox, ttk

from algorithms import ScheduleResult, run_all
from visualization import DiskMovementPlot

DEFAULT_REQUESTS = "98, 183, 37, 122, 14, 124, 65, 67"
DIRECTION_OPTIONS = {
    "Toward higher cylinders (toward max)": "up",
    "Toward lower cylinders (toward min)": "down",
}


def parse_simulation_inputs(
    head_text: str,
    minimum_text: str,
    maximum_text: str,
    requests_text: str,
    direction_label: str,
) -> tuple[list[int], int, int, int, str]:
    """Parse and validate the values entered in the simulation form."""
    head = _parse_integer(head_text, "Initial head position")
    minimum = _parse_integer(minimum_text, "Minimum cylinder")
    maximum = _parse_integer(maximum_text, "Maximum cylinder")

    if minimum < 0:
        raise ValueError("Minimum cylinder cannot be negative.")
    if maximum <= minimum:
        raise ValueError("Maximum cylinder must be greater than minimum cylinder.")
    if not minimum <= head <= maximum:
        raise ValueError(f"Initial head must be between {minimum} and {maximum}.")

    raw_requests = requests_text.strip()
    if not raw_requests:
        raise ValueError("Enter at least one disk request.")
    tokens = [token for token in re.split(r"[\s,]+", raw_requests) if token]
    requests = []
    for token in tokens:
        try:
            requests.append(int(token))
        except ValueError as error:
            raise ValueError(f"Request '{token}' is not a whole cylinder number.") from error

    if any(request < 0 for request in requests):
        raise ValueError("Cylinder numbers cannot be negative.")
    outside = [request for request in requests if request < minimum or request > maximum]
    if outside:
        raise ValueError(
            f"Request(s) {', '.join(map(str, outside))} are outside the disk boundaries "
            f"({minimum} to {maximum})."
        )
    duplicates = sorted(request for request, count in Counter(requests).items() if count > 1)
    if duplicates:
        raise ValueError(f"Duplicate cylinder request(s) are not allowed: {', '.join(map(str, duplicates))}.")

    direction = DIRECTION_OPTIONS.get(direction_label)
    if direction is None:
        raise ValueError("Select a valid initial direction.")
    return requests, head, minimum, maximum, direction


def _parse_integer(value: str, label: str) -> int:
    try:
        return int(value.strip())
    except ValueError as error:
        raise ValueError(f"{label} must be a whole number.") from error


class DiskSchedulingApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Disk Scheduling and Storage Simulator")
        self.root.geometry("1280x900")
        self.root.minsize(1000, 720)
        self.root.configure(bg="#f1f5f9")

        self.head_var = tk.StringVar(value="53")
        self.min_var = tk.StringVar(value="0")
        self.max_var = tk.StringVar(value="199")
        self.requests_var = tk.StringVar(value=DEFAULT_REQUESTS)
        self.direction_var = tk.StringVar(value=next(iter(DIRECTION_OPTIONS)))
        self.status_var = tk.StringVar(value="Enter disk parameters, then run the simulation.")

        self._configure_styles()
        self._build_ui()
        self._clear_results()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#f1f5f9")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f1f5f9", foreground="#0f172a", font=("Segoe UI", 9))
        style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"), foreground="#0f172a")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#475569")
        style.configure("CardTitle.TLabel", background="#ffffff", font=("Segoe UI", 11, "bold"))
        style.configure("Muted.TLabel", background="#ffffff", foreground="#64748b", font=("Segoe UI", 8))
        style.configure("TButton", font=("Segoe UI", 9), padding=(10, 7))
        style.configure("Run.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 9))
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=27, background="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TLabelframe", background="#ffffff")
        style.configure("TLabelframe.Label", background="#ffffff", font=("Segoe UI", 9, "bold"))

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=(18, 14))
        container.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)
        container.columnconfigure(0, weight=0, minsize=300)
        container.columnconfigure(1, weight=1)

        header = ttk.Frame(container)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ttk.Label(header, text="Disk Scheduling and Storage Simulator", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Explore head movement, service order, and performance across four operating-system algorithms.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        input_card = ttk.Frame(container, style="Card.TFrame", padding=14)
        input_card.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        output = ttk.Frame(container, style="Card.TFrame", padding=12)
        output.grid(row=1, column=1, sticky="nsew")
        output.rowconfigure(2, weight=1)
        output.columnconfigure(0, weight=1)

        ttk.Label(input_card, text="Simulation inputs", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 10))
        parameters = ttk.LabelFrame(input_card, text="Disk configuration", padding=10)
        parameters.pack(fill="x")

        self._add_entry(parameters, "Initial head position", self.head_var, 0)
        self._add_entry(parameters, "Minimum cylinder", self.min_var, 1)
        self._add_entry(parameters, "Maximum cylinder", self.max_var, 2)

        ttk.Label(parameters, text="Initial direction").grid(row=6, column=0, sticky="w", pady=(8, 3))
        direction = ttk.Combobox(
            parameters,
            textvariable=self.direction_var,
            values=tuple(DIRECTION_OPTIONS),
            state="readonly",
            width=30,
        )
        direction.grid(row=7, column=0, sticky="ew")
        parameters.columnconfigure(0, weight=1)

        request_frame = ttk.LabelFrame(input_card, text="Disk request sequence", padding=10)
        request_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(
            request_frame,
            text="Enter cylinder numbers separated by commas or spaces.",
            style="Muted.TLabel",
            wraplength=255,
        ).pack(anchor="w", pady=(0, 6))
        ttk.Entry(request_frame, textvariable=self.requests_var, width=34).pack(fill="x")

        buttons = ttk.Frame(input_card, style="Card.TFrame")
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text="Run Simulation", style="Run.TButton", command=self.run_simulation).pack(
            fill="x"
        )
        ttk.Button(buttons, text="Reset", command=self.reset).pack(fill="x", pady=(7, 0))
        ttk.Label(
            input_card,
            text="Requests at the current head are serviced with zero movement. "
                 "Duplicate cylinders are rejected in the form.",
            style="Muted.TLabel",
            wraplength=260,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))

        comparison = ttk.LabelFrame(output, text="Performance comparison", padding=8)
        comparison.grid(row=0, column=0, sticky="ew")
        comparison.columnconfigure(0, weight=1)
        columns = ("algorithm", "service_order", "total", "average")
        self.results_table = ttk.Treeview(comparison, columns=columns, show="headings", height=4)
        self.results_table.heading("algorithm", text="Algorithm")
        self.results_table.heading("service_order", text="Service order")
        self.results_table.heading("total", text="Total movement")
        self.results_table.heading("average", text="Average seek distance")
        self.results_table.column("algorithm", width=90, minwidth=80, anchor="center", stretch=False)
        self.results_table.column("service_order", width=340, minwidth=170, anchor="w")
        self.results_table.column("total", width=120, minwidth=105, anchor="center", stretch=False)
        self.results_table.column("average", width=160, minwidth=145, anchor="center", stretch=False)
        self.results_table.tag_configure("best", background="#dcfce7", foreground="#14532d")
        self.results_table.grid(row=0, column=0, sticky="ew")
        table_scroll = ttk.Scrollbar(comparison, orient="vertical", command=self.results_table.yview)
        table_scroll.grid(row=0, column=1, sticky="ns")
        self.results_table.configure(yscrollcommand=table_scroll.set)

        ttk.Label(output, textvariable=self.status_var, style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(7, 8)
        )

        graph_frame = ttk.LabelFrame(output, text="Head movement graph", padding=4)
        graph_frame.grid(row=2, column=0, sticky="nsew")
        graph_frame.rowconfigure(0, weight=1)
        graph_frame.columnconfigure(0, weight=1)
        self.movement_plot = DiskMovementPlot(graph_frame)
        self.movement_plot.widget.grid(row=0, column=0, sticky="nsew")

    @staticmethod
    def _add_entry(parent: ttk.LabelFrame, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row * 2, column=0, sticky="w", pady=(7 if row else 0, 3))
        ttk.Entry(parent, textvariable=variable).grid(row=row * 2 + 1, column=0, sticky="ew")

    def _read_inputs(self) -> tuple[list[int], int, int, int, str]:
        return parse_simulation_inputs(
            self.head_var.get(),
            self.min_var.get(),
            self.max_var.get(),
            self.requests_var.get(),
            self.direction_var.get(),
        )

    def run_simulation(self) -> None:
        try:
            requests, head, minimum, maximum, direction = self._read_inputs()
            results = run_all(requests, head, minimum, maximum, direction)
        except ValueError as error:
            messagebox.showerror("Input error", str(error), parent=self.root)
            return

        best_total = min(result.total_movement for result in results)
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        for result in results:
            best_tag = ("best",) if result.total_movement == best_total else ()
            self.results_table.insert(
                "",
                "end",
                values=(
                    result.algorithm,
                    " -> ".join(map(str, result.service_order)),
                    result.total_movement,
                    f"{result.average_seek_distance:.2f}",
                ),
                tags=best_tag,
            )

        winners = [result.algorithm for result in results if result.total_movement == best_total]
        winner_text = ", ".join(winners)
        self.status_var.set(
            f"Lowest movement: {winner_text} ({best_total} cylinders). "
            "Green rows mark the best result."
        )
        self.movement_plot.draw(results, minimum, maximum, direction)

    def reset(self) -> None:
        self.head_var.set("53")
        self.min_var.set("0")
        self.max_var.set("199")
        self.requests_var.set(DEFAULT_REQUESTS)
        self.direction_var.set(next(iter(DIRECTION_OPTIONS)))
        self._clear_results()

    def _clear_results(self) -> None:
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        self.status_var.set("Enter disk parameters, then run the simulation.")
        self.movement_plot.clear()


def create_app(root: tk.Tk) -> DiskSchedulingApp:
    return DiskSchedulingApp(root)


def main() -> None:
    root = tk.Tk()
    create_app(root)
    root.mainloop()


if __name__ == "__main__":
    main()
