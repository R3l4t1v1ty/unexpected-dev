"""Tests for uxphys_collide. Run from this folder:
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
"""

import math
import unittest

import uxphys_collide as col
from uxphys_collide import Area, Body, CircleShape, CollisionGrid, RectShape, StaticBody, Terrain
from uxphys_math import Vector2, Vector2i

CS = 16
FLOOR, WALL, WATER, MUD = 0, 1, 2, 3
# Layers: walls on 1, water on 2, mud blocks nothing but halves speed.
TERRAINS = [Terrain(0), Terrain(1), Terrain(2), Terrain(0, 0.5)]
CHARS = {".": FLOOR, "#": WALL, "~": WATER, ",": MUD}


def make_grid(*rows, **kwargs):
    """A grid from ASCII rows: . floor, # wall, ~ water, , mud."""
    cells = bytearray(CHARS[c] for row in rows for c in row)
    return CollisionGrid(len(rows[0]), len(rows), CS, cells, terrains=TERRAINS, **kwargs)


def open_grid(columns=20, rows=20, **kwargs):
    return make_grid(*(["." * columns] * rows), **kwargs)


def box(size=8):
    return RectShape.centered(size, size)


class Case(unittest.TestCase):

    def assertNear(self, a, b, tolerance=0.01, msg=None):
        self.assertLessEqual(abs(a - b), tolerance, msg or "%r != %r" % (a, b))

    def run_body(self, body, velocity, ticks=1, delta=1 / 60.0):
        body.velocity = Vector2(*velocity)
        for _ in range(ticks):
            body.move_and_slide(delta)


class TestShapesAndQueries(Case):

    def test_shapes(self):
        r = RectShape(-6, -4, 12, 4)
        self.assertEqual(tuple(r.get_rect()), (-6, -4, 12, 4))
        self.assertEqual(tuple(RectShape.centered(10, 4).get_rect()), (-5, -2, 10, 4))
        self.assertEqual(tuple(RectShape((1, 2, 3, 4)).get_rect()), (1, 2, 3, 4))
        self.assertEqual(tuple(CircleShape(5, 1, 1).get_rect()), (-4, -4, 10, 10))
        with self.assertRaises(ValueError):
            RectShape(0, 0, 0, 5)
        with self.assertRaises(ValueError):
            CircleShape(0)

    def test_intersect_shape_touching_is_not_overlapping(self):
        grid = open_grid()
        a = grid.add(StaticBody(RectShape(0, 0, 10, 10), position=(50, 50)))
        self.assertEqual(grid.intersect_shape(RectShape(0, 0, 10, 10), (60, 50)), [])
        self.assertEqual(grid.intersect_shape(RectShape(0, 0, 10, 10), (59.9, 50)), [a])

    def test_circle_box_corner(self):
        grid = open_grid()
        grid.add(StaticBody(RectShape(0, 0, 10, 10), position=(50, 50)))
        # Corner at (60, 60): a circle of radius 5 at (64, 64) is 5.66 away.
        self.assertEqual(grid.intersect_shape(CircleShape(5), (64, 64)), [])
        self.assertEqual(len(grid.intersect_shape(CircleShape(6), (64, 64))), 1)
        self.assertEqual(len(grid.intersect_shape(CircleShape(5), (64, 55))), 1)

    def test_circle_circle(self):
        grid = open_grid()
        grid.add(StaticBody(CircleShape(5), position=(100, 100)))
        self.assertEqual(grid.intersect_shape(CircleShape(5), (110, 100)), [])
        self.assertEqual(len(grid.intersect_shape(CircleShape(5), (109, 100))), 1)

    def test_intersect_point(self):
        grid = open_grid()
        a = grid.add(StaticBody(RectShape(0, 0, 10, 10), position=(50, 50)))
        area = grid.add(Area(CircleShape(8), position=(55, 55)))
        self.assertEqual(grid.intersect_point((55, 55)), [a])
        self.assertEqual(grid.intersect_point((55, 55), collide_with_areas=True), [a, area])
        self.assertEqual(grid.intersect_point((60, 55)), [])
        self.assertEqual(grid.intersect_point((55, 55), collision_mask=2), [])
        self.assertEqual(grid.intersect_point((55, 55), exclude=[a]), [])

    def test_is_free(self):
        grid = make_grid("....", ".#..", "....", "....")
        self.assertTrue(grid.is_free(box(8), (8, 8)))
        self.assertFalse(grid.is_free(box(8), (16, 20)))
        self.assertTrue(grid.is_free(box(8), (12, 20)))  # touching the wall's left side
        self.assertTrue(grid.is_free(box(8), (16, 20), collision_mask=2))
        s = grid.add(StaticBody(box(8), position=(50, 50)))
        self.assertFalse(grid.is_free(box(8), (52, 52)))
        self.assertTrue(grid.is_free(box(8), (52, 52), exclude=[s]))
        # Outside: open by default, blocked with a solid outside terrain.
        self.assertTrue(grid.is_free(box(8), (0, 30)))
        grid.outside = WALL
        self.assertFalse(grid.is_free(box(8), (0, 30)))

    def test_terrain_lookup(self):
        grid = make_grid("..,", ".#.")
        self.assertEqual(grid.get_cell((1, 1)), WALL)
        self.assertEqual(grid.get_cell((-1, 0)), FLOOR)
        self.assertEqual(grid.local_to_map((17, 31.9)), Vector2i(1, 1))
        self.assertEqual(grid.local_to_map((-0.5, 0)), Vector2i(-1, 0))
        self.assertEqual(grid.map_to_local((1, 1)), Vector2(24, 24))
        self.assertEqual(grid.terrain_at((40, 2)), MUD)
        self.assertEqual(grid.speed_at((40, 2)), 0.5)
        self.assertTrue(grid.is_cell_blocked((1, 1)))
        self.assertFalse(grid.is_cell_blocked((1, 1), collision_mask=2))
        grid.set_cell((1, 1), FLOOR)
        self.assertFalse(grid.is_cell_blocked((1, 1)))
        with self.assertRaises(IndexError):
            grid.set_cell((5, 5), WALL)
        self.assertEqual(grid.size, Vector2(48, 32))


