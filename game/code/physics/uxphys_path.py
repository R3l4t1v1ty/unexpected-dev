"""Pathfinding on a CollisionGrid: A* over cells for a body of a given size,
then string pulling.

    import uxphys_path
    box = body.get_local_aabb()
    path = uxphys_path.astar(grid, body.position, target, box, body.collision_mask,
                             allow_partial_path=True)
    path = uxphys_path.smooth_path(grid, path, box, body.collision_mask)

Paths are lists of Vector2 positions for the body (its position, not the
box's corner): the start, waypoints at cell centres, and the goal.

Terrain and static bodies block; moving Bodies don't (they move: let
move_and_slide handle them). Walkability maps are cached per mask and body
size until the terrain or static bodies change.

A start or goal outside the grid, or where the body doesn't fit, is moved to
the nearest cell where it fits.
"""

import heapq
import math
from array import array

from uxphys_math import Vector2

__all__ = ["MAX_EXPANSIONS", "walkable_map", "regions", "astar", "smooth_path", "find_path", "segment_clear"]

MAX_EXPANSIONS = 30000
# How far (in cells) to look for a cell where the body fits, around the start and the goal.
START_RADIUS = 8
GOAL_RADIUS = 32

_SQRT2 = math.sqrt(2.0)
_INF = math.inf
# Shrinks boxes so that touching a blocked cell doesn't count as overlapping it.
_EPS = 1e-6


def _box(box):
    """(x0, y0, x1, y1) of a body box relative to its position. box is a
    Rect2, an (x, y, w, h) tuple, a shape, or None for a point."""
    if box is None:
        return (0.0, 0.0, 0.0, 0.0)
    if hasattr(box, "get_rect"):
        box = box.get_rect()
    x, y, w, h = box
    return (float(x), float(y), float(x) + w, float(y) + h)


def _window(grid, x0, y0, x1, y1):
    """The cells (relative to the cell) a box covers when its body stands at a
    cell's centre: (left, top, right, bottom), inclusive."""
    cs = float(grid.cell_size)
    left = math.floor(0.5 + x0 / cs)
    top = math.floor(0.5 + y0 / cs)
    right = max(left, math.ceil(0.5 + x1 / cs) - 1)
    bottom = max(top, math.ceil(0.5 + y1 / cs) - 1)
    return left, top, right, bottom


def _outside_blocks(grid, collision_mask):
    return grid.is_cell_blocked((-1, -1), collision_mask)


def walkable_map(grid, box=None, collision_mask=1):
    """bytes, one per cell: 1 where a body with this box (relative to its
    position) fits with its position at the cell's centre. Cached on the grid."""
    x0, y0, x1, y1 = _box(box)
    left, top, right, bottom = _window(grid, x0, y0, x1, y1)
    key = ("walkable", collision_mask, left, top, right, bottom)
    result = grid.cache.get(key)
    if result is not None:
        return result

    cols = grid.columns
    rows = grid.rows
    blocked = grid.blocked_map(collision_mask)
    outside = _outside_blocks(grid, collision_mask)

    # Each row becomes an int with bit (column + pad) set where blocked, then the
    # window is OR-ed together with shifts: one big-int operation per offset.
    pad = max(-left, right, 0)
    full = (1 << (cols + 2 * pad)) - 1
    pad_bits = full & ~(((1 << cols) - 1) << pad) if outside else 0
    to_digits = bytes.maketrans(b"\x00\x01", b"01")
    horizontal = []
    for row in range(rows):
        digits = blocked[row * cols:(row + 1) * cols].translate(to_digits)[::-1]
        bits = (int(digits, 2) << pad) | pad_bits
        spread = 0
        for k in range(left, right + 1):
            spread |= (bits >> k) if k >= 0 else (bits << -k)
        horizontal.append(spread)

    edge = full if outside else 0
    to_walkable = bytes.maketrans(b"01", b"\x01\x00")
    mask = (1 << cols) - 1
    out = []
    for row in range(rows):
        spread = 0
        for k in range(top, bottom + 1):
            r = row + k
            spread |= horizontal[r] if 0 <= r < rows else edge
        bits = (spread >> pad) & mask
        out.append(format(bits, "0%db" % cols)[::-1].encode("ascii").translate(to_walkable))
    result = b"".join(out)
    grid.cache[key] = result
    return result


