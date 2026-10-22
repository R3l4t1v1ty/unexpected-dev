"""Godot 4.4's 2D math in plain Python: Vector2, Vector2i, Rect2, Rect2i,
Transform2D, plus the @GlobalScope helpers Python lacks (lerp, move_toward...).

    import uxphys_math as m
    v = m.Vector2(3, 4).normalized()
    speed = m.move_toward(speed, max_speed, accel * delta)

Python protocols stand in for some Godot helpers:
    abs(v)  round(v)  math.floor(v)  math.ceil(v)  v % 3  v // 16
    x, y = v   tuple(v)   v[0]   Vector2((10, 20))   point in rect
The Godot method names work too (v.abs(), v.floor(), rect.get_center()...).

Reference semantics: `a = b` shares the vector. Arithmetic returns a new
vector and `a += b` rebinds `a`, so that's safe, but `a.x = 3` changes every
name bound to it: call .copy() first if you need an independent vector.
Constants (Vector2.ZERO...) are fresh on every access, so they can't be
corrupted that way.

No Ren'Py imports: this runs under plain python3 for the tests.
"""

import math
import operator

__all__ = [
    "Vector2", "Vector2i", "Rect2", "Rect2i", "Transform2D",
    "CMP_EPSILON", "UNIT_EPSILON",
    "sign", "signf", "signi", "roundf", "roundi",
    "is_equal_approx", "is_zero_approx",
    "clamp", "clampf", "clampi", "snapped", "snappedf", "snappedi",
    "wrap", "wrapf", "wrapi", "fposmod", "posmod", "pingpong",
    "lerp", "lerpf", "inverse_lerp", "remap", "smoothstep", "move_toward", "ease",
    "cubic_interpolate", "cubic_interpolate_in_time",
    "bezier_interpolate", "bezier_derivative",
    "angle_difference", "lerp_angle", "rotate_toward",
    "cubic_interpolate_angle", "cubic_interpolate_angle_in_time",
]

CMP_EPSILON = 0.00001
# Godot uses 0.00001 when built with PRECISE_MATH_CHECKS, 0.001 otherwise.
UNIT_EPSILON = 0.001


## @GlobalScope helpers (core/math/math_funcs.h). Python's math module covers
## the rest: math.pi/tau/inf, math.radians/degrees, math.floor/ceil, math.isclose.

def sign(x):
    """-1, 0 or 1. Unlike math.copysign, returns 0 for 0."""
    return (x > 0) - (x < 0)


def signf(x):
    return float(sign(x))


signi = sign


def roundf(x):
    """Rounds half away from zero, like Godot. Python's round() rounds half to even."""
    return math.copysign(math.floor(abs(x) + 0.5), x)


def roundi(x):
    return int(roundf(x))


def is_equal_approx(a, b):
    """Godot's tolerance: relative CMP_EPSILON, with CMP_EPSILON as the floor."""
    return math.isclose(a, b, rel_tol=CMP_EPSILON, abs_tol=CMP_EPSILON)


def is_zero_approx(x):
    return abs(x) < CMP_EPSILON


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


clampf = clamp
clampi = clamp


def snapped(value, step):
    """Snaps value to the nearest multiple of step (step 0 leaves it unchanged)."""
    if not step:
        return value
    return math.floor(value / step + 0.5) * step


snappedf = snapped


def snappedi(value, step):
    return int(snapped(value, step))


def wrap(value, min_value, max_value):
    """Wraps value into [min_value, max_value). Works for ints and floats."""
    span = max_value - min_value
    if not span:
        return min_value
    return min_value + (value - min_value) % span


wrapf = wrap
wrapi = wrap


def fposmod(x, y):
    """Python's % already takes the sign of y."""
    return x % y


posmod = fposmod


def _fract(x):
    return x - math.floor(x)


def pingpong(value, length):
    if not length:
        return 0.0
    return abs(_fract((value - length) / (length * 2.0)) * length * 2.0 - length)


def lerp(from_value, to_value, weight):
    """Works on numbers and on vectors."""
    return from_value + (to_value - from_value) * weight


lerpf = lerp


def inverse_lerp(from_value, to_value, value):
    return (value - from_value) / (to_value - from_value)


def remap(value, istart, istop, ostart, ostop):
    return lerp(ostart, ostop, inverse_lerp(istart, istop, value))


def smoothstep(from_value, to_value, x):
    """0 to 1 with a smooth start and end. Equal edges make it a step (Godot 4.3+)."""
    if is_equal_approx(from_value, to_value):
        if from_value <= to_value:
            return 0.0 if x <= from_value else 1.0
        return 1.0 if x <= to_value else 0.0
    s = clamp((x - from_value) / (to_value - from_value), 0.0, 1.0)
    return s * s * (3.0 - 2.0 * s)


def move_toward(from_value, to_value, delta):
    if abs(to_value - from_value) <= delta:
        return to_value
    return from_value + sign(to_value - from_value) * delta