class TestMovement(Case):

    def test_no_tunnelling_terrain(self):
        grid = make_grid(*(["....#....."] * 5))
        body = grid.add(Body(box(8), position=(8, 40)))
        self.run_body(body, (1000000, 0))
        self.assertLessEqual(body.position.x + 4, 64)
        self.assertNear(body.position.x, 60)
        c = body.get_slide_collision(0)
        self.assertEqual(c.normal, Vector2(-1, 0))
        self.assertIs(c.collider, grid)
        self.assertEqual(c.cell, Vector2i(4, 2))
        self.assertNear(c.position.x, 64)
        self.assertTrue(body.is_on_wall())
        self.assertEqual(body.get_wall_normal(), Vector2(-1, 0))

    def test_no_tunnelling_thin_static(self):
        grid = open_grid(40, 5)
        wall = grid.add(StaticBody(RectShape(0, 0, 1, 80), position=(300, 0)))
        body = grid.add(Body(box(8), position=(20, 40)))
        self.run_body(body, (500000, 0))
        self.assertNear(body.position.x, 296)
        self.assertIs(body.get_slide_collision(0).collider, wall)
        # And from the other side, fast and backwards.
        body.position = (600, 40)
        self.run_body(body, (-500000, 0))
        self.assertNear(body.position.x, 305)

    def test_no_tunnelling_circle(self):
        grid = make_grid(*(["....#....."] * 5))
        body = grid.add(Body(CircleShape(4), position=(8, 40)))
        self.run_body(body, (1000000, 0))
        self.assertNear(body.position.x, 60)
        self.assertEqual(body.get_slide_collision(0).normal, Vector2(-1, 0))

    def test_no_tunnelling_body_vs_body(self):
        grid = open_grid(60, 5)
        other = grid.add(Body(RectShape(0, 0, 2, 2), position=(500, 39)))
        body = grid.add(Body(box(8), position=(20, 40)))
        self.run_body(body, (900000, 0))
        self.assertNear(body.position.x, 496)
        self.assertIs(body.get_slide_collision(0).collider, other)

    def test_diagonal_tunnelling_through_corner_gap(self):
        # Two wall cells touching at a corner: a diagonal move can't squeeze between.
        grid = make_grid("......", "..#...", ".#....", "......")
        body = grid.add(Body(CircleShape(2), position=(12, 52)))
        self.run_body(body, (60000, -60000))
        p = body.position
        self.assertFalse(p.x > 32 and p.y < 32)

    def test_slide_along_wall_no_snag(self):
        # A long wall made of many cells; moving diagonally into it slides the whole way.
        grid = make_grid(*(["......#"] * 50))
        body = grid.add(Body(box(8), position=(80, 20)))
        body.velocity = Vector2(120, 120)
        for _ in range(240):
            body.move_and_slide(1 / 60.0)
        self.assertNear(body.position.x, 92)
        # Constant speed along the wall after the first contact: 120*sqrt(2) px/s.
        self.assertGreater(body.position.y, 20 + 120 * 3.5)
        self.assertTrue(body.is_on_wall())
        self.assertLess(body.get_real_velocity().x, 1e-6)

    def test_slide_along_wall_circle_no_snag(self):
        grid = make_grid(*(["......#"] * 50))
        body = grid.add(Body(CircleShape(4), position=(80, 20)))
        start_y = body.position.y
        body.velocity = Vector2(100, 100)
        for _ in range(240):
            body.move_and_slide(1 / 60.0)
        self.assertNear(body.position.x, 92)
        self.assertGreater(body.position.y - start_y, 100 * 3.5)

    def test_slide_along_floor_of_bodies(self):
        # Sliding along a row of separate static boxes doesn't catch on their seams either.
        grid = open_grid(40, 10)
        for i in range(20):
            grid.add(StaticBody(RectShape(0, 0, 16, 16), position=(i * 16, 100)))
        body = grid.add(Body(box(8), position=(20, 80)))
        body.velocity = Vector2(100, 100)
        for _ in range(120):
            body.move_and_slide(1 / 60.0)
        self.assertNear(body.position.y, 96)
        self.assertGreater(body.position.x, 20 + 100 * 1.9)

    def test_corner_stops(self):
        grid = make_grid("######", "#....#", "#....#", "######")
        body = grid.add(Body(box(8), position=(40, 30)))
        body.velocity = Vector2(200, 200)
        for _ in range(60):
            body.move_and_slide(1 / 60.0)
        self.assertNear(body.position.x, 76)
        self.assertNear(body.position.y, 44)

    def test_head_on_stops_unless_min_angle_zero(self):
        grid = make_grid(*(["......#"] * 20))
        angle = math.radians(5)
        velocity = (100 * math.cos(angle), 100 * math.sin(angle))
        body = grid.add(Body(box(8), position=(80, 100)))
        self.run_body(body, velocity, ticks=60)
        self.assertNear(body.position.y, 100 + 100 * math.sin(angle) * (12 / (100 * math.cos(angle))), 0.5)
        stopped_y = body.position.y
        self.run_body(body, velocity, ticks=60)
        self.assertNear(body.position.y, stopped_y)
        body.wall_min_slide_angle = 0
        self.run_body(body, velocity, ticks=60)
        self.assertGreater(body.position.y, stopped_y + 50)

    def test_circle_slides_round_a_corner(self):
        grid = make_grid(*(["......"] * 3 + ["...###"] * 3))
        body = grid.add(Body(CircleShape(4), position=(40, 46)))
        # Moving right just low enough to clip the block's top-left corner (48, 48).
        self.run_body(body, (1200, 0))
        c = body.get_slide_collision(0)
        self.assertLess(c.normal.x, 0)
        self.assertLess(c.normal.y, 0)
        self.assertGreater(body.position.x, 46)
        self.assertLess(body.position.y, 46)

    def test_rect_against_circle(self):
        grid = open_grid()
        pillar = grid.add(StaticBody(CircleShape(10), position=(100, 100)))
        body = grid.add(Body(box(8), position=(40, 100)))
        self.run_body(body, (6000, 0))
        self.assertNear(body.position.x, 86)
        c = body.get_slide_collision(0)
        self.assertIs(c.collider, pillar)
        self.assertEqual(c.collider_shape, pillar.shapes[0])
        self.assertNear(c.normal.x, -1)
        self.assertNear(c.position.x, 90)

    def test_layer_masks(self):
        grid = make_grid(*(["....~....."] * 5))
        walker = grid.add(Body(box(8), position=(8, 40), collision_mask=1 | 2))
        bullet = grid.add(Body(box(2), position=(8, 20), collision_mask=1))
        self.run_body(walker, (6000, 0))
        self.assertNear(walker.position.x, 60)
        self.run_body(bullet, (6000, 0))
        self.assertGreater(bullet.position.x, 100)

        # A static body on layer 3 (value 4) only stops masks that include it.
        grid2 = open_grid(40, 5)
        ghost_wall = grid2.add(StaticBody(RectShape(0, 0, 4, 80), position=(200, 0), collision_layer=4))
        a = grid2.add(Body(box(8), position=(20, 40)))
        b = grid2.add(Body(box(8), position=(20, 60)))
        b.set_collision_mask_value(3, True)
        self.assertEqual(b.collision_mask, 1 | 4)
        self.assertTrue(b.get_collision_mask_value(3))
        self.run_body(a, (30000, 0))
        self.run_body(b, (30000, 0))
        self.assertGreater(a.position.x, 300)
        self.assertNear(b.position.x, 196)
        ghost_wall.collision_layer = 1
        self.run_body(a, (-30000, 0))
        self.assertNear(a.position.x, 208)

    def test_bodies_on_other_layers_pass_through(self):
        grid = open_grid(40, 5)
        npc = grid.add(Body(box(8), position=(100, 40), collision_layer=2))
        player = grid.add(Body(box(8), position=(20, 40)))
        self.run_body(player, (12000, 0))
        self.assertGreater(player.position.x, 150)
        npc.collision_layer = 1
        self.run_body(player, (-12000, 0))
        self.assertNear(player.position.x, 108)

    def test_collision_exceptions(self):
        grid = open_grid(40, 5)
        shooter = grid.add(Body(box(8), position=(100, 40)))
        bullet = grid.add(Body(box(2), position=(80, 40)))
        bullet.add_collision_exception_with(shooter)
        self.run_body(bullet, (6000, 0))
        self.assertGreater(bullet.position.x, 150)
        self.assertEqual(bullet.get_collision_exceptions(), [shooter])
        bullet.remove_collision_exception_with(shooter)
        self.run_body(bullet, (-12000, 0))
        self.assertNear(bullet.position.x, 105)

    def test_outside(self):
        grid = open_grid(10, 10)
        body = grid.add(Body(box(8), position=(80, 80)))
        self.run_body(body, (-60000, 0))
        self.assertLess(body.position.x, 0)
        walled = open_grid(10, 10, outside=WALL)
        body = walled.add(Body(box(8), position=(80, 80)))
        self.run_body(body, (-60000, 0))
        self.assertNear(body.position.x, 4)
        self.assertIsNone(body.get_slide_collision(0).cell)
        self.run_body(body, (0, 60000))
        self.assertNear(body.position.y, 156)

    def test_remove_by_owner(self):
        grid = open_grid(40, 5)
        prop = object()
        grid.add(StaticBody(RectShape(0, 0, 4, 40), position=(200, 0), owner=prop))
        grid.add(StaticBody(RectShape(0, 40, 4, 40), position=(200, 0), owner=prop))
        self.assertEqual(len(grid.objects_of(prop)), 2)
        body = grid.add(Body(box(8), position=(20, 40)))
        self.run_body(body, (30000, 0))
        self.assertNear(body.position.x, 196)
        version = grid.version
        grid.remove_owner(prop)
        self.assertGreater(grid.version, version)
        self.assertEqual(grid.objects_of(prop), [])
        self.run_body(body, (30000, 0))
        self.assertGreater(body.position.x, 300)

    def test_terrain_speed(self):
        grid = make_grid(*([",,,,,,,,,,"] * 3))
        body = grid.add(Body(box(8), position=(20, 24)))
        self.run_body(body, (60, 0))
        self.assertNear(body.position.x, 20.5)
        self.assertEqual(body.terrain_speed, 0.5)
        self.assertNear(body.get_real_velocity().x, 30)
        body.use_terrain_speed = False
        self.run_body(body, (60, 0))
        self.assertNear(body.position.x, 21.5)

    def test_starting_overlap_can_escape(self):
        grid = open_grid(20, 5)
        grid.add(StaticBody(RectShape(0, 0, 16, 16), position=(100, 32)))
        body = grid.add(Body(box(8), position=(98, 40)))  # 2 px into the box's left side
        self.run_body(body, (600, 0))
        self.assertNear(body.position.x, 98)
        self.assertNear(body.get_slide_collision(0).depth, 2)
        self.run_body(body, (-600, 0))
        self.assertNear(body.position.x, 88)

    def test_move_and_collide(self):
        grid = make_grid(*(["....#....."] * 5))
        body = grid.add(Body(box(8), position=(8, 40)))
        c = body.move_and_collide(Vector2(100, 0), test_only=True)
        self.assertIsNotNone(c)
        self.assertEqual(body.position, Vector2(8, 40))
        self.assertNear(c.travel.x, 52)
        self.assertNear(c.remainder.x, 48)
        self.assertTrue(body.test_move((100, 0)))
        self.assertFalse(body.test_move((10, 0)))
        self.assertIsNone(body.move_and_collide((10, 0)))
        self.assertEqual(body.position, Vector2(18, 40))
        self.assertEqual(body.get_last_motion(), Vector2(10, 0))
        c = body.move_and_collide((100, 0))
        self.assertNear(body.position.x, 60)
        self.assertNear(c.get_angle(), math.pi / 2)

    def test_bodies_found_after_crossing_buckets(self):
        grid = open_grid(60, 60)
        mover = grid.add(Body(box(8), position=(20, 20)))
        self.run_body(mover, (600 * 60, 600 * 60))  # 600 px diagonally, far across buckets
        self.assertNear(mover.position.x, 620)
        chaser = grid.add(Body(box(8), position=(500, 620)))
        self.run_body(chaser, (60000, 0))
        self.assertNear(chaser.position.x, 612)
        self.assertIs(chaser.get_slide_collision(0).collider, mover)

    def test_teleport_and_shapes(self):
        grid = open_grid(40, 5)
        wall = grid.add(StaticBody(RectShape(0, 0, 4, 80), position=(200, 0)))
        body = grid.add(Body(box(8), position=(20, 40)))
        wall.position = (100, 0)
        self.run_body(body, (30000, 0))
        self.assertNear(body.position.x, 96)
        body.shapes = [box(16)]
        self.assertEqual(body.get_local_aabb().size, Vector2(16, 16))
        body.position = (20, 40)
        self.run_body(body, (30000, 0))
        self.assertNear(body.position.x, 92)

    def test_errors(self):
        grid = open_grid()
        body = Body(box(8))
        with self.assertRaises(RuntimeError):
            body.move_and_slide(1 / 60.0)
        grid.add(body)
        with self.assertRaises(ValueError):
            grid.add(body)
        with self.assertRaises(ValueError):
            open_grid().remove(body)
        with self.assertRaises(ValueError):
            body.position = (math.nan, 0)
        with self.assertRaises(TypeError):
            Body([object()])


