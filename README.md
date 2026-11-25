# Disk Scheduling and Storage Simulator

A desktop teaching tool that compares FCFS, SSTF, SCAN, and C-SCAN disk scheduling. It reports each algorithm's service order, total physical head movement, and average seek distance, and plots the paths in a Tkinter window.

## Objectives

- Explore how disk scheduling policies change request order and head travel.
- Visualize requests, disk boundaries, the initial head, and movement direction.
- Compare all four algorithms on the same input and highlight the lowest movement.
- Make boundary travel and the C-SCAN wrap visible and count them correctly.

## Technologies

- Python 3.10 or later
- Tkinter (included with most standard Python installations)
- Matplotlib
- NumPy is not used directly.

## Installation

In PowerShell, open this project folder and install its Python dependency:

```powershell
cd C:\xampp\htdocs\ecommerce\DiskSchedulingSimulatorDesktop
python -m pip install -r requirements.txt
```

Tkinter is part of Python's standard library. If `import tkinter` fails, install or repair Python with its Tcl/Tk support enabled.

## Run the application

```powershell
cd C:\xampp\htdocs\ecommerce\DiskSchedulingSimulatorDesktop
python main.py
```

The starting form uses head `53`, boundaries `0` and `199`, requests `98, 183, 37, 122, 14, 124, 65, 67`, and an initial direction toward higher cylinders. Change the values and select **Run Simulation** to refresh the comparison and graphs. **Reset** restores the sample values and clears the results.

## Run automated tests

```powershell
cd C:\xampp\htdocs\ecommerce\DiskSchedulingSimulatorDesktop
python -m unittest discover -s tests -v
```

## Algorithms

- **FCFS (First-Come, First-Served):** services requests in their input order.
- **SSTF (Shortest Seek Time First):** repeatedly services the pending request nearest the current head. Equal-distance ties retain their input order.
- **SCAN (Elevator):** services requests in the chosen direction, travels to that disk boundary, then reverses to service remaining requests.
- **C-SCAN (Circular SCAN):** services requests in one direction, travels to that boundary, and, when requests remain on the other side, wraps to the opposite boundary before continuing in the original direction. The wrap is physical travel, not a serviced request.

The GUI accepts nonnegative integer cylinders within the inclusive disk boundaries, requires at least one request, and rejects duplicate entries. A request at the initial head position is allowed and contributes zero movement.

## Calculation formulas

Let the physical head path be `p[0], p[1], ..., p[k]`, including disk-boundary travel and any C-SCAN wrap.

- Movement for each physical segment: `d[i] = abs(p[i + 1] - p[i])`
- Total head movement: `sum(d[i])`
- Average seek distance: `total head movement / number of requests`

The circular jump is included in the physical path and total movement. It is not inserted into the service order. Requests already at the current head need no extra path segment, so they add zero movement.

## Sample input and output

Using head `53`, cylinders `0–199`, requests `98, 183, 37, 122, 14, 124, 65, 67`, and direction toward higher cylinders:

| Algorithm | Service order | Total movement | Average seek distance |
|---|---|---:|---:|
| FCFS | 98, 183, 37, 122, 14, 124, 65, 67 | 640 | 80.00 |
| SSTF | 65, 67, 37, 14, 98, 122, 124, 183 | 236 | 29.50 |
| SCAN | 65, 67, 98, 122, 124, 183, 37, 14 | 331 | 41.38 |
| C-SCAN | 65, 67, 98, 122, 124, 183, 14, 37 | 382 | 47.75 |

For example, the upward C-SCAN path is `53 -> 65 -> 67 -> 98 -> 122 -> 124 -> 183 -> 199 -> 0 -> 14 -> 37`. Its total includes `16` cylinders to the upper boundary, a `199`-cylinder wrap, and `37` cylinders to the last request: `382`.