def _neighbors(grid, walk, key):
    """bytes, one per cell: bit d set when the step in direction d (see
    _steps) stays in the grid on a walkable cell, without cutting a corner."""
    result = grid.cache.get(key)
    if result is not None:
        return result
    cols = grid.columns
    rows = grid.rows
    n = cols * rows
    # The whole map as one int, a byte per cell: shifting by 8 bits moves one cell.
    w = int.from_bytes(walk, "little")
    not_first = int.from_bytes((b"\x00" + b"\x01" * (cols - 1)) * rows, "little")
    not_last = int.from_bytes((b"\x01" * (cols - 1) + b"\x00") * rows, "little")
    row = 8 * cols
    left = (w << 8) & not_first
    right = (w >> 8) & not_last
    up = w << row
    down = w >> row
    up_left = (w << (row + 8)) & not_first & left & up
    up_right = (w << (row - 8)) & not_last & right & up
    down_left = (w >> (row - 8)) & not_first & left & down
    down_right = (w >> (row + 8)) & not_last & right & down
    combined = (left | right << 1 | up << 2 | down << 3
                | up_left << 4 | up_right << 5 | down_left << 6 | down_right << 7)
    result = (combined & ((1 << (8 * n)) - 1)).to_bytes(n, "little")
    grid.cache[key] = result
    return result


def _steps(cols):
    """For each 8-bit neighbour mask, the steps it allows: (index offset,
    column offset, row offset, length)."""
    directions = ((-1, -1, 0, 1.0), (1, 1, 0, 1.0), (-cols, 0, -1, 1.0), (cols, 0, 1, 1.0),
                  (-cols - 1, -1, -1, _SQRT2), (-cols + 1, 1, -1, _SQRT2),
                  (cols - 1, -1, 1, _SQRT2), (cols + 1, 1, 1, _SQRT2))
    return tuple(tuple(d for bit, d in enumerate(directions) if m & (1 << bit)) for m in range(256))


def _cell_costs(grid):
    """(per-cell cost list or None if all terrain is normal speed, lowest cost)."""
    speeds = [t.speed for t in grid.terrains]
    if all(s == 1.0 for s in speeds):
        return None, 1.0
    key = ("costs",)
    costs = grid.cache.get(key)
    table = [1.0] * 256
    for i, s in enumerate(speeds):
        table[i] = 1.0 / max(s, 0.01)
    if costs is None:
        costs = [table[c] for c in grid.get_cells()]
        grid.cache[key] = costs
    return costs, min(min(table), 1.0)


def regions(grid, box=None, collision_mask=1):
    """array('i'), one per cell: which connected region of walkable_map() the
    cell is in (0 where the body doesn't fit). Two cells with the same region
    reach each other. Cached on the grid with the walkable map."""
    x0, y0, x1, y1 = _box(box)
    walk = walkable_map(grid, (x0, y0, x1 - x0, y1 - y0), collision_mask)
    return _regions(grid, walk, ("regions", collision_mask) + _window(grid, x0, y0, x1, y1))


def _regions(grid, walk, key):
    labels = grid.cache.get(key)
    if labels is not None:
        return labels
    cols = grid.columns
    rows = grid.rows

    # Union-find over runs of walkable cells, row by row. Cells connect through
    # their sides only: a diagonal step needs both side cells free anyway.
    parent = [0]

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    runs = []
    previous = []
    for row in range(rows):
        base = row * cols
        line = walk[base:base + cols]
        current = []
        x = line.find(1)
        while x >= 0:
            end = line.find(0, x)
            if end < 0:
                end = cols
            run = len(parent)
            parent.append(run)
            current.append((x, end, run))
            runs.append((base + x, base + end, run))
            x = line.find(1, end) if end < cols else -1
        j = 0
        for x, end, run in current:
            while j < len(previous) and previous[j][1] <= x:
                j += 1
            k = j
            while k < len(previous) and previous[k][0] < end:
                a = find(run)
                b = find(previous[k][2])
                if a != b:
                    parent[max(a, b)] = min(a, b)
                k += 1
        previous = current

    labels = array("i", [0]) * (cols * rows)
    for a, b, run in runs:
        labels[a:b] = array("i", [find(run)]) * (b - a)
    grid.cache[key] = labels
    return labels


