"""Tests for uxphys_path. Run from this folder:
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
"""

import random
import unittest

import uxphys_path as path
from test_uxphys_collide import CS, WALL, make_grid
from uxphys_collide import Body, CollisionGrid, RectShape, StaticBody
from uxphys_math import Rect2, Vector2

MAZE = (
    "#####################",
    "#...#.......#.......#",
    "#.#.#.#####.#.#####.#",
    "#.#...#...#...#...#.#",
    "#.#####.#.#####.#.#.#",
    "#.......#.......#...#",
    "#####################",
)
SMALL = Rect2(-4, -4, 8, 8)


def center(cx, cy):
    return Vector2((cx + 0.5) * CS, (cy + 0.5) * CS)


class PathCase(unittest.TestCase):

    def assertPathClear(self, grid, points, box, mask=1):
        for a, b in zip(points, points[1:]):
            self.assertTrue(path.segment_clear(grid, a, b, box, mask), "blocked between %s and %s" % (a, b))

    def walk(self, grid, body, points, speed=120.0, ticks=2000):
        """Steers body along points with move_and_slide; returns ticks used, or None."""
        points = list(points[1:])
        delta = 1 / 60.0
        for tick in range(ticks):
            if not points:
                return tick
            target = points[0]
            offset = target - body.position
            if offset.length() <= speed * delta:
                body.velocity = offset / delta
                points.pop(0)
            else:
                body.velocity = offset.normalized() * speed
            body.move_and_slide(delta)
        return None