class AreaCase(Case):

    def setUp(self):
        self.grid = open_grid(30, 30)
        self.events = []

    def watch(self, area, name="area"):
        area.body_entered.connect(lambda body: self.events.append((name, "body_entered", body)))
        area.body_exited.connect(lambda body: self.events.append((name, "body_exited", body)))
        area.area_entered.connect(lambda other: self.events.append((name, "area_entered", other)))
        area.area_exited.connect(lambda other: self.events.append((name, "area_exited", other)))
        return area

    def take(self):
        events = self.events
        self.events = []
        return events


class TestAreas(AreaCase):

    def test_enter_stay_exit(self):
        grid = self.grid
        area = self.watch(grid.add(Area(RectShape(0, 0, 64, 64), position=(160, 160))))
        body = grid.add(Body(box(8), position=(100, 192)))
        grid.step()
        self.assertEqual(self.take(), [])
        body.velocity = Vector2(600, 0)
        for _ in range(8):
            body.move_and_slide(1 / 60.0)
            grid.step()
        self.assertEqual(self.take(), [("area", "body_entered", body)])
        self.assertEqual(area.get_overlapping_bodies(), [body])
        self.assertTrue(area.overlaps_body(body))
        # Staying inside: no more events.
        body.velocity = Vector2(60, 0)
        for _ in range(10):
            body.move_and_slide(1 / 60.0)
            grid.step()
        self.assertEqual(self.take(), [])
        body.velocity = Vector2(6000, 0)
        body.move_and_slide(1 / 60.0)
        grid.step()
        self.assertEqual(self.take(), [("area", "body_exited", body)])
        self.assertFalse(area.has_overlapping_bodies())

    def test_events_wait_for_step(self):
        grid = self.grid
        self.watch(grid.add(Area(RectShape(0, 0, 64, 64), position=(160, 160))))
        body = grid.add(Body(box(8), position=(192, 192)))
        self.assertEqual(self.take(), [])
        grid.step()
        self.assertEqual(self.take(), [("area", "body_entered", body)])

    def test_teleport_through_area_in_one_tick(self):
        grid = self.grid
        self.watch(grid.add(Area(RectShape(0, 0, 64, 64), position=(160, 160))))
        body = grid.add(Body(box(8), position=(100, 100)))
        grid.step()
        body.position = (192, 192)
        body.position = (400, 400)
        grid.step()
        self.assertEqual(self.take(), [])

    def test_remove_body_inside(self):
        grid = self.grid
        area = self.watch(grid.add(Area(RectShape(0, 0, 64, 64), position=(160, 160))))
        body = grid.add(Body(box(8), position=(192, 192)))
        grid.step()
        self.take()
        grid.remove(body)
        self.assertEqual(self.take(), [])
        grid.step()
        self.assertEqual(self.take(), [("area", "body_exited", body)])
        self.assertEqual(area.get_overlapping_bodies(), [])
        grid.step()
        self.assertEqual(self.take(), [])

    def test_remove_area_with_body_inside(self):
        grid = self.grid
        area = self.watch(grid.add(Area(RectShape(0, 0, 64, 64), position=(160, 160))))
        body = grid.add(Body(box(8), position=(192, 192)))
        grid.step()
        self.take()
        grid.remove(area)
        grid.step()
        self.assertEqual(self.take(), [("area", "body_exited", body)])
        self.assertEqual(body._monitors, {})
        # Moving the body afterwards is fine and fires nothing.
        body.position = (195, 195)
        grid.step()
        self.assertEqual(self.take(), [])

    def test_remove_from_callback(self):
        grid = self.grid
        area = grid.add(Area(RectShape(0, 0, 64, 64), position=(160, 160)))
        coin = grid.add(Body(box(8), position=(192, 192)))
        player = grid.add(Body(box(8), position=(200, 200)))
        area.body_entered.connect(lambda body: grid.remove(body) if body is coin else None)
        self.watch(area)
        grid.step()
        self.assertNotIn(coin, grid)
        self.assertEqual(self.take(), [("area", "body_entered", coin), ("area", "body_entered", player)])
        grid.step()
        self.assertEqual(self.take(), [("area", "body_exited", coin)])
        self.assertEqual(area.get_overlapping_bodies(), [player])

    def test_area_added_over_body_and_moving_area(self):
        grid = self.grid
        body = grid.add(Body(box(8), position=(192, 192)))
        static = grid.add(StaticBody(box(8), position=(300, 192)))
        grid.step()
        area = self.watch(grid.add(Area(RectShape(-32, -32, 64, 64), position=(192, 192))))
        grid.step()
        self.assertEqual(self.take(), [("area", "body_entered", body)])
        area.position = (300, 192)
        grid.step()
        self.assertEqual(self.take(), [("area", "body_entered", static), ("area", "body_exited", body)])

    def test_mask(self):
        grid = self.grid
        area = self.watch(grid.add(Area(RectShape(0, 0, 64, 64), position=(160, 160), collision_mask=2)))
        body = grid.add(Body(box(8), position=(192, 192)))
        grid.step()
        self.assertEqual(self.take(), [])
        body.collision_layer = 2
        grid.step()
        self.assertEqual(self.take(), [("area", "body_entered", body)])
        area.collision_mask = 1
        grid.step()
        self.assertEqual(self.take(), [("area", "body_exited", body)])

    def test_area_area_and_monitorable(self):
        grid = self.grid
        hurtbox = self.watch(grid.add(Area(RectShape(0, 0, 32, 32), position=(160, 160))), "hurt")
        hitbox = grid.add(Area(RectShape(0, 0, 8, 8), position=(400, 400), monitoring=False))
        grid.step()
        hitbox.position = (170, 170)
        grid.step()
        self.assertEqual(self.take(), [("hurt", "area_entered", hitbox)])
        self.assertEqual(hurtbox.get_overlapping_areas(), [hitbox])
        hitbox.monitorable = False
        grid.step()
        self.assertEqual(self.take(), [("hurt", "area_exited", hitbox)])
        hitbox.monitorable = True
        grid.step()
        self.assertEqual(self.take(), [("hurt", "area_entered", hitbox)])
        self.assertTrue(hurtbox.overlaps_area(hitbox))
        # The hitbox isn't monitoring, so it detects nothing itself.
        self.assertEqual(hitbox.get_overlapping_areas(), [])

    def test_monitoring_toggle(self):
        grid = self.grid
        area = self.watch(grid.add(Area(RectShape(0, 0, 64, 64), position=(160, 160))))
        body = grid.add(Body(box(8), position=(192, 192)))
        grid.step()
        self.take()
        area.monitoring = False
        grid.step()
        self.assertEqual(self.take(), [("area", "body_exited", body)])
        area.monitoring = True
        grid.step()
        self.assertEqual(self.take(), [("area", "body_entered", body)])

    def test_circle_area_and_disconnect(self):
        grid = self.grid
        area = grid.add(Area(CircleShape(20), position=(200, 200)))
        seen = []
        callback = seen.append
        area.body_entered.connect(callback)
        area.body_entered.connect(callback)  # connecting twice is a no-op
        self.assertTrue(area.body_entered.is_connected(callback))
        corner = grid.add(Body(box(8), position=(219, 219)))  # its corner (215, 215) is 21.2 away
        grid.step()
        self.assertEqual(seen, [])
        corner.position = (214, 214)
        grid.step()
        self.assertEqual(seen, [corner])
        area.body_entered.disconnect(callback)
        grid.add(Body(box(8), position=(200, 200)))
        grid.step()
        self.assertEqual(seen, [corner])

    def test_many_bodies(self):
        grid = self.grid
        area = grid.add(Area(RectShape(0, 0, 100, 100), position=(100, 100)))
        bodies = [grid.add(Body(box(4), position=(110 + i * 8, 150))) for i in range(10)]
        grid.step()
        self.assertEqual(area.get_overlapping_bodies(), bodies)