def _nearest_walkable(walk, cols, rows, cs, px, py, radius, labels=None, region=0):
    """Index of the walkable cell (in `region` of labels, if given) whose centre
    is nearest (px, py), searching up to radius cells around the (clamped)
    cell under it, or None."""
    cx = min(max(math.floor(px / cs), 0), cols - 1)
    cy = min(max(math.floor(py / cs), 0), rows - 1)
    best = None
    best_d = _INF
    for ring in range(radius + 1):
        # A cell in this ring is at least this far (in pixels) from the start cell's edge.
        if best is not None and (ring - 1) * cs > best_d:
            break
        if ring > cx and ring > cy and ring + cx >= cols and ring + cy >= rows:
            break  # the ring has left the grid on every side
        for y in range(cy - ring, cy + ring + 1):
            if not 0 <= y < rows:
                continue
            edge_row = y == cy - ring or y == cy + ring
            xs = range(cx - ring, cx + ring + 1) if edge_row else (cx - ring, cx + ring)
            for x in xs:
                if 0 <= x < cols:
                    i = y * cols + x
                    if walk[i] and (labels is None or labels[i] == region):
                        d = math.hypot((x + 0.5) * cs - px, (y + 0.5) * cs - py)
                        if d < best_d:
                            best_d = d
                            best = i
    return best


def _box_fits(blocked, cols, rows, cs, outside, x0, y0, x1, y1):
    """Whether the world box overlaps no blocked cell (touching is fine)."""
    x0 += _EPS
    y0 += _EPS
    x1 -= _EPS
    y1 -= _EPS
    if outside and (x0 < 0 or y0 < 0 or x1 > cols * cs or y1 > rows * cs):
        return False
    c0 = max(0, math.floor(x0 / cs))
    c1 = min(cols - 1, math.floor(x1 / cs))
    if c0 > c1:
        return True
    for row in range(max(0, math.floor(y0 / cs)), min(rows - 1, math.floor(y1 / cs)) + 1):
        if blocked.find(1, row * cols + c0, row * cols + c1 + 1) >= 0:
            return False
    return True


