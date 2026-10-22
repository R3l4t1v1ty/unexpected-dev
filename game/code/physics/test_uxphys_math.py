"""Tests for uxphys_math. Run from this folder:
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
"""

import math
import pickle
import unittest

import uxphys_math as m
from uxphys_math import Vector2, Vector2i, Rect2, Rect2i, Transform2D


class VecCase(unittest.TestCase):

    def assertVec(self, v, x, y, places=6):
        self.assertAlmostEqual(v.x, x, places=places, msg=repr(v))
        self.assertAlmostEqual(v.y, y, places=places, msg=repr(v))


class TestGlobals(unittest.TestCase):

    def test_sign_round(self):
        self.assertEqual(m.sign(-3), -1)
        self.assertEqual(m.sign(0.0), 0)
        self.assertEqual(m.roundf(2.5), 3.0)
        self.assertEqual(m.roundf(-2.5), -3.0)
        self.assertEqual(m.roundi(0.5), 1)

    def test_clamp_snapped_wrap(self):
        self.assertEqual(m.clamp(5, 0, 3), 3)
        self.assertEqual(m.snapped(13, 8), 16)
        self.assertEqual(m.snapped(11, 8), 8)
        self.assertEqual(m.snapped(7.3, 0), 7.3)
        self.assertEqual(m.wrapi(-1, 0, 4), 3)
        self.assertAlmostEqual(m.wrapf(5.5, 0.0, 2.0), 1.5)
        self.assertEqual(m.wrap(3, 3, 3), 3)
        self.assertAlmostEqual(m.pingpong(3.0, 2.0), 1.0)
        self.assertAlmostEqual(m.pingpong(5.0, 2.0), 1.0)
        self.assertEqual(m.pingpong(1.0, 0.0), 0.0)

    def test_interpolation(self):
        self.assertEqual(m.lerp(0.0, 10.0, 0.25), 2.5)
        self.assertEqual(m.inverse_lerp(0.0, 10.0, 2.5), 0.25)
        self.assertEqual(m.remap(5.0, 0.0, 10.0, 100.0, 200.0), 150.0)
        self.assertEqual(m.smoothstep(0.0, 1.0, 0.5), 0.5)
        self.assertEqual(m.smoothstep(0.0, 1.0, -1.0), 0.0)
        # Equal edges: a step (Godot 4.3+).
        self.assertEqual(m.smoothstep(1.0, 1.0, 0.5), 0.0)
        self.assertEqual(m.smoothstep(1.0, 1.0, 2.0), 1.0)
        self.assertEqual(m.move_toward(0.0, 10.0, 3.0), 3.0)
        self.assertEqual(m.move_toward(9.0, 10.0, 3.0), 10.0)
        self.assertEqual(m.move_toward(0.0, -10.0, 3.0), -3.0)
        self.assertAlmostEqual(m.ease(0.5, 2.0), 0.25)
        self.assertAlmostEqual(m.ease(0.5, -2.0), 0.5)
        self.assertEqual(m.ease(0.5, 0.0), 0.0)
        self.assertAlmostEqual(m.cubic_interpolate(0.0, 1.0, 0.0, 1.0, 0.5), 0.5)
        self.assertAlmostEqual(m.bezier_interpolate(0.0, 0.0, 1.0, 1.0, 0.5), 0.5)

    def test_angles(self):
        self.assertAlmostEqual(m.angle_difference(0.0, math.pi / 2), math.pi / 2)
        self.assertAlmostEqual(m.angle_difference(0.1, math.tau - 0.1), -0.2)
        self.assertAlmostEqual(m.angle_difference(math.tau - 0.1, 0.1), 0.2)
        self.assertAlmostEqual(m.lerp_angle(math.tau - 0.1, 0.1, 0.5), math.tau)
        self.assertAlmostEqual(m.rotate_toward(0.0, 1.0, 0.25), 0.25)
        self.assertAlmostEqual(m.rotate_toward(0.0, 1.0, 5.0), 1.0)
        self.assertAlmostEqual(m.rotate_toward(0.0, -1.0, 0.25), -0.25)