class TestAstar(PathCase):

    def test_maze(self):
        grid = make_grid(*MAZE)
        start = center(1, 1)
        goal = center(19, 5) + Vector2(2, 3)
        raw = path.astar(grid, start, goal, SMALL)
        self.assertGreater(len(raw), 10)
        self.assertEqual(raw[0], start)
        self.assertEqual(raw[-1], goal)
        walk = path.walkable_map(grid, SMALL)
        for point in raw[1:-1]:
            cx, cy = int(point.x // CS), int(point.y // CS)
            self.assertTrue(walk[cy * grid.columns + cx])
            self.assertEqual(point, center(cx, cy))
        self.assertPathClear(grid, raw, SMALL)

        smooth = path.smooth_path(grid, raw, SMALL)
        self.assertLess(len(smooth), len(raw))
        self.assertEqual(smooth[0], start)
        self.assertEqual(smooth[-1], goal)
        self.assertPathClear(grid, smooth, SMALL)

        # A body really gets there along it.
        body = grid.add(Body(RectShape(-4, -4, 8, 8), position=start))
        self.assertIsNotNone(self.walk(grid, body, smooth))
        self.assertLess(body.position.distance_to(goal), 0.01)

    def test_body_size(self):
        # Only a 1-cell gap: the small body gets through, the big one can't.
        grid = make_grid(
            "##########",
            "#........#",
            "#........#",
            "####.#####",
            "#........#",
            "#........#",
            "##########",
        )
        start = center(4, 1)
        goal = center(4, 5)
        small = path.astar(grid, start, goal, SMALL)
        self.assertTrue(small)
        self.assertTrue(all(p.x == center(4, 0).x for p in small))
        big = Rect2(-12, -12, 24, 24)
        self.assertEqual(path.astar(grid, start, goal, big), [])
        self.assertIsNot(path.walkable_map(grid, SMALL), path.walkable_map(grid, big))

        # With a 3-cell gap further along, the big body goes the long way round.
        grid = make_grid(
            "##############",
            "#............#",
            "#............#",
            "#............#",
            "####.####...##",
            "#............#",
            "#............#",
            "#............#",
            "##############",
        )
        start = center(4, 2)
        goal = center(4, 6)
        self.assertTrue(all(p.x < 6 * CS for p in path.astar(grid, start, goal, SMALL)))
        long_way = path.astar(grid, start, goal, big)
        self.assertTrue(any(p.x > 8 * CS for p in long_way))
        self.assertPathClear(grid, long_way, big)
        self.assertPathClear(grid, path.smooth_path(grid, long_way, big), big)

    def test_start_outside_grid(self):
        grid = make_grid(*MAZE)
        goal = center(5, 1)
        for start in (Vector2(-50, -50), Vector2(10000, 30), Vector2(40, -1)):
            raw = path.astar(grid, start, goal, SMALL)
            self.assertTrue(raw, start)
            self.assertEqual(raw[0], start)
            self.assertTrue(grid.get_rect().has_point(raw[1]))
            self.assertEqual(raw[-1], goal)

    def test_start_where_body_does_not_fit(self):
        grid = make_grid(*MAZE)
        # Standing (illegally) inside a wall: snapped to the nearest open cell.
        raw = path.astar(grid, center(2, 2), center(5, 1), SMALL)
        self.assertTrue(raw)
        self.assertIn(raw[1], (center(1, 2), center(3, 2), center(2, 1)))

    def test_goal_in_wall(self):
        grid = make_grid(
            "..........",
            "..........",
            "...####...",
            "...####...",
            "...####...",
            "..........",
        )
        raw = path.astar(grid, center(0, 0), center(5, 3) + Vector2(3, 0), SMALL)
        self.assertEqual(raw[-1], center(7, 3))

    def test_unreachable(self):
        grid = make_grid(
            "..........",
            "......####",
            "......#..#",
            "......####",
        )
        goal = center(7, 2)
        self.assertEqual(path.astar(grid, center(0, 0), goal, SMALL), [])
        partial = path.astar(grid, center(0, 0), goal, SMALL, allow_partial_path=True)
        self.assertTrue(partial)
        # Two reachable cells are equally near (32 px): either will do.
        self.assertIn(partial[-1], (center(5, 2), center(7, 0)))

    def test_max_expansions(self):
        grid = make_grid(*MAZE)
        self.assertEqual(path.astar(grid, center(1, 1), center(19, 5), SMALL, max_expansions=10), [])
        partial = path.astar(grid, center(1, 1), center(19, 5), SMALL, max_expansions=10, allow_partial_path=True)
        self.assertTrue(len(partial) >= 2)

    def test_terrain_speed(self):
        # Straight through the mud costs 3 + 5 * 2 = 13; round it about 9.7.
        grid = make_grid(
            "..,,,,,..",
            "..,,,,,..",
            ".........",
        )
        start = center(0, 0)
        goal = center(8, 0)
        slow_aware = path.astar(grid, start, goal, SMALL)
        self.assertTrue(any(p.y > 2 * CS for p in slow_aware))
        straight = path.astar(grid, start, goal, SMALL, use_terrain_speed=False)
        self.assertTrue(all(p.y < CS for p in straight))

    def test_static_bodies_block_and_cache(self):
        grid = make_grid(
            "#########",
            "#.......#",
            "#########",
        )
        start = center(1, 1)
        goal = center(7, 1)
        walk = path.walkable_map(grid, SMALL)
        self.assertIs(path.walkable_map(grid, SMALL), walk)
        door = grid.add(StaticBody(RectShape(0, 0, 4, 16), position=(4 * CS + 6, CS)))
        self.assertIsNot(path.walkable_map(grid, SMALL), walk)
        self.assertEqual(path.astar(grid, start, goal, SMALL), [])
        grid.remove(door)
        self.assertTrue(path.astar(grid, start, goal, SMALL))
        # Moving bodies don't block paths.
        grid.add(Body(RectShape(0, 0, 16, 16), position=(4 * CS, CS)))
        self.assertTrue(path.astar(grid, start, goal, SMALL))

    def test_mask(self):
        grid = make_grid("....~....", "....~....")
        self.assertTrue(path.astar(grid, center(0, 0), center(8, 0), SMALL, collision_mask=1))
        self.assertEqual(path.astar(grid, center(0, 0), center(8, 0), SMALL, collision_mask=1 | 2), [])

    def test_outside(self):
        grid = make_grid("....", "....", "....")
        box = Rect2(-8, -8, 16, 16)
        self.assertTrue(path.walkable_map(grid, box)[0])
        grid.outside = WALL
        self.assertTrue(path.walkable_map(grid, box)[0])
        self.assertFalse(path.walkable_map(grid, Rect2(-10, -8, 20, 16))[0])
        self.assertFalse(path.segment_clear(grid, (8, 8), (-20, 8), SMALL))

    def test_same_cell_and_exact_goal(self):
        grid = make_grid(".....", "..#..", ".....")
        raw = path.astar(grid, (10, 10), (12, 6), SMALL)
        self.assertEqual(raw, [Vector2(10, 10), Vector2(12, 6)])
        # The body doesn't fit at (30, 22): its box would overlap the wall cell.
        raw = path.astar(grid, (10, 10), (30, 13), SMALL)
        self.assertEqual(raw[-1], center(1, 0))


class TestSmoothing(PathCase):

    def test_open_field(self):
        grid = make_grid(*(["." * 30] * 20))
        raw = path.astar(grid, (8, 8), (400, 300), SMALL)
        self.assertGreater(len(raw), 10)
        self.assertEqual(path.smooth_path(grid, raw, SMALL), [Vector2(8, 8), Vector2(400, 300)])
        self.assertEqual(path.find_path(grid, (8, 8), (400, 300), SMALL), [Vector2(8, 8), Vector2(400, 300)])

    def test_keeps_corners(self):
        grid = make_grid(
            "......",
            "......",
            "####..",
            "......",
        )
        raw = path.astar(grid, center(0, 0), center(0, 3), SMALL)
        smooth = path.smooth_path(grid, raw, SMALL)
        self.assertGreaterEqual(len(smooth), 3)
        self.assertPathClear(grid, smooth, SMALL)

    def test_segment_clear_exact(self):
        grid = make_grid("....", ".#..", "....")
        # The wall cell spans x 16..32, y 16..32. A box of half-size 4 at y=12 touches it from above.
        self.assertTrue(path.segment_clear(grid, (0, 12), (60, 12), SMALL))
        self.assertFalse(path.segment_clear(grid, (0, 12.5), (60, 12.5), SMALL))
        self.assertTrue(path.segment_clear(grid, (0, 0), (60, 0), SMALL))
        self.assertFalse(path.segment_clear(grid, (8, 8), (40, 40), SMALL))
        # Diagonal passing near the corner (16, 16): the box corner clips it.
        self.assertFalse(path.segment_clear(grid, (4, 30), (30, 4), SMALL))
        self.assertTrue(path.segment_clear(grid, (4, 20), (20, 4), Rect2(-1, -1, 2, 2)))

    def test_short_paths_unchanged(self):
        grid = make_grid("....")
        self.assertEqual(path.smooth_path(grid, [], SMALL), [])
        self.assertEqual(path.smooth_path(grid, [Vector2(1, 1), Vector2(2, 2)], SMALL), [Vector2(1, 1), Vector2(2, 2)])


class TestMaps(unittest.TestCase):

    def random_grid(self, seed, columns=23, rows=17):
        rng = random.Random(seed)
        cells = bytearray(1 if rng.random() < 0.3 else 0 for _ in range(columns * rows))
        return CollisionGrid(columns, rows, CS, cells)

    def test_neighbors_match_brute_force(self):
        for seed in range(5):
            grid = self.random_grid(seed)
            cols, rows = grid.columns, grid.rows
            walk = path.walkable_map(grid, SMALL)
            masks = path._neighbors(grid, walk, ("test", seed))

            def ok(c, r):
                return 0 <= c < cols and 0 <= r < rows and walk[r * cols + c]

            for r in range(rows):
                for c in range(cols):
                    expected = 0
                    for bit, (dc, dr) in enumerate(((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1))):
                        if ok(c + dc, r + dr) and (not dc or not dr or (ok(c + dc, r) and ok(c, r + dr))):
                            expected |= 1 << bit
                    self.assertEqual(masks[r * cols + c], expected, (seed, c, r))

    def test_regions_match_flood_fill(self):
        for seed in range(5):
            grid = self.random_grid(seed + 10)
            cols, rows = grid.columns, grid.rows
            walk = path.walkable_map(grid, SMALL)
            labels = path.regions(grid, SMALL)
            seen = {}
            for start in range(cols * rows):
                if not walk[start] or start in seen:
                    self.assertEqual(labels[start] == 0, not walk[start])
                    continue
                # Flood fill through sides; every cell found must share one label, unused elsewhere.
                stack = [start]
                seen[start] = start
                while stack:
                    i = stack.pop()
                    self.assertEqual(labels[i], labels[start])
                    r, c = divmod(i, cols)
                    for dc, dr in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nc, nr = c + dc, r + dr
                        j = nr * cols + nc
                        if 0 <= nc < cols and 0 <= nr < rows and walk[j] and j not in seen:
                            seen[j] = start
                            stack.append(j)
            groups = {}
            for i, root in seen.items():
                groups.setdefault(labels[i], set()).add(root)
            self.assertTrue(all(len(roots) == 1 for roots in groups.values()))

    def test_heuristic_weight_still_finds_paths(self):
        grid = make_grid(*MAZE)
        raw = path.astar(grid, center(1, 1), center(19, 5), SMALL, heuristic_weight=2.0)
        self.assertEqual(raw[-1], center(19, 5))
        for a, b in zip(raw, raw[1:]):
            self.assertTrue(path.segment_clear(grid, a, b, SMALL))


class TestWindow(unittest.TestCase):

    def test_windows(self):
        grid = make_grid("....")
        self.assertEqual(path._window(grid, -4, -4, 4, 4), (0, 0, 0, 0))
        self.assertEqual(path._window(grid, -8, -8, 8, 8), (0, 0, 0, 0))
        self.assertEqual(path._window(grid, -8, -8, 9, 8), (0, 0, 1, 0))
        self.assertEqual(path._window(grid, -6, -4, 6, 0), (0, 0, 0, 0))
        self.assertEqual(path._window(grid, -24, -30, 24, 0), (-1, -2, 1, 0))
        self.assertEqual(path._window(grid, 0, 0, 0, 0), (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