def ease(x, curve):
    """curve > 1 eases in, 0 < curve < 1 eases out, curve < 0 eases in-out, 0 returns 0."""
    x = clamp(x, 0.0, 1.0)
    if curve > 0:
        if curve < 1.0:
            return 1.0 - (1.0 - x) ** (1.0 / curve)
        return x ** curve
    if curve < 0:
        if x < 0.5:
            return (x * 2.0) ** -curve * 0.5
        return (1.0 - (1.0 - (x - 0.5) * 2.0) ** -curve) * 0.5 + 0.5
    return 0.0


def cubic_interpolate(from_value, to_value, pre, post, weight):
    return 0.5 * (
        (from_value * 2.0)
        + (-pre + to_value) * weight
        + (2.0 * pre - 5.0 * from_value + 4.0 * to_value - post) * weight ** 2
        + (-pre + 3.0 * from_value - 3.0 * to_value + post) * weight ** 3
    )


def cubic_interpolate_in_time(from_value, to_value, pre, post, weight, to_t, pre_t, post_t):
    # Barry-Goldman method
    t = to_t * weight
    a1 = lerp(pre, from_value, (t - pre_t) / -pre_t if pre_t else 0.0)
    a2 = lerp(from_value, to_value, t / to_t if to_t else 0.5)
    a3 = lerp(to_value, post, (t - to_t) / (post_t - to_t) if post_t - to_t else 1.0)
    b1 = lerp(a1, a2, (t - pre_t) / (to_t - pre_t) if to_t - pre_t else 0.0)
    b2 = lerp(a2, a3, t / post_t if post_t else 1.0)
    return lerp(b1, b2, t / to_t if to_t else 0.5)


def bezier_interpolate(start, control_1, control_2, end, t):
    omt = 1.0 - t
    return start * omt ** 3 + control_1 * 3.0 * omt ** 2 * t + control_2 * 3.0 * omt * t ** 2 + end * t ** 3


def bezier_derivative(start, control_1, control_2, end, t):
    omt = 1.0 - t
    return (control_1 - start) * 3.0 * omt ** 2 + (control_2 - control_1) * 6.0 * omt * t + (end - control_2) * 3.0 * t ** 2


## Angles (radians)

def angle_difference(from_angle, to_angle):
    """Shortest signed turn from from_angle to to_angle, in [-pi, pi]."""
    difference = math.fmod(to_angle - from_angle, math.tau)
    return math.fmod(2.0 * difference, math.tau) - difference


def lerp_angle(from_angle, to_angle, weight):
    return from_angle + angle_difference(from_angle, to_angle) * weight


def rotate_toward(from_angle, to_angle, delta):
    difference = angle_difference(from_angle, to_angle)
    abs_difference = abs(difference)
    # When delta < 0, move no further than pi radians away from to_angle.
    return from_angle + clamp(delta, abs_difference - math.pi, abs_difference) * (1.0 if difference >= 0.0 else -1.0)


def _unwrap_angles(from_angle, to_angle, pre, post):
    """Rewrites the angles so each is the shortest turn from the one before it."""
    from_rot = math.fmod(from_angle, math.tau)
    pre_rot = from_rot + angle_difference(from_rot, pre)
    to_rot = from_rot + angle_difference(from_rot, to_angle)
    post_rot = to_rot + angle_difference(to_rot, post)
    return from_rot, to_rot, pre_rot, post_rot


def cubic_interpolate_angle(from_angle, to_angle, pre, post, weight):
    from_rot, to_rot, pre_rot, post_rot = _unwrap_angles(from_angle, to_angle, pre, post)
    return cubic_interpolate(from_rot, to_rot, pre_rot, post_rot, weight)


def cubic_interpolate_angle_in_time(from_angle, to_angle, pre, post, weight, to_t, pre_t, post_t):
    from_rot, to_rot, pre_rot, post_rot = _unwrap_angles(from_angle, to_angle, pre, post)
    return cubic_interpolate_in_time(from_rot, to_rot, pre_rot, post_rot, weight, to_t, pre_t, post_t)


## Shared vector machinery

class _Constant(object):
    """Class attribute that hands out a fresh instance on each access, so
    constants like Vector2.ZERO can't be corrupted by mutation."""

    __slots__ = ("args",)

    def __init__(self, *args):
        self.args = args

    def __get__(self, instance, owner):
        return owner(*self.args)


def _xy(value):
    """(x, y) of a vector, or a number broadcast to both components."""
    if isinstance(value, (int, float)):
        return value, value
    if isinstance(value, _VectorBase):
        return value.x, value.y
    raise TypeError("expected a vector or a number, got %s" % type(value).__name__)