class TestVector2(VecCase):

    def test_construct(self):
        self.assertVec(Vector2(), 0, 0)
        self.assertVec(Vector2((3, 4)), 3, 4)
        self.assertVec(Vector2(Vector2i(3, 4)), 3, 4)
        self.assertIsInstance(Vector2(1, 2).x, float)
        x, y = Vector2(5, 6)
        self.assertEqual((x, y), (5.0, 6.0))
        self.assertEqual(Vector2(1, 2)[1], 2.0)

    def test_arithmetic(self):
        a = Vector2(1, 2)
        self.assertEqual(a + Vector2(3, 4), Vector2(4, 6))
        self.assertEqual(a - 1, Vector2(0, 1))
        self.assertEqual(2 * a, Vector2(2, 4))
        self.assertEqual(a * Vector2(2, 3), Vector2(2, 6))
        self.assertEqual(a / 2, Vector2(0.5, 1))
        self.assertEqual(-a, Vector2(-1, -2))
        self.assertEqual(Vector2(-7, 7) // 4, Vector2(-2, 1))
        self.assertEqual(Vector2(-1, 5) % 4, Vector2(3, 1))
        self.assertEqual(a + Vector2i(1, 1), Vector2(2, 3))

    def test_reference_semantics(self):
        a = Vector2(1, 1)
        b = a
        b += Vector2(1, 0)
        self.assertEqual(a, Vector2(1, 1))
        zero = Vector2.ZERO
        zero.x = 5
        self.assertEqual(Vector2.ZERO, Vector2(0, 0))

    def test_compare_hash(self):
        self.assertTrue(Vector2(1, 2) < Vector2(1, 3))
        self.assertTrue(Vector2(0, 9) < Vector2(1, 0))
        self.assertNotEqual(Vector2(1, 2), Vector2i(1, 2))
        self.assertEqual(len({Vector2(1, 2), Vector2(1, 2)}), 1)
        self.assertFalse(Vector2())
        self.assertTrue(Vector2(0, 1))

    def test_length(self):
        v = Vector2(3, 4)
        self.assertEqual(v.length(), 5)
        self.assertEqual(v.length_squared(), 25)
        self.assertEqual(Vector2().distance_to(v), 5)
        self.assertEqual(Vector2().distance_squared_to(v), 25)
        self.assertVec(v.normalized(), 0.6, 0.8)
        self.assertTrue(v.normalized().is_normalized())
        self.assertEqual(Vector2().normalized(), Vector2())
        self.assertVec(v.limit_length(2.5), 1.5, 2.0)
        self.assertVec(v.limit_length(10), 3, 4)
        self.assertVec(Vector2().direction_to(Vector2(0, 5)), 0, 1)

    def test_rounding(self):
        v = Vector2(1.5, -1.5)
        self.assertEqual(round(v), Vector2(2, -2))
        self.assertEqual(v.round(), Vector2(2, -2))
        self.assertEqual(math.floor(v), Vector2(1, -2))
        self.assertEqual(v.ceil(), Vector2(2, -1))
        self.assertEqual(abs(v), Vector2(1.5, 1.5))
        self.assertEqual(v.abs(), Vector2(1.5, 1.5))
        self.assertEqual(v.sign(), Vector2(1, -1))

    def test_componentwise(self):
        v = Vector2(5, -5)
        self.assertEqual(v.clamp(Vector2(0, 0), Vector2(3, 3)), Vector2(3, 0))
        self.assertEqual(v.clampf(-1, 1), Vector2(1, -1))
        self.assertEqual(Vector2(13, 11).snapped(8), Vector2(16, 8))
        self.assertEqual(Vector2(13, 11).snapped(Vector2(8, 1)), Vector2(16, 11))
        self.assertEqual(v.min(0), Vector2(0, -5))
        self.assertEqual(v.max(Vector2(6, 0)), Vector2(6, 0))
        self.assertEqual(Vector2(1, 2).max_axis_index(), Vector2.AXIS_Y)
        self.assertEqual(Vector2(1, 2).min_axis_index(), Vector2.AXIS_X)

    def test_angles(self):
        self.assertAlmostEqual(Vector2(0, 1).angle(), math.pi / 2)
        self.assertAlmostEqual(Vector2(1, 0).angle_to(Vector2(0, 1)), math.pi / 2)
        self.assertAlmostEqual(Vector2(1, 1).angle_to_point(Vector2(1, 3)), math.pi / 2)
        self.assertVec(Vector2(1, 0).rotated(math.pi / 2), 0, 1)
        self.assertVec(Vector2.from_angle(math.pi), -1, 0)
        self.assertEqual(Vector2(1, 2).orthogonal(), Vector2(2, -1))

    def test_products(self):
        a, b = Vector2(1, 2), Vector2(3, 4)
        self.assertEqual(a.dot(b), 11)
        self.assertEqual(a.cross(b), -2)
        self.assertVec(Vector2(2, 2).project(Vector2(1, 0)), 2, 0)
        n = Vector2(0, -1)
        self.assertVec(Vector2(3, 4).slide(n), 3, 0)
        self.assertVec(Vector2(3, 4).bounce(n), 3, -4)
        self.assertVec(Vector2(3, 4).reflect(Vector2(1, 0)), 3, -4)

    def test_interpolation(self):
        self.assertVec(Vector2(0, 0).lerp(Vector2(10, 20), 0.5), 5, 10)
        self.assertVec(Vector2(1, 0).slerp(Vector2(0, 2), 0.5), math.sqrt(0.5) * 1.5, math.sqrt(0.5) * 1.5)
        self.assertVec(Vector2().slerp(Vector2(2, 0), 0.5), 1, 0)
        self.assertVec(Vector2(0, 0).move_toward(Vector2(10, 0), 3), 3, 0)
        self.assertVec(Vector2(0, 0).move_toward(Vector2(1, 0), 3), 1, 0)
        self.assertVec(m.lerp(Vector2(0, 0), Vector2(4, 8), 0.25), 1, 2)
        self.assertVec(Vector2(0, 0).bezier_interpolate(Vector2(0, 0), Vector2(1, 1), Vector2(1, 1), 0.5), 0.5, 0.5)
        self.assertVec(Vector2(0, 0).cubic_interpolate(Vector2(1, 1), Vector2(0, 0), Vector2(1, 1), 0.5), 0.5, 0.5)

    def test_checks(self):
        self.assertTrue(Vector2(1, 1).is_equal_approx(Vector2(1.000001, 1)))
        self.assertTrue(Vector2(0.000001, 0).is_zero_approx())
        self.assertFalse(Vector2(math.inf, 0).is_finite())

    def test_pickle(self):
        v = pickle.loads(pickle.dumps(Vector2(1.5, 2)))
        self.assertEqual(v, Vector2(1.5, 2))
        self.assertIsInstance(v, Vector2)


class TestVector2i(VecCase):

    def test_int_rules(self):
        v = Vector2i(7, -7)
        self.assertEqual(v // 2, Vector2i(3, -4))
        self.assertEqual(v % 3, Vector2i(1, 2))
        self.assertIsInstance(v / 2, Vector2)
        self.assertEqual(v / 2, Vector2(3.5, -3.5))
        self.assertIsInstance(v * 0.5, Vector2)
        self.assertIsInstance(v * 2, Vector2i)
        self.assertIsInstance(v + Vector2(1, 1), Vector2)
        self.assertIsInstance(Vector2(1, 1) + v, Vector2)
        self.assertEqual(Vector2i(Vector2(2.9, -2.9)), Vector2i(2, -2))

    def test_dict_key(self):
        tiles = {Vector2i(3, 4): "a"}
        self.assertEqual(tiles[Vector2i(3, 4)], "a")
        self.assertEqual(Vector2i(3, 4).length(), 5)
        self.assertEqual(Vector2i(5, -5).clampi(-1, 1), Vector2i(1, -1))
        self.assertEqual(Vector2i.MAX.x, 2 ** 31 - 1)


class TestRect2(VecCase):

    def test_construct(self):
        r = Rect2(1, 2, 3, 4)
        self.assertEqual(tuple(r), (1, 2, 3, 4))
        self.assertEqual(Rect2(Vector2(1, 2), Vector2(3, 4)), r)
        self.assertEqual(Rect2((1, 2, 3, 4)), r)
        self.assertEqual(r.end, Vector2(4, 6))
        self.assertEqual(r.center, Vector2(2.5, 4))
        self.assertEqual(r.get_center(), Vector2(2.5, 4))
        self.assertEqual(r.area, 12)
        self.assertEqual(Rect2.from_points([(1, 5), (3, 2)]), Rect2(1, 2, 2, 3))
        r.end = (10, 10)
        self.assertEqual(r.size, Vector2(9, 8))

    def test_has_point(self):
        r = Rect2(0, 0, 10, 10)
        self.assertIn(Vector2(0, 0), r)
        self.assertIn((5, 5), r)
        self.assertNotIn(Vector2(10, 5), r)
        self.assertNotIn(Vector2(-0.1, 5), r)

    def test_intersects(self):
        a = Rect2(0, 0, 10, 10)
        self.assertTrue(a.intersects(Rect2(5, 5, 10, 10)))
        self.assertFalse(a.intersects(Rect2(10, 0, 5, 5)))
        self.assertTrue(a.intersects(Rect2(10, 0, 5, 5), include_borders=True))
        self.assertEqual(a & Rect2(5, 5, 10, 10), Rect2(5, 5, 5, 5))
        self.assertFalse(a & Rect2(20, 20, 1, 1))
        self.assertEqual(a | Rect2(20, 20, 1, 1), Rect2(0, 0, 21, 21))
        self.assertTrue(a.encloses(Rect2(1, 1, 9, 9)))
        self.assertFalse(a.encloses(Rect2(1, 1, 10, 9)))

    def test_grow_expand(self):
        a = Rect2(0, 0, 10, 10)
        self.assertEqual(a.grow(2), Rect2(-2, -2, 14, 14))
        self.assertEqual(a.grow_side(Rect2.SIDE_RIGHT, 5), Rect2(0, 0, 15, 10))
        self.assertEqual(a.grow_individual(1, 2, 3, 4), Rect2(-1, -2, 14, 16))
        self.assertEqual(a.expand((-5, 20)), Rect2(-5, 0, 15, 20))
        self.assertEqual(abs(Rect2(10, 10, -4, -6)), Rect2(6, 4, 4, 6))
        self.assertTrue(a.has_area())
        self.assertFalse(Rect2(0, 0, 0, 5).has_area())

    def test_intersects_segment(self):
        r = Rect2(10, 10, 10, 10)
        hit = r.intersects_segment((0, 15), (30, 15))
        self.assertIsNotNone(hit)
        self.assertVec(hit[0], 10, 15)
        self.assertVec(hit[1], -1, 0)
        hit = r.intersects_segment((15, 30), (15, 0))
        self.assertVec(hit[0], 15, 20)
        self.assertVec(hit[1], 0, 1)
        self.assertIsNone(r.intersects_segment((0, 0), (30, 0)))
        self.assertIsNone(r.intersects_segment((0, 15), (5, 15)))
        inside = r.intersects_segment((15, 15), (40, 15))
        self.assertVec(inside[0], 15, 15)
        self.assertVec(inside[1], 0, 0)

    def test_support_approx(self):
        r = Rect2(0, 0, 4, 2)
        self.assertEqual(r.get_support((1, -1)), Vector2(4, 0))
        self.assertTrue(r.is_equal_approx(Rect2(0, 0, 4.000001, 2)))

    def test_pickle(self):
        r = pickle.loads(pickle.dumps(Rect2(1, 2, 3, 4)))
        self.assertEqual(r, Rect2(1, 2, 3, 4))


class TestRect2i(unittest.TestCase):

    def test_rect2i(self):
        r = Rect2i(0, 0, 5, 5)
        self.assertEqual(r.center, Vector2i(2, 2))
        self.assertIsInstance(r.position, Vector2i)
        self.assertEqual(list(Rect2i(1, 1, 2, 2).cells()), [Vector2i(1, 1), Vector2i(2, 1), Vector2i(1, 2), Vector2i(2, 2)])
        self.assertEqual(Rect2i(Rect2(1.7, 2.2, 3.9, 4.1)), Rect2i(1, 2, 3, 4))
        self.assertEqual(r & Rect2i(3, 3, 5, 5), Rect2i(3, 3, 2, 2))


class TestTransform2D(VecCase):

    def test_constructors(self):
        t = Transform2D()
        self.assertEqual(t, Transform2D.IDENTITY)
        t = Transform2D(math.pi / 2, Vector2(10, 0))
        self.assertVec(t.x, 0, 1)
        self.assertVec(t.y, -1, 0)
        self.assertVec(t.origin, 10, 0)
        t = Transform2D(0.5, Vector2(2, 3), 0.25, Vector2(1, 1))
        self.assertAlmostEqual(t.rotation, 0.5)
        self.assertVec(t.scale, 2, 3)
        self.assertAlmostEqual(t.skew, 0.25)
        self.assertEqual(Transform2D(Vector2(1, 0), Vector2(0, 1), Vector2(5, 6)).origin, Vector2(5, 6))

    def test_xform(self):
        t = Transform2D(math.pi / 2, Vector2(10, 0))
        p = t * Vector2(1, 0)
        self.assertVec(p, 10, 1)
        self.assertVec(p * t, 1, 0)
        self.assertVec(t @ Vector2(1, 0), 10, 1)
        self.assertVec(t.basis_xform(Vector2(1, 0)), 0, 1)
        r = t * Rect2(0, 0, 2, 1)
        self.assertTrue(r.is_equal_approx(Rect2(9, 0, 1, 2)))

    def test_compose_inverse(self):
        a = Transform2D(0.3, Vector2(2, 0.5), 0.1, Vector2(4, -2))
        b = Transform2D(-1.1, Vector2(7, 3))
        p = Vector2(3, 5)
        self.assertTrue((a * b * p).is_equal_approx(a * (b * p)))
        self.assertTrue((a.affine_inverse() * (a * p)).is_equal_approx(p))
        self.assertTrue((b.inverse() * (b * p)).is_equal_approx(p))
        self.assertTrue((a * a.affine_inverse()).is_equal_approx(Transform2D()))

    def test_derived(self):
        t = Transform2D(0.0, Vector2(5, 5))
        self.assertVec(t.rotated(math.pi / 2).origin, -5, 5)
        self.assertVec(t.rotated_local(math.pi / 2).origin, 5, 5)
        self.assertVec(t.scaled(Vector2(2, 3)).origin, 10, 15)
        self.assertVec(t.scaled_local(2).origin, 5, 5)
        self.assertVec(t.translated(Vector2(1, 1)).origin, 6, 6)
        self.assertVec(Transform2D(math.pi / 2, Vector2()).translated_local(Vector2(1, 0)).origin, 0, 1)
        look = t.looking_at(Vector2(5, 10))
        self.assertAlmostEqual(look.rotation, math.pi / 2)
        mid = Transform2D(0.0, Vector2()).interpolate_with(Transform2D(1.0, Vector2(10, 0)), 0.5)
        self.assertAlmostEqual(mid.rotation, 0.5)
        self.assertVec(mid.origin, 5, 0)
        skewed = Transform2D(0.3, Vector2(2, 1), 0.2, Vector2())
        ortho = skewed.orthonormalized()
        self.assertAlmostEqual(ortho.x.length(), 1)
        self.assertAlmostEqual(ortho.x.dot(ortho.y), 0)
        self.assertTrue(Transform2D(0.4, Vector2()).is_conformal())
        self.assertFalse(skewed.is_conformal())

    def test_set_properties(self):
        t = Transform2D(0.0, Vector2(2, 3), 0.0, Vector2())
        t.rotation = 1.0
        self.assertAlmostEqual(t.rotation, 1.0)
        self.assertVec(t.scale, 2, 3)
        t.scale = (4, 5)
        self.assertVec(t.scale, 4, 5)
        t.skew = 0.2
        self.assertAlmostEqual(t.skew, 0.2)
        self.assertAlmostEqual(Transform2D.FLIP_X.scale.y, -1)

    def test_matrix_values_pickle(self):
        t = Transform2D(0.0, Vector2(3, 4))
        self.assertEqual(t.matrix_values()[3], 3)
        self.assertEqual(t.matrix_values()[7], 4)
        self.assertEqual(pickle.loads(pickle.dumps(t)), t)


if __name__ == "__main__":
    unittest.main()
