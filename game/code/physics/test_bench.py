"""Physics benchmark: python3 test_bench.py (named test_* so builds exclude it).

200 bodies wander a 100 x 100 grid of 16 px cells with walls, turning when
they bump into something, with 20 areas watching them. Reports milliseconds
per tick (every body's move_and_slide plus grid.step()), then pathfinding
timings on a 4K room with 8 px cells.

Importing it (unittest discovery does) runs nothing.
"""

import math
import random
import statistics
import sys
import time

import uxphys_path
from uxphys_collide import Area, Body, CollisionGrid, RectShape, Terrain
from uxphys_math import Vector2

BODIES = 200
AREAS = 20
COLUMNS = ROWS = 100
CELL = 16
DELTA = 1 / 60.0
WARMUP = 60
TICKS = 600


def make_world(rng):
    cells = bytearray(COLUMNS * ROWS)
    for i in range(COLUMNS):
        cells[i] = cells[(ROWS - 1) * COLUMNS + i] = 1
        cells[i * COLUMNS] = cells[i * COLUMNS + COLUMNS - 1] = 1
    # Wall blocks and lines, about 10% of the cells.
    for _ in range(120):
        x = rng.randrange(2, COLUMNS - 6)
        y = rng.randrange(2, ROWS - 6)
        w, h = (rng.randrange(1, 8), 1) if rng.random() < 0.5 else (1, rng.randrange(1, 8))
        if rng.random() < 0.3:
            w, h = rng.randrange(2, 4), rng.randrange(2, 4)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                cells[yy * COLUMNS + xx] = 1
    grid = CollisionGrid(COLUMNS, ROWS, CELL, cells, terrains=[Terrain(0), Terrain(1), Terrain(0, 0.5)])
    # Some mud.
    for _ in range(30):
        x = rng.randrange(1, COLUMNS - 1)
        y = rng.randrange(1, ROWS - 1)
        if not grid.get_cell((x, y)):
            grid.set_cell((x, y), 2)

    feet = RectShape(-6, -4, 12, 8)
    bodies = []
    while len(bodies) < BODIES:
        position = (rng.uniform(20, COLUMNS * CELL - 20), rng.uniform(20, ROWS * CELL - 20))
        if grid.is_free(feet, position):
            body = grid.add(Body(feet, position=position))
            body.velocity = Vector2.from_angle(rng.uniform(0, math.tau)) * rng.uniform(60, 120)
            bodies.append(body)

    counts = {"entered": 0, "exited": 0}

    def entered(body):
        counts["entered"] += 1

    def exited(body):
        counts["exited"] += 1

    for _ in range(AREAS):
        area = grid.add(Area(RectShape(0, 0, 64, 64), position=(rng.uniform(16, 1500), rng.uniform(16, 1500))))
        area.body_entered.connect(entered)
        area.body_exited.connect(exited)
    return grid, bodies, counts


def tick(grid, bodies, rng):
    for body in bodies:
        if body.move_and_slide(DELTA):
            # Bumped into something: wander off another way.
            body.velocity = Vector2.from_angle(rng.uniform(0, math.tau)) * rng.uniform(60, 120)
    grid.step()


def bench_ticks():
    rng = random.Random(1)
    grid, bodies, counts = make_world(rng)
    for _ in range(WARMUP):
        tick(grid, bodies, rng)
    times = []
    for _ in range(TICKS):
        start = time.perf_counter()
        tick(grid, bodies, rng)
        times.append((time.perf_counter() - start) * 1000.0)
    times.sort()
    print("%d bodies, %d areas, %dx%d cells of %d px, %d ticks:" % (BODIES, AREAS, COLUMNS, ROWS, CELL, TICKS))
    print("  mean %.3f ms   median %.3f ms   p95 %.3f ms   max %.3f ms per tick" % (
        statistics.mean(times), times[len(times) // 2], times[int(len(times) * 0.95)], times[-1]))
    print("  areas: %d enters, %d exits" % (counts["entered"], counts["exited"]))
    return statistics.mean(times)


def bench_paths():
    rng = random.Random(2)
    columns, rows, cell = 480, 270, 8  # a 3840 x 2160 room
    cells = bytearray(columns * rows)
    for _ in range(900):
        x = rng.randrange(0, columns - 10)
        y = rng.randrange(0, rows - 10)
        if rng.random() < 0.5:
            for xx in range(x, x + rng.randrange(3, 30)):
                if xx < columns:
                    cells[y * columns + xx] = 1
        else:
            for yy in range(y, y + rng.randrange(3, 30)):
                if yy < rows:
                    cells[yy * columns + x] = 1
    grid = CollisionGrid(columns, rows, cell, cells)
    box = (-6, -4, 12, 8)

    start = time.perf_counter()
    uxphys_path.astar(grid, (8, 8), (9, 9), box)
    build = (time.perf_counter() - start) * 1000.0

    pairs = []
    while len(pairs) < 30:
        a = (rng.uniform(0, columns * cell), rng.uniform(0, rows * cell))
        b = (rng.uniform(0, columns * cell), rng.uniform(0, rows * cell))
        if math.dist(a, b) > 1500:
            pairs.append((a, b))

    print("Pathfinding on %dx%d cells of %d px (a 4K room with random walls), 30 long paths:" % (columns, rows, cell))
    print("  maps for one body size (walkable, regions, neighbours): %.1f ms once, then cached" % build)
    for label, weight in (("exact astar() + smooth_path()", 1.0), ("find_path(), weight 1.2", 1.2)):
        times = []
        for a, b in pairs:
            start = time.perf_counter()
            uxphys_path.find_path(grid, a, b, box, heuristic_weight=weight)
            times.append((time.perf_counter() - start) * 1000.0)
        times.sort()
        print("  %-30s median %.1f ms   p90 %.1f ms   max %.1f ms" % (
            label + ":", times[len(times) // 2], times[int(len(times) * 0.9)], times[-1]))


if __name__ == "__main__":
    print("Python %s" % sys.version.split()[0])
    mean = bench_ticks()
    print("  target < 2 ms: %s" % ("met" if mean < 2.0 else "NOT met"))
    bench_paths()