def _vector_compare(op):
    """Exact, lexicographic (x first, then y) comparison like Godot's.
    Only vectors of the same type compare; Vector2 never equals Vector2i."""
    def method(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return op((self.x, self.y), (other.x, other.y))
    return method


class _VectorBase(object):
    """Shared by Vector2 and Vector2i. Subclasses set _cast to float or int."""

    __slots__ = ("x", "y")

    AXIS_X = 0
    AXIS_Y = 1

    def __init__(self, x=0, y=0):
        try:
            self.x = self._cast(x)
            self.y = self._cast(y)
        except TypeError:
            # Copy from another vector or an (x, y) sequence.
            self.x = self._cast(x[0])
            self.y = self._cast(x[1])

    def copy(self):
        return type(self)(self.x, self.y)

    ## Python protocol

    def __reduce__(self):
        return (type(self), (self.x, self.y))

    def __repr__(self):
        return "%s(%r, %r)" % (type(self).__name__, self.x, self.y)

    def __str__(self):
        return "(%r, %r)" % (self.x, self.y)

    def __iter__(self):
        return iter((self.x, self.y))

    def __len__(self):
        return 2

    def __getitem__(self, axis):
        return (self.x, self.y)[axis]

    def __setitem__(self, axis, value):
        setattr(self, ("x", "y")[axis], self._cast(value))

    def __hash__(self):
        return hash((self.x, self.y))

    def __bool__(self):
        return bool(self.x or self.y)

    __eq__ = _vector_compare(operator.eq)
    __ne__ = _vector_compare(operator.ne)
    __lt__ = _vector_compare(operator.lt)
    __le__ = _vector_compare(operator.le)
    __gt__ = _vector_compare(operator.gt)
    __ge__ = _vector_compare(operator.ge)

    def __neg__(self):
        return type(self)(-self.x, -self.y)

    def __pos__(self):
        return self.copy()

    def __abs__(self):
        return type(self)(abs(self.x), abs(self.y))

    def abs(self):
        return type(self)(abs(self.x), abs(self.y))

    ## Length

    def length(self):
        return math.hypot(self.x, self.y)

    def length_squared(self):
        return self.x * self.x + self.y * self.y

    def distance_to(self, to):
        return math.hypot(to.x - self.x, to.y - self.y)

    def distance_squared_to(self, to):
        dx = to.x - self.x
        dy = to.y - self.y
        return dx * dx + dy * dy

    def aspect(self):
        return self.x / self.y

    ## Component-wise (each argument may be a vector or a number)

    def sign(self):
        return type(self)(sign(self.x), sign(self.y))

    def snapped(self, step):
        sx, sy = _xy(step)
        return type(self)(snapped(self.x, sx), snapped(self.y, sy))

    def clamp(self, min_value, max_value):
        lx, ly = _xy(min_value)
        hx, hy = _xy(max_value)
        return type(self)(clamp(self.x, lx, hx), clamp(self.y, ly, hy))

    def min(self, other):
        ox, oy = _xy(other)
        return type(self)(min(self.x, ox), min(self.y, oy))

    def max(self, other):
        ox, oy = _xy(other)
        return type(self)(max(self.x, ox), max(self.y, oy))

    def posmod(self, mod):
        return self % mod

    def posmodv(self, modv):
        return self % modv

    def min_axis_index(self):
        return self.AXIS_X if self.x < self.y else self.AXIS_Y

    def max_axis_index(self):
        return self.AXIS_Y if self.x < self.y else self.AXIS_X


def _vector2_op(op):
    """Forward and reflected Vector2 operators. The other operand can be any
    vector (a Vector2i is promoted) or a number (applied to both components)."""
    def forward(self, other):
        try:
            ox, oy = _xy(other)
        except TypeError:
            return NotImplemented
        return Vector2(op(self.x, ox), op(self.y, oy))

    def reflected(self, other):
        try:
            ox, oy = _xy(other)
        except TypeError:
            return NotImplemented
        return Vector2(op(ox, self.x), op(oy, self.y))

    return forward, reflected


## Vector2 (core/math/vector2.h)

class Vector2(_VectorBase):
    """A 2D vector of floats. Godot's snappedf/clampf/minf/maxf are the same as
    snapped/clamp/min/max here: every operand may be a vector or a number."""

    __slots__ = ()
    _cast = float

    @staticmethod
    def from_angle(angle):
        return Vector2(math.cos(angle), math.sin(angle))

    ## Operators

    __add__, __radd__ = _vector2_op(operator.add)
    __sub__, __rsub__ = _vector2_op(operator.sub)
    __mul__, __rmul__ = _vector2_op(operator.mul)
    __truediv__, __rtruediv__ = _vector2_op(operator.truediv)
    __floordiv__, __rfloordiv__ = _vector2_op(operator.floordiv)
    __mod__, __rmod__ = _vector2_op(operator.mod)

    def __round__(self, ndigits=None):
        """round(v) rounds half away from zero like Godot; round(v, n) uses Python's rounding."""
        if ndigits is None:
            return Vector2(roundf(self.x), roundf(self.y))
        return Vector2(round(self.x, ndigits), round(self.y, ndigits))

    def __floor__(self):
        return Vector2(math.floor(self.x), math.floor(self.y))

    def __ceil__(self):
        return Vector2(math.ceil(self.x), math.ceil(self.y))

    def __trunc__(self):
        return Vector2(math.trunc(self.x), math.trunc(self.y))

    def round(self):
        return Vector2(roundf(self.x), roundf(self.y))

    def floor(self):
        return Vector2(math.floor(self.x), math.floor(self.y))

    def ceil(self):
        return Vector2(math.ceil(self.x), math.ceil(self.y))

    snappedf = _VectorBase.snapped
    clampf = _VectorBase.clamp
    minf = _VectorBase.min
    maxf = _VectorBase.max

    ## Direction

    def normalized(self):
        l = self.length()
        if l:
            return Vector2(self.x / l, self.y / l)
        return self.copy()

    def is_normalized(self):
        # length_squared() avoids the sqrt and is more stringent.
        return math.isclose(self.length_squared(), 1.0, abs_tol=UNIT_EPSILON)

    def limit_length(self, length=1.0):
        l = self.length()
        if 0 < l and length < l:
            return self * (length / l)
        return self.copy()

    def direction_to(self, to):
        return (to - self).normalized()

    ## Angles (radians; y is down, so positive turns clockwise on screen)

    def angle(self):
        return math.atan2(self.y, self.x)

    def angle_to(self, to):
        return math.atan2(self.cross(to), self.dot(to))

    def angle_to_point(self, to):
        return math.atan2(to.y - self.y, to.x - self.x)

    def rotated(self, angle):
        sine = math.sin(angle)
        cosi = math.cos(angle)
        return Vector2(self.x * cosi - self.y * sine, self.x * sine + self.y * cosi)

    def orthogonal(self):
        return Vector2(self.y, -self.x)

    ## Products and projections

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def cross(self, other):
        return self.x * other.y - self.y * other.x

    def project(self, b):
        return b * (self.dot(b) / b.length_squared())

    def plane_project(self, d, vec):
        return vec - self * (self.dot(vec) - d)

    def slide(self, n):
        """Component of this vector along the line with normal n (n must be normalized)."""
        return self - n * self.dot(n)

    def bounce(self, n):
        return -self.reflect(n)

    def reflect(self, line):
        return line * (2.0 * self.dot(line)) - self

    ## Interpolation (the module-level versions work on vectors as-is)

    def lerp(self, to, weight):
        return self + (to - self) * weight

    def slerp(self, to, weight):
        start_length_sq = self.length_squared()
        end_length_sq = to.length_squared()
        if not start_length_sq or not end_length_sq:
            # Zero length vectors have no angle, so the best we can do is lerp.
            return self.lerp(to, weight)
        start_length = math.sqrt(start_length_sq)
        result_length = lerp(start_length, math.sqrt(end_length_sq), weight)
        return self.rotated(self.angle_to(to) * weight) * (result_length / start_length)

    def cubic_interpolate(self, b, pre_a, post_b, weight):
        return cubic_interpolate(self, b, pre_a, post_b, weight)

    def cubic_interpolate_in_time(self, b, pre_a, post_b, weight, b_t, pre_a_t, post_b_t):
        return cubic_interpolate_in_time(self, b, pre_a, post_b, weight, b_t, pre_a_t, post_b_t)

    def bezier_interpolate(self, control_1, control_2, end, t):
        return bezier_interpolate(self, control_1, control_2, end, t)

    def bezier_derivative(self, control_1, control_2, end, t):
        return bezier_derivative(self, control_1, control_2, end, t)

    def move_toward(self, to, delta):
        offset = to - self
        l = offset.length()
        if l <= delta or l < CMP_EPSILON:
            return Vector2(to.x, to.y)
        return self + offset * (delta / l)

    ## Checks

    def is_equal_approx(self, to):
        return is_equal_approx(self.x, to.x) and is_equal_approx(self.y, to.y)

    def is_zero_approx(self):
        return abs(self.x) < CMP_EPSILON and abs(self.y) < CMP_EPSILON

    def is_finite(self):
        return math.isfinite(self.x) and math.isfinite(self.y)


Vector2.ZERO = _Constant(0.0, 0.0)
Vector2.ONE = _Constant(1.0, 1.0)
Vector2.INF = _Constant(math.inf, math.inf)
Vector2.LEFT = _Constant(-1.0, 0.0)
Vector2.RIGHT = _Constant(1.0, 0.0)
Vector2.UP = _Constant(0.0, -1.0)
Vector2.DOWN = _Constant(0.0, 1.0)


## Vector2i (core/math/vector2i.h)

def _vector2i_op(op):
    """Forward and reflected Vector2i operators. Int operands keep the result a
    Vector2i and float operands promote it to Vector2. A Vector2 operand returns
    NotImplemented so Vector2's reflected operator promotes the result."""
    def forward(self, other):
        if isinstance(other, Vector2i):
            return Vector2i(op(self.x, other.x), op(self.y, other.y))
        if isinstance(other, int):
            return Vector2i(op(self.x, other), op(self.y, other))
        if isinstance(other, float):
            return op(Vector2(self.x, self.y), other)
        return NotImplemented

    def reflected(self, other):
        if isinstance(other, int):
            return Vector2i(op(other, self.x), op(other, self.y))
        if isinstance(other, float):
            return op(other, Vector2(self.x, self.y))
        return NotImplemented

    return forward, reflected


class Vector2i(_VectorBase):
    """A 2D vector of ints, for cells and pixels. Hashable, so it works as a
    dict key: `tiles[Vector2i(3, 4)]`.

    Follows Python's integer rules rather than C++'s:
        v // 2   v % 3    stay Vector2i (floor division, floor modulo)
        v / 2    v * 0.5  return a Vector2, like int / int returns a float
        v + Vector2(...)  returns a Vector2
    Vector2i(Vector2) truncates toward zero, as in Godot.
    """

    __slots__ = ()
    _cast = int

    __add__, __radd__ = _vector2i_op(operator.add)
    __sub__, __rsub__ = _vector2i_op(operator.sub)
    __mul__, __rmul__ = _vector2i_op(operator.mul)
    __floordiv__, __rfloordiv__ = _vector2i_op(operator.floordiv)
    __mod__, __rmod__ = _vector2i_op(operator.mod)

    def __truediv__(self, other):
        return Vector2(self.x, self.y) / other

    def __rtruediv__(self, other):
        return other / Vector2(self.x, self.y)

    snappedi = _VectorBase.snapped
    clampi = _VectorBase.clamp
    mini = _VectorBase.min
    maxi = _VectorBase.max


Vector2i.ZERO = _Constant(0, 0)
Vector2i.ONE = _Constant(1, 1)
Vector2i.MIN = _Constant(-2 ** 31, -2 ** 31)
Vector2i.MAX = _Constant(2 ** 31 - 1, 2 ** 31 - 1)
Vector2i.LEFT = _Constant(-1, 0)
Vector2i.RIGHT = _Constant(1, 0)
Vector2i.UP = _Constant(0, -1)
Vector2i.DOWN = _Constant(0, 1)


## Rect2 and Rect2i (core/math/rect2.h, rect2i.h)

class _RectBase(object):
    """Shared by Rect2 and Rect2i. Subclasses set _vector to Vector2 or Vector2i.

    Rect2(x, y, w, h), Rect2(position, size) and Rect2((x, y, w, h)) all work.

    Python protocols:
        point in rect      has_point
        a & b              intersection; an empty rect when they don't overlap,
                           so `if a & b:` reads as "if they overlap"
        a | b              merge
        abs(rect)  round(rect)
        x, y, w, h = rect  tuple(rect) is Ren'Py's (x, y, w, h) format

    Like Godot, most methods assume a non-negative size; use abs(rect) first.
    Assigning `rect.position = v` copies v; `rect.position.x = 3` edits in place.
    """

    __slots__ = ("_position", "_size")

    SIDE_LEFT = 0
    SIDE_TOP = 1
    SIDE_RIGHT = 2
    SIDE_BOTTOM = 3

    def __init__(self, *args):
        if len(args) == 2:
            self.position, self.size = args
            return
        if len(args) == 1:
            args = tuple(args[0])
        elif not args:
            args = (0, 0, 0, 0)
        x, y, w, h = args
        self._position = self._vector(x, y)
        self._size = self._vector(w, h)

    @classmethod
    def from_points(cls, points):
        """Smallest rect that contains every point (vectors or (x, y) pairs)."""
        xs, ys = zip(*points)
        left = min(xs)
        top = min(ys)
        return cls(left, top, max(xs) - left, max(ys) - top)

    def copy(self):
        return type(self)(self)

    ## Properties

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = self._vector(*value)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = self._vector(*value)

    @property
    def end(self):
        """Bottom-right corner. Setting it resizes the rect, keeping position."""
        return self._position + self._size

    @end.setter
    def end(self, value):
        self._size = self._vector(*value) - self._position

    @property
    def area(self):
        return self._size.x * self._size.y

    def get_area(self):
        return self._size.x * self._size.y

    def get_center(self):
        return self.center

    ## Python protocol

    def __reduce__(self):
        return (type(self), tuple(self))

    def __repr__(self):
        return "%s(%r, %r, %r, %r)" % ((type(self).__name__,) + tuple(self))

    def __str__(self):
        return "[P: %s, S: %s]" % (self._position, self._size)

    def __iter__(self):
        return iter((self._position.x, self._position.y, self._size.x, self._size.y))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._position == other._position and self._size == other._size

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else not result

    def __hash__(self):
        return hash(tuple(self))

    def __bool__(self):
        return bool(self._position or self._size)

    def __contains__(self, point):
        return self.has_point(point)

    def __and__(self, other):
        return self.intersection(other) if isinstance(other, type(self)) else NotImplemented

    def __or__(self, other):
        return self.merge(other) if isinstance(other, type(self)) else NotImplemented

    def __abs__(self):
        """Same rect with a non-negative size."""
        return type(self)(self._position + self._size.min(0), abs(self._size))

    def abs(self):
        return self.__abs__()

    ## Queries

    def has_area(self):
        return self._size.x > 0 and self._size.y > 0

    def has_point(self, point):
        """True if point is inside. The right and bottom edges are excluded."""
        px, py = point
        x, y, w, h = self
        return x <= px < x + w and y <= py < y + h

    def encloses(self, other):
        """True if other lies completely inside this rect."""
        x, y, w, h = self
        ox, oy, ow, oh = other
        return ox >= x and oy >= y and ox + ow <= x + w and oy + oh <= y + h

    def intersects(self, other, include_borders=False):
        """True if the rects overlap. Touching edges only count with include_borders."""
        x, y, w, h = self
        ox, oy, ow, oh = other
        if include_borders:
            return x <= ox + ow and ox <= x + w and y <= oy + oh and oy <= y + h
        return x < ox + ow and ox < x + w and y < oy + oh and oy < y + h

    ## New rects

    def intersection(self, other):
        """The overlapping area, or an empty rect if they don't intersect."""
        if not self.intersects(other):
            return type(self)()
        begin = self._position.max(other._position)
        return type(self)(begin, self.end.min(other.end) - begin)

    def merge(self, other):
        """Smallest rect containing both."""
        begin = self._position.min(other._position)
        return type(self)(begin, self.end.max(other.end) - begin)

    def expand(self, point):
        """Smallest rect containing this one and the point."""
        point = self._vector(*point)
        begin = self._position.min(point)
        return type(self)(begin, self.end.max(point) - begin)

    def grow(self, amount):
        return self.grow_individual(amount, amount, amount, amount)

    def grow_individual(self, left, top, right, bottom):
        x, y, w, h = self
        return type(self)(x - left, y - top, w + left + right, h + top + bottom)

    def grow_side(self, side, amount):
        """Grows one side; side is SIDE_LEFT / SIDE_TOP / SIDE_RIGHT / SIDE_BOTTOM."""
        amounts = [0, 0, 0, 0]
        amounts[side] = amount
        return self.grow_individual(*amounts)


class Rect2(_RectBase):
    """An axis-aligned rectangle of floats: position (top-left) and size."""

    __slots__ = ()
    _vector = Vector2

    @property
    def center(self):
        return self._position + self._size * 0.5

    def __round__(self, ndigits=None):
        return Rect2(round(self._position, ndigits), round(self._size, ndigits))

    def intersects_segment(self, from_point, to_point):
        """Where the segment from_point -> to_point first enters the rect.

        Returns (hit_position, hit_normal), or None if the segment misses.
        A segment starting inside hits at from_point with a zero normal.
        """
        fx, fy = from_point
        tx, ty = to_point
        segment = ((fx, tx), (fy, ty))
        position = (self._position.x, self._position.y)
        size = (self._size.x, self._size.y)
        t_min, t_max = 0.0, 1.0
        axis = 0
        normal_sign = 0.0

        for i in (0, 1):
            seg_from, seg_to = segment[i]
            box_begin = position[i]
            box_end = box_begin + size[i]

            if seg_from < seg_to:
                if seg_from > box_end or seg_to < box_begin:
                    return None
                length = seg_to - seg_from
                cmin = (box_begin - seg_from) / length if seg_from < box_begin else 0.0
                cmax = (box_end - seg_from) / length if seg_to > box_end else 1.0
                csign = -1.0
            else:
                if seg_to > box_end or seg_from < box_begin:
                    return None
                length = seg_to - seg_from
                cmin = (box_end - seg_from) / length if seg_from > box_end else 0.0
                cmax = (box_begin - seg_from) / length if seg_to < box_begin else 1.0
                csign = 1.0

            if cmin > t_min:
                t_min, axis, normal_sign = cmin, i, csign
            t_max = min(t_max, cmax)
            if t_max < t_min:
                return None

        normal = Vector2()
        normal[axis] = normal_sign
        return Vector2(fx + (tx - fx) * t_min, fy + (ty - fy) * t_min), normal

    def get_support(self, direction):
        """The corner furthest in the given direction."""
        dx, dy = direction
        x, y, w, h = self
        return Vector2(x + w if dx > 0 else x, y + h if dy > 0 else y)

    def is_equal_approx(self, other):
        return self._position.is_equal_approx(other._position) and self._size.is_equal_approx(other._size)

    def is_finite(self):
        return self._position.is_finite() and self._size.is_finite()


class Rect2i(_RectBase):
    """Rect2 with Vector2i position and size, for cell and pixel grids.

    Differences from Rect2:
     - center rounds down with `//`, so Rect2i(0, 0, 5, 5).center is (2, 2).
     - No intersects_segment, get_support or approximate checks (as in Godot).
     - Rect2i(rect2) truncates toward zero; Rect2(rect2i) converts exactly.
     - Transform2D * rect2i returns a Rect2, since rotation produces fractions.
    """

    __slots__ = ()
    _vector = Vector2i

    @property
    def center(self):
        return self._position + self._size // 2

    def cells(self):
        """Every Vector2i cell inside the rect, row by row (end excluded)."""
        x, y, w, h = self
        return (Vector2i(cx, cy) for cy in range(y, y + h) for cx in range(x, x + w))


## Transform2D (core/math/transform_2d.h)

def _rect_corners(rect):
    x, y, w, h = rect
    return (Vector2(x, y), Vector2(x + w, y), Vector2(x, y + h), Vector2(x + w, y + h))


class Transform2D(object):
    """A 2x3 affine matrix stored as three Vector2 columns: the basis `x` and
    `y` plus the translation `origin`. Godot's get_/set_ pairs are also
    properties: t.rotation, t.scale, t.skew, t.origin.

    Applying it (Godot's `*` or Python's matrix operator `@`):
        parent * child                compose (child first, then parent)
        t * vector  t * rect  t * [points]    (a Rect2i comes back as a Rect2)
        vector * t  rect * t          inverse transform; like Godot, this assumes
                                      no scale or skew (use t.affine_inverse() * v)
        t * 2.0     t / 2.0           scale every column

    Constructors, as in Godot:
        Transform2D()                                     identity
        Transform2D(rotation, position)
        Transform2D(rotation, scale, skew, position)
        Transform2D(x, y, origin)                         columns
        Transform2D(xx, xy, yx, yy, ox, oy)               six floats

    2D is y-down, so a positive rotation turns clockwise on screen.
    t.matrix_values() gives the 16 floats of a Ren'Py Matrix for ATL's
    matrixtransform: Matrix(t.matrix_values()).
    """

    __slots__ = ("_x", "_y", "_origin")

    def __init__(self, *args):
        n = len(args)
        if n == 6:
            xx, xy, yx, yy, ox, oy = args
            self._x = Vector2(xx, xy)
            self._y = Vector2(yx, yy)
            self._origin = Vector2(ox, oy)
        elif n == 0:
            self._x = Vector2(1.0, 0.0)
            self._y = Vector2(0.0, 1.0)
            self._origin = Vector2()
        elif n == 1:
            self.x, self.y, self.origin = args[0]
        elif n == 3:
            self.x, self.y, self.origin = args
        elif n == 2:
            rotation, position = args
            cr = math.cos(rotation)
            sr = math.sin(rotation)
            self._x = Vector2(cr, sr)
            self._y = Vector2(-sr, cr)
            self.origin = position
        elif n == 4:
            rotation, scale, skew, position = args
            sx, sy = scale
            self._x = Vector2(math.cos(rotation) * sx, math.sin(rotation) * sx)
            self._y = Vector2(-math.sin(rotation + skew) * sy, math.cos(rotation + skew) * sy)
            self.origin = position
        else:
            raise TypeError("Transform2D() takes 0, 1, 2, 3, 4 or 6 arguments (%d given)" % n)

    def copy(self):
        return Transform2D(*self._floats())

    def _floats(self):
        return (self._x.x, self._x.y, self._y.x, self._y.y, self._origin.x, self._origin.y)

    ## Columns (assigning copies the value)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = Vector2(*value)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = Vector2(*value)

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        self._origin = Vector2(*value)

    def get_origin(self):
        return self._origin.copy()

    ## Decomposed properties

    @property
    def rotation(self):
        return math.atan2(self._x.y, self._x.x)

    @rotation.setter
    def rotation(self, value):
        # Keeps scale; like Godot, this resets any skew.
        sx, sy = self.scale
        cr = math.cos(value)
        sr = math.sin(value)
        self._x = Vector2(cr * sx, sr * sx)
        self._y = Vector2(-sr * sy, cr * sy)

    def get_rotation(self):
        return self.rotation

    @property
    def scale(self):
        """Length of each basis column; y is negative when the transform is flipped."""
        return Vector2(self._x.length(), sign(self.determinant()) * self._y.length())

    @scale.setter
    def scale(self, value):
        sx, sy = value
        self._x = self._x.normalized() * sx
        self._y = self._y.normalized() * sy

    def get_scale(self):
        return self.scale

    @property
    def skew(self):
        det_sign = sign(self.determinant())
        cos_angle = self._x.normalized().dot(self._y.normalized() * det_sign)
        return math.acos(clamp(cos_angle, -1.0, 1.0)) - math.pi / 2

    @skew.setter
    def skew(self, value):
        det_sign = sign(self.determinant())
        self._y = self._x.rotated(math.pi / 2 + value).normalized() * (det_sign * self._y.length())

    def get_skew(self):
        return self.skew

    ## Python protocol

    def __reduce__(self):
        return (Transform2D, self._floats())

    def __repr__(self):
        return "Transform2D(%r, %r, %r, %r, %r, %r)" % self._floats()

    def __str__(self):
        return "[X: %s, Y: %s, O: %s]" % (self._x, self._y, self._origin)

    def __iter__(self):
        return iter((self._x, self._y, self._origin))

    def __len__(self):
        return 3

    def __getitem__(self, column):
        return (self._x, self._y, self._origin)[column]

    def __setitem__(self, column, value):
        setattr(self, ("x", "y", "origin")[column], value)

    def __eq__(self, other):
        if not isinstance(other, Transform2D):
            return NotImplemented
        return self._floats() == other._floats()

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else not result

    def __hash__(self):
        return hash(self._floats())

    ## Operators

    def __matmul__(self, other):
        if isinstance(other, Transform2D):
            ax, ay, ao = self._x, self._y, self._origin
            bx, by, bo = other._x, other._y, other._origin
            return Transform2D(
                ax.x * bx.x + ay.x * bx.y, ax.y * bx.x + ay.y * bx.y,
                ax.x * by.x + ay.x * by.y, ax.y * by.x + ay.y * by.y,
                ax.x * bo.x + ay.x * bo.y + ao.x, ax.y * bo.x + ay.y * bo.y + ao.y)
        if isinstance(other, _VectorBase):
            return self.xform(other)
        if isinstance(other, _RectBase):
            return Rect2.from_points([self.xform(c) for c in _rect_corners(other)])
        if isinstance(other, (list, tuple)):
            return [self.__matmul__(point) for point in other]
        return NotImplemented

    def __rmatmul__(self, other):
        if isinstance(other, _VectorBase):
            return self.xform_inv(other)
        if isinstance(other, _RectBase):
            return Rect2.from_points([self.xform_inv(c) for c in _rect_corners(other)])
        if isinstance(other, (list, tuple)):
            return [self.__rmatmul__(point) for point in other]
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Transform2D(self._x * other, self._y * other, self._origin * other)
        return self.__matmul__(other)

    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            return self * other
        return self.__rmatmul__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Transform2D(self._x / other, self._y / other, self._origin / other)
        return NotImplemented

    ## Applying to vectors

    def basis_xform(self, v):
        """Applies rotation, scale and skew, but not the translation."""
        x, y = self._x, self._y
        return Vector2(x.x * v.x + y.x * v.y, x.y * v.x + y.y * v.y)

    def basis_xform_inv(self, v):
        return Vector2(self._x.dot(v), self._y.dot(v))

    def xform(self, v):
        x, y, o = self._x, self._y, self._origin
        return Vector2(x.x * v.x + y.x * v.y + o.x, x.y * v.x + y.y * v.y + o.y)

    def xform_inv(self, v):
        """Inverse of xform() when the basis is orthonormal (no scale or skew)."""
        return self.basis_xform_inv(v - self._origin)

    ## Inverses

    def determinant(self):
        return self._x.x * self._y.y - self._x.y * self._y.x

    def inverse(self):
        """Fast inverse for rotation + translation only; see affine_inverse()."""
        x, y = self._x, self._y
        t = Transform2D(x.x, y.x, x.y, y.y, 0.0, 0.0)
        t._origin = t.basis_xform(-self._origin)
        return t

    def affine_inverse(self):
        """Full inverse, handling scale and skew. Raises ZeroDivisionError if not invertible."""
        idet = 1.0 / self.determinant()
        x, y = self._x, self._y
        t = Transform2D(y.y * idet, -x.y * idet, -y.x * idet, x.x * idet, 0.0, 0.0)
        t._origin = t.basis_xform(-self._origin)
        return t

    ## New transforms. The plain versions apply in parent space (left
    ## multiplication); the _local versions apply in local space (right).

    def rotated(self, angle):
        return Transform2D(angle, Vector2()) @ self

    def rotated_local(self, angle):
        return self @ Transform2D(angle, Vector2())

    def scaled(self, scale):
        """scale is a Vector2 or a number."""
        return Transform2D(self._x * scale, self._y * scale, self._origin * scale)

    def scaled_local(self, scale):
        sx, sy = _xy(scale)
        return Transform2D(self._x * sx, self._y * sy, self._origin)

    def translated(self, offset):
        return Transform2D(self._x, self._y, self._origin + offset)

    def translated_local(self, offset):
        return Transform2D(self._x, self._y, self._origin + self.basis_xform(offset))

    def orthonormalized(self):
        """Removes scale and skew (Gram-Schmidt), keeping rotation and origin."""
        x = self._x.normalized()
        y = (self._y - x * x.dot(self._y)).normalized()
        return Transform2D(x, y, self._origin)

    def looking_at(self, target):
        """Rotated so +x points at target, keeping origin. Scale and skew are dropped."""
        t = Transform2D(self.rotation, self._origin)
        local_target = self.affine_inverse().xform(target)
        t.rotation = t.rotation + (local_target * self.scale).angle()
        return t

    def interpolate_with(self, to, weight):
        """Interpolates rotation, scale, skew and origin separately."""
        return Transform2D(
            lerp_angle(self.rotation, to.rotation, weight),
            self.scale.lerp(to.scale, weight),
            lerp_angle(self.skew, to.skew, weight),
            self._origin.lerp(to._origin, weight))

    ## Checks

    def is_conformal(self):
        """True if the basis has no skew and the same scale on both axes."""
        eq = is_equal_approx
        x, y = self._x, self._y
        return (eq(x.x, y.y) and eq(x.y, -y.x)) or (eq(x.x, -y.y) and eq(x.y, y.x))

    def is_equal_approx(self, other):
        return all(a.is_equal_approx(b) for a, b in zip(self, other))

    def is_finite(self):
        return all(column.is_finite() for column in self)

    ## Ren'Py interop

    def matrix_values(self):
        """The 16 floats of a Ren'Py Matrix doing the same mapping:
        Matrix(t.matrix_values()) for ATL's matrixtransform."""
        x, y, o = self._x, self._y, self._origin
        return [
            x.x, y.x, 0.0, o.x,
            x.y, y.y, 0.0, o.y,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ]


Transform2D.IDENTITY = _Constant(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
Transform2D.FLIP_X = _Constant(-1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
Transform2D.FLIP_Y = _Constant(1.0, 0.0, 0.0, -1.0, 0.0, 0.0)