class TestRaycast(Case):

    def test_terrain_each_direction(self):
        grid = make_grid(".....", ".....", "..#..", ".....", ".....")
        cases = [
            ((0, 40), (80, 40), (32, 40), (-1, 0)),
            ((80, 40), (0, 40), (48, 40), (1, 0)),
            ((40, 0), (40, 80), (40, 32), (0, -1)),
            ((40, 80), (40, 0), (40, 48), (0, 1)),
        ]
        for start, end, point, normal in cases:
            hit = grid.raycast(start, end)
            self.assertIsNotNone(hit, start)
            self.assertNear(hit.position.x, point[0])
            self.assertNear(hit.position.y, point[1])
            self.assertEqual(hit.normal, Vector2(*normal))
            self.assertIs(hit.collider, grid)
            self.assertEqual(hit.cell, Vector2i(2, 2))
            self.assertEqual(hit["position"], hit.position)

    def test_diagonal_and_misses(self):
        grid = make_grid(".....", ".....", "..#..", ".....", ".....")
        hit = grid.raycast((0, 0), (80, 80))
        self.assertNear(hit.position.x, 32)
        self.assertNear(hit.position.y, 32)
        self.assertIsNone(grid.raycast((0, 0), (80, 0)))
        self.assertIsNone(grid.raycast((0, 40), (30, 40)))
        self.assertIsNone(grid.raycast((0, 40), (80, 40), collision_mask=2))
        self.assertIsNone(grid.raycast((40, 40), (40, 40)))

    def test_hit_from_inside(self):
        grid = make_grid("......", "..##..", "......", "....#.")
        # Starting inside the wall: ignore it and hit nothing...
        self.assertIsNone(grid.raycast((40, 24), (90, 24)))
        # ...but a later wall still counts.
        hit = grid.raycast((40, 24), (72, 56))
        self.assertIsNotNone(hit)
        self.assertEqual(hit.cell, Vector2i(4, 3))
        hit = grid.raycast((40, 24), (90, 24), hit_from_inside=True)
        self.assertEqual(hit.position, Vector2(40, 24))
        self.assertEqual(hit.normal, Vector2(0, 0))

    def test_outside(self):
        grid = open_grid(5, 5, outside=WALL)
        hit = grid.raycast((40, 40), (200, 40))
        self.assertNear(hit.position.x, 80)
        self.assertEqual(hit.normal, Vector2(-1, 0))
        self.assertIsNone(hit.cell)
        # Starting outside (inside the solid): enter the grid, then hit the far side.
        hit = grid.raycast((-50, 40), (200, 40))
        self.assertNear(hit.position.x, 80)
        self.assertEqual(grid.raycast((-50, 40), (200, 40), hit_from_inside=True).position, Vector2(-50, 40))
        self.assertIsNone(open_grid(5, 5).raycast((40, 40), (200, 40)))
        # Entering from an open outside into a wall cell at the edge.
        edge = make_grid("#....", ".....")
        hit = edge.raycast((-30, 8), (40, 8))
        self.assertNear(hit.position.x, 0)
        self.assertEqual(hit.normal, Vector2(-1, 0))

    def test_objects(self):
        grid = open_grid(40, 10)
        rect = grid.add(StaticBody(RectShape(0, 0, 10, 10), position=(100, 35)))
        circle = grid.add(Body(CircleShape(5), position=(200, 40)))
        hit = grid.raycast((0, 40), (600, 40))
        self.assertIs(hit.collider, rect)
        self.assertNear(hit.position.x, 100)
        self.assertEqual(hit.collider_shape, rect.shapes[0])
        hit = grid.raycast((0, 40), (600, 40), exclude=[rect])
        self.assertIs(hit.collider, circle)
        self.assertNear(hit.position.x, 195)
        self.assertNear(hit.normal.x, -1)
        hit = grid.raycast((300, 40), (0, 40))
        self.assertIs(hit.collider, circle)
        self.assertNear(hit.position.x, 205)
        self.assertIsNone(grid.raycast((0, 40), (600, 40), collision_mask=2))
        self.assertIsNone(grid.raycast((0, 40), (600, 40), collide_with_bodies=False))

    def test_nearest_of_terrain_and_objects(self):
        grid = make_grid(*(["..........#........."] * 4))
        grid.add(StaticBody(RectShape(0, 0, 4, 64), position=(250, 0)))
        self.assertIs(grid.raycast((0, 30), (320, 30)).collider, grid)
        self.assertNear(grid.raycast((320, 30), (0, 30)).position.x, 254)

    def test_areas(self):
        grid = open_grid(40, 10)
        area = grid.add(Area(RectShape(0, 0, 20, 20), position=(100, 30)))
        self.assertIsNone(grid.raycast((0, 40), (600, 40)))
        hit = grid.raycast((0, 40), (600, 40), collide_with_areas=True)
        self.assertIs(hit.collider, area)
        hit = grid.raycast((110, 40), (600, 40), collide_with_areas=True, hit_from_inside=True)
        self.assertEqual(hit.normal, Vector2(0, 0))
        self.assertIsNone(grid.raycast((110, 40), (600, 40), collide_with_areas=True))

    def test_long_ray_across_buckets(self):
        grid = open_grid(200, 200)
        target = grid.add(StaticBody(CircleShape(3), position=(3000, 2900)))
        hit = grid.raycast((10, 20), (3000 * 1.1 - 1, 2900 * 1.1 - 20 * 0.1 - 1))
        self.assertIsNotNone(hit)
        self.assertIs(hit.collider, target)


if __name__ == "__main__":
    unittest.main()