def astar(grid, start, goal, box=None, collision_mask=1, max_expansions=MAX_EXPANSIONS,
          allow_partial_path=False, use_terrain_speed=True, heuristic_weight=1.0):
    """The shortest path from start to goal (pixel positions) for a body with
    this box (relative to its position, see walkable_map), moving in 8
    directions without cutting corners. Slow terrain costs more when
    use_terrain_speed.

    Returns a list of Vector2: start, cell centres, then the goal (or the
    centre of the nearest reachable cell where the body fits, if it doesn't
    fit at the goal). Returns [] if the goal can't be reached, or if the search
    gives up after max_expansions cells; with allow_partial_path it then
    returns the path to the reachable cell nearest the goal instead (like
    Godot's AStarGrid2D).

    heuristic_weight above 1 (say 1.5) searches far fewer cells for paths
    that may be a little longer; smooth_path() hides most of the difference."""
    x0, y0, x1, y1 = _box(box)
    cols = grid.columns
    rows = grid.rows
    cs = float(grid.cell_size)
    walk = walkable_map(grid, (x0, y0, x1 - x0, y1 - y0), collision_mask)
    window = _window(grid, x0, y0, x1, y1)
    labels = _regions(grid, walk, ("regions", collision_mask) + window)
    neighbors = _neighbors(grid, walk, ("neighbors", collision_mask) + window)
    steps = _steps(cols)
    sx, sy = float(start[0]), float(start[1])
    gx, gy = float(goal[0]), float(goal[1])

    s = _nearest_walkable(walk, cols, rows, cs, sx, sy, START_RADIUS)
    if s is None:
        return []
    region = labels[s]
    goal_cell = (min(max(math.floor(gy / cs), 0), rows - 1) * cols
                 + min(max(math.floor(gx / cs), 0), cols - 1))
    if walk[goal_cell]:
        g = goal_cell
        reachable = labels[g] == region
    else:
        # The body doesn't fit at the goal: the nearest reachable cell where it does.
        g = _nearest_walkable(walk, cols, rows, cs, gx, gy, GOAL_RADIUS, labels, region)
        reachable = g is not None
    if not reachable:
        if not allow_partial_path:
            return []
        # The reachable cell nearest the goal, however far.
        g = _nearest_walkable(walk, cols, rows, cs, gx, gy, max(cols, rows), labels, region)

    costs, min_cost = _cell_costs(grid) if use_terrain_speed else (None, 1.0)
    goal_col = g % cols
    goal_row = g // cols
    # Octile distance, scaled by the cheapest terrain so it never overestimates.
    straight = min_cost
    diag_extra = (_SQRT2 - 1.0) * min_cost
    weight = float(heuristic_weight)

    dx = abs(s % cols - goal_col)
    dy = abs(s // cols - goal_row)
    h0 = straight * dy + diag_extra * dx if dx < dy else straight * dx + diag_extra * dy
    heap = [(h0 * weight, h0, s)]
    n = cols * rows
    gscore = [_INF] * n
    gscore[s] = 0.0
    came = {s: -1}
    closed = bytearray(n)
    best = s
    best_h = h0
    expansions = 0
    found = False
    push = heapq.heappush
    pop = heapq.heappop

    while heap:
        _, h, i = pop(heap)
        if closed[i]:
            continue
        closed[i] = 1
        if i == g:
            found = True
            break
        expansions += 1
        if expansions > max_expansions:
            break
        if h < best_h:
            best = i
            best_h = h
        gi = gscore[i]
        r, c = divmod(i, cols)
        dc0 = c - goal_col
        dr0 = r - goal_row
        for offset, dc, dr, step in steps[neighbors[i]]:
            j = i + offset
            if closed[j]:
                continue
            ng = gi + (step * costs[j] if costs is not None else step)
            if ng < gscore[j]:
                gscore[j] = ng
                came[j] = i
                dx = dc0 + dc
                if dx < 0:
                    dx = -dx
                dy = dr0 + dr
                if dy < 0:
                    dy = -dy
                hj = straight * dy + diag_extra * dx if dx < dy else straight * dx + diag_extra * dy
                push(heap, (ng + hj * weight, hj, j))

    if found:
        end = g
    elif allow_partial_path:
        end = best
    else:
        return []

    cells = []
    i = end
    while i >= 0:
        cells.append(i)
        i = came[i]
    cells.reverse()

    path = [Vector2(sx, sy)]
    start_col = math.floor(sx / cs)
    start_row = math.floor(sy / cs)
    for n, i in enumerate(cells):
        c = i % cols
        r = i // cols
        if n == 0 and c == start_col and r == start_row:
            continue  # already standing in it
        path.append(Vector2((c + 0.5) * cs, (r + 0.5) * cs))
    if found and reachable:
        blocked = grid.blocked_map(collision_mask)
        outside = _outside_blocks(grid, collision_mask)
        in_goal_cell = math.floor(gx / cs) == goal_col and math.floor(gy / cs) == goal_row
        if in_goal_cell and _box_fits(blocked, cols, rows, cs, outside, gx + x0, gy + y0, gx + x1, gy + y1):
            if len(path) > 1:
                path[-1] = Vector2(gx, gy)
            else:
                path.append(Vector2(gx, gy))
    if len(path) == 1:
        # Ending in the start's own cell: still return two points.
        path.append(Vector2((end % cols + 0.5) * cs, (end // cols + 0.5) * cs))
    return path


def segment_clear(grid, from_point, to_point, box=None, collision_mask=1):
    """Whether a body with this box moving in a straight line from from_point
    to to_point stays clear of terrain and static bodies (cell-exact)."""
    x0, y0, x1, y1 = _box(box)
    blocked = grid.blocked_map(collision_mask)
    outside = _outside_blocks(grid, collision_mask)
    return _swept_clear(blocked, grid.columns, grid.rows, float(grid.cell_size), outside,
                        x0, y0, x1, y1, float(from_point[0]), float(from_point[1]),
                        float(to_point[0]), float(to_point[1]))


def _swept_clear(blocked, cols, rows, cs, outside, x0, y0, x1, y1, px, py, qx, qy):
    # The box at the start, shrunk so touching doesn't count.
    ax0 = px + x0 + _EPS
    ax1 = px + x1 - _EPS
    ay0 = py + y0 + _EPS
    ay1 = py + y1 - _EPS
    if ax1 < ax0:
        ax0 = ax1 = px + (x0 + x1) * 0.5
    if ay1 < ay0:
        ay0 = ay1 = py + (y0 + y1) * 0.5
    dx = qx - px
    dy = qy - py
    ymin = min(ay0, ay0 + dy)
    ymax = max(ay1, ay1 + dy)
    if outside:
        xmin = min(ax0, ax0 + dx)
        xmax = max(ax1, ax1 + dx)
        if xmin < 0 or ymin < 0 or xmax > cols * cs or ymax > rows * cs:
            return False

    # Row by row: when the box overlaps the row, and its x extent meanwhile.
    for row in range(max(0, math.floor(ymin / cs)), min(rows - 1, math.floor(ymax / cs)) + 1):
        top = row * cs
        bottom = top + cs
        if dy:
            ta = (bottom - ay0) / dy
            tb = (top - ay1) / dy
            if ta > tb:
                ta, tb = tb, ta
            t0 = ta if ta > 0.0 else 0.0
            t1 = tb if tb < 1.0 else 1.0
            if t0 > t1:
                continue
        else:
            t0 = 0.0
            t1 = 1.0
        if dx >= 0:
            left = ax0 + dx * t0
            right = ax1 + dx * t1
        else:
            left = ax0 + dx * t1
            right = ax1 + dx * t0
        c0 = max(0, math.floor(left / cs))
        c1 = min(cols - 1, math.floor(right / cs))
        if c0 <= c1 and blocked.find(1, row * cols + c0, row * cols + c1 + 1) >= 0:
            return False
    return True


def smooth_path(grid, path, box=None, collision_mask=1):
    """String pulling: drops every waypoint the body can skip by going
    straight, checked cell-exact against terrain and static bodies. The first
    and last points are kept."""
    path = list(path)
    if len(path) < 3:
        return path
    x0, y0, x1, y1 = _box(box)
    blocked = grid.blocked_map(collision_mask)
    outside = _outside_blocks(grid, collision_mask)
    cols = grid.columns
    rows = grid.rows
    cs = float(grid.cell_size)

    result = [path[0]]
    anchor = path[0]
    for i in range(1, len(path) - 1):
        nxt = path[i + 1]
        if not _swept_clear(blocked, cols, rows, cs, outside, x0, y0, x1, y1, anchor.x, anchor.y, nxt.x, nxt.y):
            result.append(path[i])
            anchor = path[i]
    result.append(path[-1])
    return result


def find_path(grid, start, goal, box=None, collision_mask=1, max_expansions=MAX_EXPANSIONS,
              allow_partial_path=True, use_terrain_speed=True, heuristic_weight=1.2):
    """astar() then smooth_path(), for tap-to-move: partial paths are allowed
    (tapping somewhere unreachable walks to the nearest reachable spot), and
    the search is slightly greedy (heuristic_weight 1.2): in big rooms it's
    about 3x faster, for smoothed paths about 3% longer."""
    path = astar(grid, start, goal, box, collision_mask, max_expansions, allow_partial_path,
                 use_terrain_speed, heuristic_weight)
    return smooth_path(grid, path, box, collision_mask)
