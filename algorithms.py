"""Disk scheduling algorithms and their movement metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

Direction = Literal["up", "down"]


@dataclass(frozen=True)
class ScheduleResult:
    """The service order and physical path produced by one algorithm."""

    algorithm: str
    initial_head: int
    service_order: tuple[int, ...]
    movement_sequence: tuple[int, ...]
    movement_distances: tuple[int, ...]
    total_movement: int
    average_seek_distance: float
    service_steps: tuple[int, ...]
    circular_jumps: tuple[int, ...]


class _RouteBuilder:
    def __init__(self, initial_head: int) -> None:
        self.positions = [initial_head]
        self.distances: list[int] = []
        self.service_order: list[int] = []
        self.service_steps: list[int] = []
        self.circular_jumps: list[int] = []

    def move_to(self, cylinder: int, circular: bool = False) -> None:
        current = self.positions[-1]
        if current == cylinder and not circular:
            return

        if circular:
            self.circular_jumps.append(len(self.positions) - 1)
        self.distances.append(abs(cylinder - current))
        self.positions.append(cylinder)

    def service(self, cylinder: int) -> None:
        self.move_to(cylinder)
        self.service_order.append(cylinder)
        self.service_steps.append(len(self.positions) - 1)

    def result(self, algorithm: str) -> ScheduleResult:
        total = sum(self.distances)
        return ScheduleResult(
            algorithm=algorithm,
            initial_head=self.positions[0],
            service_order=tuple(self.service_order),
            movement_sequence=tuple(self.positions),
            movement_distances=tuple(self.distances),
            total_movement=total,
            average_seek_distance=total / len(self.service_order),
            service_steps=tuple(self.service_steps),
            circular_jumps=tuple(self.circular_jumps),
        )


def _validate_inputs(
    requests: Iterable[int],
    head: int,
    min_cylinder: int,
    max_cylinder: int,
    direction: str,
) -> tuple[tuple[int, ...], Direction]:
    try:
        request_list = tuple(requests)
    except TypeError as error:
        raise ValueError("Requests must be a sequence of cylinder numbers.") from error

    values = (("Initial head", head), ("Minimum cylinder", min_cylinder), ("Maximum cylinder", max_cylinder))
    for label, value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{label} must be an integer.")
    if min_cylinder < 0:
        raise ValueError("The minimum cylinder cannot be negative.")
    if min_cylinder >= max_cylinder:
        raise ValueError("The maximum cylinder must be greater than the minimum cylinder.")
    if not min_cylinder <= head <= max_cylinder:
        raise ValueError("The initial head must be within the disk boundaries.")
    if not request_list:
        raise ValueError("Enter at least one disk request.")
    if direction not in ("up", "down"):
        raise ValueError("Direction must be 'up' or 'down'.")

    for request in request_list:
        if isinstance(request, bool) or not isinstance(request, int):
            raise ValueError("Every disk request must be an integer.")
        if request < min_cylinder or request > max_cylinder:
            raise ValueError(
                f"Request {request} is outside the disk boundaries "
                f"({min_cylinder} to {max_cylinder})."
            )
    validated_direction: Direction = "up" if direction == "up" else "down"
    return request_list, validated_direction


def fcfs(
    requests: Iterable[int],
    head: int,
    min_cylinder: int = 0,
    max_cylinder: int = 199,
    direction: str = "up",
) -> ScheduleResult:
    """Service requests in the order they were submitted."""
    request_list, _ = _validate_inputs(requests, head, min_cylinder, max_cylinder, direction)
    route = _RouteBuilder(head)
    for request in request_list:
        route.service(request)
    return route.result("FCFS")


def sstf(
    requests: Iterable[int],
    head: int,
    min_cylinder: int = 0,
    max_cylinder: int = 199,
    direction: str = "up",
) -> ScheduleResult:
    """Always service the nearest pending request; ties keep input order."""
    request_list, _ = _validate_inputs(requests, head, min_cylinder, max_cylinder, direction)
    route = _RouteBuilder(head)
    pending = list(request_list)

    while pending:
        nearest_index = min(
            range(len(pending)),
            key=lambda index: (abs(pending[index] - route.positions[-1]), index),
        )
        route.service(pending.pop(nearest_index))
    return route.result("SSTF")


def scan(
    requests: Iterable[int],
    head: int,
    min_cylinder: int = 0,
    max_cylinder: int = 199,
    direction: str = "up",
) -> ScheduleResult:
    """Sweep to a disk boundary, then reverse to service remaining requests."""
    request_list, direction = _validate_inputs(requests, head, min_cylinder, max_cylinder, direction)
    route = _RouteBuilder(head)

    for request in (item for item in request_list if item == head):
        route.service(request)

    if direction == "up":
        for request in sorted(item for item in request_list if item > head):
            route.service(request)
        route.move_to(max_cylinder)
        for request in sorted((item for item in request_list if item < head), reverse=True):
            route.service(request)
    else:
        for request in sorted((item for item in request_list if item < head), reverse=True):
            route.service(request)
        route.move_to(min_cylinder)
        for request in sorted(item for item in request_list if item > head):
            route.service(request)
    return route.result("SCAN")


def c_scan(
    requests: Iterable[int],
    head: int,
    min_cylinder: int = 0,
    max_cylinder: int = 199,
    direction: str = "up",
) -> ScheduleResult:
    """Sweep in one direction and wrap to the opposite edge when needed."""
    request_list, direction = _validate_inputs(requests, head, min_cylinder, max_cylinder, direction)
    route = _RouteBuilder(head)

    for request in (item for item in request_list if item == head):
        route.service(request)

    if direction == "up":
        for request in sorted(item for item in request_list if item > head):
            route.service(request)
        route.move_to(max_cylinder)
        remaining = sorted(item for item in request_list if item < head)
        if remaining:
            route.move_to(min_cylinder, circular=True)
            for request in remaining:
                route.service(request)
    else:
        for request in sorted((item for item in request_list if item < head), reverse=True):
            route.service(request)
        route.move_to(min_cylinder)
        remaining = sorted((item for item in request_list if item > head), reverse=True)
        if remaining:
            route.move_to(max_cylinder, circular=True)
            for request in remaining:
                route.service(request)
    return route.result("C-SCAN")


def run_all(
    requests: Iterable[int],
    head: int,
    min_cylinder: int = 0,
    max_cylinder: int = 199,
    direction: str = "up",
) -> tuple[ScheduleResult, ...]:
    """Run all four algorithms for the same disk configuration."""
    request_list, direction = _validate_inputs(requests, head, min_cylinder, max_cylinder, direction)
    return (
        fcfs(request_list, head, min_cylinder, max_cylinder, direction),
        sstf(request_list, head, min_cylinder, max_cylinder, direction),
        scan(request_list, head, min_cylinder, max_cylinder, direction),
        c_scan(request_list, head, min_cylinder, max_cylinder, direction),
    )
