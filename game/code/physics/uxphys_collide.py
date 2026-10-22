"""Collision for adventure mode, after Godot 4.4's physics: a terrain grid,
static bodies, moving bodies (CharacterBody2D in floating mode), areas
(Area2D) and queries (raycasts, point and shape tests).

    import uxphys_collide as col
    grid = col.CollisionGrid(120, 68, 16, cells, terrains=[col.Terrain(0), col.Terrain(1)])
    player = col.Body(col.RectShape(-6, -4, 12, 4), position=(100, 200), owner=entity)
    grid.add(player)

    # every tick
    player.velocity = direction * speed
    player.move_and_slide(delta)
    grid.step()          # areas: enter and exit signals, once per tick

Units are pixels, y points down. Cells are cell_size pixels square; cell
(0, 0) covers [0, cell_size) on both axes.

Layers work like Godot's: collision_layer says what an object (or terrain
type) is, collision_mask what it collides with or detects. Layer n is bit
n - 1, so layer 1 is 1, layer 2 is 2, layer 3 is 4...

Positions are copies: `body.position.x = 5` changes a temporary vector and
does nothing. Assign `body.position = ...` (a teleport). `body.velocity` is a
plain attribute, so `body.velocity.x = 0` works.

Physics objects hold callables and aren't meant for saves: rebuild them from
saved plain data after a load.
"""

import math

from uxphys_math import CMP_EPSILON, Rect2, Vector2, Vector2i

__all__ = [
    "ALL_LAYERS", "SKIN", "Terrain", "RectShape", "CircleShape", "Signal",
    "CollisionGrid", "CollisionObject", "StaticBody", "Body", "Area",
    "Collision", "RayHit",
]

INF = math.inf
ALL_LAYERS = 0xFFFFFFFF
_floor = math.floor

# Gap a body keeps from whatever stops it, in pixels. Small enough to be
# invisible, large enough to stay positive after rounding, so a body sliding
# along a wall never catches on the seams between its cells.
SKIN = 0.001

# Positions must stay within +-_MAX_COORD; that keeps bucket keys unique.
_MAX_COORD = 1000000.0
_KEY = 1 << 20

# Godot's FLOOR_ANGLE_THRESHOLD, added to wall_min_slide_angle.
_ANGLE_THRESHOLD = 0.01

# Stands for "outside the grid" boxes: far enough, but keeps float precision.
_FAR = 10000000.0


def _check_coord(x, y):
    if not (-_MAX_COORD < x < _MAX_COORD and -_MAX_COORD < y < _MAX_COORD):
        raise ValueError("position out of range: (%r, %r)" % (x, y))


## Terrain and shapes

class Terrain(object):
    """A terrain type: the collision layers its cells are on (0 = blocks
    nothing) and a speed factor for bodies standing on it (0.5 = half speed)."""

    __slots__ = ("layer", "speed")

    def __init__(self, layer=0, speed=1.0):
        self.layer = int(layer)
        self.speed = float(speed)

    def __repr__(self):
        return "Terrain(%r, %r)" % (self.layer, self.speed)


class RectShape(object):
    """An axis-aligned box. (x, y) is its top-left corner relative to the
    owner's position, like the map editor's [x, y, w, h] boxes; centered()
    makes Godot's RectangleShape2D, centred on the position.

    Shapes never change: to resize something, give it new shapes. One shape
    can be shared by any number of objects."""

    __slots__ = ("x0", "y0", "x1", "y1")
    is_circle = False

    def __init__(self, x, y=None, width=None, height=None):
        if y is None:
            x, y, width, height = x
        if not (width > 0 and height > 0):
            raise ValueError("a RectShape needs a positive size")
        self.x0 = float(x)
        self.y0 = float(y)
        self.x1 = self.x0 + width
        self.y1 = self.y0 + height

    @classmethod
    def centered(cls, width, height, x=0.0, y=0.0):
        """A width x height box centred on (x, y)."""
        return cls(x - width * 0.5, y - height * 0.5, width, height)

    @property
    def size(self):
        return Vector2(self.x1 - self.x0, self.y1 - self.y0)

    def get_rect(self):
        """The box relative to the owner's position."""
        return Rect2(self.x0, self.y0, self.x1 - self.x0, self.y1 - self.y0)

    def __repr__(self):
        return "RectShape(%r, %r, %r, %r)" % (self.x0, self.y0, self.x1 - self.x0, self.y1 - self.y0)


class CircleShape(object):
    """A circle of radius `radius` centred on (x, y) relative to the owner's position."""

    __slots__ = ("cx", "cy", "radius", "x0", "y0", "x1", "y1")
    is_circle = True

    def __init__(self, radius, x=0.0, y=0.0):
        if not radius > 0:
            raise ValueError("a CircleShape needs a positive radius")
        self.radius = float(radius)
        self.cx = float(x)
        self.cy = float(y)
        self.x0 = self.cx - self.radius
        self.y0 = self.cy - self.radius
        self.x1 = self.cx + self.radius
        self.y1 = self.cy + self.radius

    def get_rect(self):
        """The circle's bounding box relative to the owner's position."""
        return Rect2(self.x0, self.y0, self.x1 - self.x0, self.y1 - self.y0)

    def __repr__(self):
        return "CircleShape(%r, %r, %r)" % (self.radius, self.cx, self.cy)


_SHAPE_TYPES = (RectShape, CircleShape)


class Signal(object):
    """A Godot-style signal: area.body_entered.connect(fn), fn(body)."""

    __slots__ = ("_callbacks",)

    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def disconnect(self, callback):
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def is_connected(self, callback):
        return callback in self._callbacks

    def emit(self, *args):
        for callback in tuple(self._callbacks):
            callback(*args)


## Sweeps: the earliest time t in [0, 1] at which a shape moving by (mx, my)
## touches a fixed shape, and the fixed shape's surface normal there (pointing
## at the mover). Each returns (t, nx, ny, depth) or None.
##
## Shapes already overlapping at the start count as a hit at t = 0 with the
## push-out normal and the overlap depth, but only when the motion goes deeper;
## moving out of (or along) an overlap is allowed, so nothing gets stuck.

def _sweep_box_box(ax0, ay0, ax1, ay1, mx, my, bx0, by0, bx1, by1):
    if mx > 0.0:
        tx0 = (bx0 - ax1) / mx
        tx1 = (bx1 - ax0) / mx
    elif mx < 0.0:
        tx0 = (bx1 - ax0) / mx
        tx1 = (bx0 - ax1) / mx
    elif ax1 <= bx0 or ax0 >= bx1:
        return None
    else:
        tx0 = -INF
        tx1 = INF

    if my > 0.0:
        ty0 = (by0 - ay1) / my
        ty1 = (by1 - ay0) / my
    elif my < 0.0:
        ty0 = (by1 - ay0) / my
        ty1 = (by0 - ay1) / my
    elif ay1 <= by0 or ay0 >= by1:
        return None
    else:
        ty0 = -INF
        ty1 = INF

    t1 = tx1 if tx1 < ty1 else ty1
    if tx0 > ty0:
        t0 = tx0
        if t0 >= t1 or t0 > 1.0 or t1 <= 0.0:
            return None
        if t0 >= 0.0:
            return (t0, -1.0 if mx > 0.0 else 1.0, 0.0, 0.0)
    else:
        t0 = ty0
        if t0 >= t1 or t0 > 1.0 or t1 <= 0.0:
            return None
        if t0 >= 0.0:
            return (t0, 0.0, -1.0 if my > 0.0 else 1.0, 0.0)

    # Overlapping at the start: push out along the shallower axis.
    px = min(ax1 - bx0, bx1 - ax0)
    py = min(ay1 - by0, by1 - ay0)
    if px < py:
        nx = 1.0 if ax0 + ax1 > bx0 + bx1 else -1.0
        if mx * nx < 0.0:
            return (0.0, nx, 0.0, px)
    else:
        ny = 1.0 if ay0 + ay1 > by0 + by1 else -1.0
        if my * ny < 0.0:
            return (0.0, 0.0, ny, py)
    return None


def _sweep_circle_box(cx, cy, r, mx, my, bx0, by0, bx1, by1):
    # Already overlapping?
    qx = bx0 if cx < bx0 else (bx1 if cx > bx1 else cx)
    qy = by0 if cy < by0 else (by1 if cy > by1 else cy)
    dx = cx - qx
    dy = cy - qy
    d2 = dx * dx + dy * dy
    if d2 < r * r:
        if d2 > 0.0:
            d = math.sqrt(d2)
            nx = dx / d
            ny = dy / d
            depth = r - d
        else:
            # Centre inside the box: out through the nearest side.
            left = cx - bx0
            right = bx1 - cx
            top = cy - by0
            bottom = by1 - cy
            nearest = min(left, right, top, bottom)
            if nearest == left:
                nx, ny = -1.0, 0.0
            elif nearest == right:
                nx, ny = 1.0, 0.0
            elif nearest == top:
                nx, ny = 0.0, -1.0
            else:
                nx, ny = 0.0, 1.0
            depth = r + nearest
        if mx * nx + my * ny < 0.0:
            return (0.0, nx, ny, depth)
        return None

    # The centre against the box grown by r (the corners get rounded below).
    ex0 = bx0 - r
    ey0 = by0 - r
    ex1 = bx1 + r
    ey1 = by1 + r
    if mx > 0.0:
        tx0 = (ex0 - cx) / mx
        tx1 = (ex1 - cx) / mx
    elif mx < 0.0:
        tx0 = (ex1 - cx) / mx
        tx1 = (ex0 - cx) / mx
    elif cx <= ex0 or cx >= ex1:
        return None
    else:
        tx0 = -INF
        tx1 = INF
    if my > 0.0:
        ty0 = (ey0 - cy) / my
        ty1 = (ey1 - cy) / my
    elif my < 0.0:
        ty0 = (ey1 - cy) / my
        ty1 = (ey0 - cy) / my
    elif cy <= ey0 or cy >= ey1:
        return None
    else:
        ty0 = -INF
        ty1 = INF
    t1 = tx1 if tx1 < ty1 else ty1
    x_axis = tx0 > ty0
    t0 = tx0 if x_axis else ty0
    if t0 >= t1 or t0 > 1.0 or t1 <= 0.0:
        return None

    if t0 >= 0.0:
        px = cx + mx * t0
        py = cy + my * t0
        if x_axis:
            if by0 <= py <= by1:
                return (t0, -1.0 if mx > 0.0 else 1.0, 0.0, 0.0)
        elif bx0 <= px <= bx1:
            return (t0, 0.0, -1.0 if my > 0.0 else 1.0, 0.0)
    else:
        px = cx
        py = cy

    # Entering a corner region of the grown box: the hit, if any, is on that
    # corner's circle (to reach a flat side from there it would cross the circle).
    kx = bx0 if px < bx0 else bx1
    ky = by0 if py < by0 else by1
    fx = cx - kx
    fy = cy - ky
    b = fx * mx + fy * my
    if b >= 0.0:
        return None
    a = mx * mx + my * my
    c = fx * fx + fy * fy - r * r
    disc = b * b - a * c
    if disc <= 0.0:
        return None
    t = (-b - math.sqrt(disc)) / a
    if t > 1.0:
        return None
    if t < 0.0:
        t = 0.0
    return (t, (fx + mx * t) / r, (fy + my * t) / r, 0.0)


def _sweep_circle_circle(cx, cy, r, mx, my, ox, oy, orad):
    big = r + orad
    fx = cx - ox
    fy = cy - oy
    c = fx * fx + fy * fy - big * big
    if c < 0.0:
        d = math.sqrt(fx * fx + fy * fy)
        if d > 0.0:
            nx = fx / d
            ny = fy / d
        else:
            nx, ny = 0.0, -1.0
        if mx * nx + my * ny < 0.0:
            return (0.0, nx, ny, big - d)
        return None
    b = fx * mx + fy * my
    if b >= 0.0:
        return None
    a = mx * mx + my * my
    disc = b * b - a * c
    if disc <= 0.0:
        return None
    t = (-b - math.sqrt(disc)) / a
    if t > 1.0:
        return None
    if t < 0.0:
        t = 0.0
    return (t, (fx + mx * t) / big, (fy + my * t) / big, 0.0)


## Overlap tests (touching doesn't count)

def _overlap_box_box(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


def _overlap_circle_box(cx, cy, r, bx0, by0, bx1, by1):
    dx = cx - (bx0 if cx < bx0 else (bx1 if cx > bx1 else cx))
    dy = cy - (by0 if cy < by0 else (by1 if cy > by1 else cy))
    return dx * dx + dy * dy < r * r


def _shapes_overlap(sa, ax, ay, sb, bx, by):
    """Whether shape sa at (ax, ay) overlaps shape sb at (bx, by)."""
    if sa.is_circle:
        if sb.is_circle:
            dx = ax + sa.cx - bx - sb.cx
            dy = ay + sa.cy - by - sb.cy
            reach = sa.radius + sb.radius
            return dx * dx + dy * dy < reach * reach
        return _overlap_circle_box(ax + sa.cx, ay + sa.cy, sa.radius, bx + sb.x0, by + sb.y0, bx + sb.x1, by + sb.y1)
    if sb.is_circle:
        return _overlap_circle_box(bx + sb.cx, by + sb.cy, sb.radius, ax + sa.x0, ay + sa.y0, ax + sa.x1, ay + sa.y1)
    return (ax + sa.x0 < bx + sb.x1 and bx + sb.x0 < ax + sa.x1
            and ay + sa.y0 < by + sb.y1 and by + sb.y0 < ay + sa.y1)


def _objects_overlap(a, b):
    ax = a._x
    ay = a._y
    bx = b._x
    by = b._y
    for sa in a._shapes:
        for sb in b._shapes:
            if _shapes_overlap(sa, ax, ay, sb, bx, by):
                return True
    return False


def _shape_overlaps_box(shape, x, y, bx0, by0, bx1, by1):
    if shape.is_circle:
        return _overlap_circle_box(x + shape.cx, y + shape.cy, shape.radius, bx0, by0, bx1, by1)
    return _overlap_box_box(x + shape.x0, y + shape.y0, x + shape.x1, y + shape.y1, bx0, by0, bx1, by1)


def _shape_has_point(shape, x, y, px, py):
    if shape.is_circle:
        dx = px - x - shape.cx
        dy = py - y - shape.cy
        return dx * dx + dy * dy < shape.radius * shape.radius
    return x + shape.x0 <= px < x + shape.x1 and y + shape.y0 <= py < y + shape.y1


## Rays: (t, nx, ny) where the ray from (fx, fy) along (dx, dy) first enters
## the shape, t in [0, limit], or None. A ray starting inside hits at t = 0
## with a zero normal when hit_from_inside, and ignores the shape otherwise.

def _ray_box(fx, fy, dx, dy, x0, y0, x1, y1, limit, hit_from_inside):
    if x0 < fx < x1 and y0 < fy < y1:
        return (0.0, 0.0, 0.0) if hit_from_inside else None
    t0 = 0.0
    t1 = INF
    axis = -1
    if dx:
        ta = (x0 - fx) / dx
        tb = (x1 - fx) / dx
        if ta > tb:
            ta, tb = tb, ta
        if ta > t0:
            t0 = ta
            axis = 0
        if tb < t1:
            t1 = tb
    elif fx <= x0 or fx >= x1:
        return None
    if dy:
        ta = (y0 - fy) / dy
        tb = (y1 - fy) / dy
        if ta > tb:
            ta, tb = tb, ta
        if ta > t0:
            t0 = ta
            axis = 1
        if tb < t1:
            t1 = tb
    elif fy <= y0 or fy >= y1:
        return None
    if t0 >= t1 or t0 > limit:
        return None
    if axis == 0:
        return (t0, -1.0 if dx > 0 else 1.0, 0.0)
    if axis == 1:
        return (t0, 0.0, -1.0 if dy > 0 else 1.0)
    # Starting on the boundary and going in.
    return (0.0, 0.0, 0.0) if hit_from_inside else None


def _ray_circle(fx, fy, dx, dy, cx, cy, r, limit, hit_from_inside):
    ex = fx - cx
    ey = fy - cy
    c = ex * ex + ey * ey - r * r
    if c < 0.0:
        return (0.0, 0.0, 0.0) if hit_from_inside else None
    b = ex * dx + ey * dy
    if b >= 0.0:
        return None
    a = dx * dx + dy * dy
    disc = b * b - a * c
    if disc <= 0.0:
        return None
    t = (-b - math.sqrt(disc)) / a
    if t > limit:
        return None
    return (t, (ex + dx * t) / r, (ey + dy * t) / r)


def _walk_cells(px, py, dx, dy):
    """Unit grid cells crossed by the ray (px, py) + t * (dx, dy), in order, as
    (cx, cy, t_enter). Endless: the caller stops it."""
    cx = math.floor(px)
    cy = math.floor(py)
    step_x = 1 if dx > 0 else -1
    step_y = 1 if dy > 0 else -1
    if dx:
        next_x = ((cx + 1 if dx > 0 else cx) - px) / dx
        delta_x = abs(1.0 / dx)
    else:
        next_x = delta_x = INF
    if dy:
        next_y = ((cy + 1 if dy > 0 else cy) - py) / dy
        delta_y = abs(1.0 / dy)
    else:
        next_y = delta_y = INF
    t = 0.0
    while True:
        yield cx, cy, t
        if next_x < next_y:
            t = next_x
            cx += step_x
            next_x += delta_x
        else:
            t = next_y
            cy += step_y
            next_y += delta_y
        if t == INF:
            return


## Results

class Collision(object):
    """What stopped a move: Godot's KinematicCollision2D. Read the attributes
    or the Godot getters.

    collider is the CollisionObject hit, or the CollisionGrid for terrain (then
    cell is its Vector2i cell). depth is non-zero only when the body started
    out overlapping what it hit."""

    __slots__ = ("position", "normal", "travel", "remainder", "collider", "collider_shape",
                 "local_shape", "cell", "depth", "collider_velocity")

    def get_position(self):
        return self.position

    def get_normal(self):
        return self.normal

    def get_travel(self):
        return self.travel

    def get_remainder(self):
        return self.remainder

    def get_collider(self):
        return self.collider

    def get_collider_shape(self):
        return self.collider_shape

    def get_local_shape(self):
        return self.local_shape

    def get_depth(self):
        return self.depth

    def get_collider_velocity(self):
        return self.collider_velocity

    def get_angle(self, up_direction=None):
        """Angle between the normal and up_direction (default Vector2.UP)."""
        ux, uy = (0.0, -1.0) if up_direction is None else up_direction
        return math.acos(max(-1.0, min(1.0, self.normal.x * ux + self.normal.y * uy)))

    def __repr__(self):
        return "<Collision %s normal %s with %r>" % (self.position, self.normal, self.collider)


class RayHit(object):
    """A raycast hit. Attributes as in Godot's intersect_ray() result, which
    also works as hit["position"]. collider is the grid for terrain, then cell
    is the Vector2i cell; a ray leaving the grid into blocking outside terrain
    has collider grid and cell None."""

    __slots__ = ("position", "normal", "collider", "collider_shape", "cell")

    def __init__(self, position, normal, collider, collider_shape=None, cell=None):
        self.position = position
        self.normal = normal
        self.collider = collider
        self.collider_shape = collider_shape
        self.cell = cell

    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self):
        return "<RayHit %s normal %s with %r>" % (self.position, self.normal, self.collider)


## Objects

class CollisionObject(object):
    """Base of StaticBody, Body and Area: a position, shapes, layers and an
    owner (any value: the game object it belongs to). Add it to a
    CollisionGrid to take part; an object belongs to one grid at a time."""

    __slots__ = ("grid", "owner", "_shapes", "_x", "_y", "_layer", "_mask",
                 "_lx0", "_ly0", "_lx1", "_ly1", "_bkeys", "_stamp", "_dirty", "_monitors", "_no_areas")

    _is_area = False
    _is_static = False

    def __init__(self, shapes=(), position=(0.0, 0.0), collision_layer=1, collision_mask=1, owner=None):
        self.grid = None
        self.owner = owner
        x, y = position
        x = float(x)
        y = float(y)
        _check_coord(x, y)
        self._x = x
        self._y = y
        self._layer = int(collision_layer)
        self._mask = int(collision_mask)
        self._bkeys = None
        self._stamp = 0
        self._dirty = False
        # Areas currently detecting this object, as an ordered set.
        self._monitors = {}
        # (grid._area_version, bucket keys) when no area was in its buckets.
        self._no_areas = None
        self._set_shapes(shapes)

    def __repr__(self):
        return "<%s at (%g, %g) owner=%r>" % (type(self).__name__, self._x, self._y, self.owner)

    ## Position

    @property
    def position(self):
        """A copy: assign a new position to move (teleport) the object."""
        return Vector2(self._x, self._y)

    @position.setter
    def position(self, value):
        x, y = value
        x = float(x)
        y = float(y)
        _check_coord(x, y)
        self._x = x
        self._y = y
        if self.grid is not None:
            self.grid._object_moved(self)

    def get_aabb(self):
        """Bounding box of all the shapes, in world coordinates."""
        return Rect2(self._x + self._lx0, self._y + self._ly0, self._lx1 - self._lx0, self._ly1 - self._ly0)

    def get_local_aabb(self):
        """Bounding box of all the shapes, relative to the position."""
        return Rect2(self._lx0, self._ly0, self._lx1 - self._lx0, self._ly1 - self._ly0)

    ## Shapes

    @property
    def shapes(self):
        return self._shapes

    @shapes.setter
    def shapes(self, shapes):
        self._set_shapes(shapes)
        if self.grid is not None:
            self.grid._object_moved(self)

    def _set_shapes(self, shapes):
        if isinstance(shapes, _SHAPE_TYPES):
            shapes = (shapes,)
        shapes = tuple(shapes)
        for shape in shapes:
            if not isinstance(shape, _SHAPE_TYPES):
                raise TypeError("expected a RectShape or CircleShape, got %r" % (shape,))
        self._shapes = shapes
        if shapes:
            self._lx0 = min(s.x0 for s in shapes)
            self._ly0 = min(s.y0 for s in shapes)
            self._lx1 = max(s.x1 for s in shapes)
            self._ly1 = max(s.y1 for s in shapes)
        else:
            self._lx0 = self._ly0 = self._lx1 = self._ly1 = 0.0

    ## Layers

    @property
    def collision_layer(self):
        return self._layer

    @collision_layer.setter
    def collision_layer(self, value):
        self._layer = int(value)
        if self.grid is not None:
            self.grid._object_changed(self)

    @property
    def collision_mask(self):
        return self._mask

    @collision_mask.setter
    def collision_mask(self, value):
        self._mask = int(value)
        if self.grid is not None:
            self.grid._object_changed(self)

    def set_collision_layer_value(self, layer_number, value):
        """Turns layer layer_number (1 to 32) on or off."""
        bit = 1 << (layer_number - 1)
        self.collision_layer = (self._layer | bit) if value else (self._layer & ~bit)

    def get_collision_layer_value(self, layer_number):
        return bool(self._layer & (1 << (layer_number - 1)))

    def set_collision_mask_value(self, layer_number, value):
        bit = 1 << (layer_number - 1)
        self.collision_mask = (self._mask | bit) if value else (self._mask & ~bit)

    def get_collision_mask_value(self, layer_number):
        return bool(self._mask & (1 << (layer_number - 1)))


class StaticBody(CollisionObject):
    """Something solid that doesn't move by itself: a prop's collision box, an
    invisible wall. Pathfinding avoids static bodies (and not moving Bodies).
    Moving one is allowed but recomputes pathfinding maps."""

    __slots__ = ()
    _is_static = True


class Body(CollisionObject):
    """A moving body: Godot's CharacterBody2D in floating (top-down) mode.

    Set velocity (pixels per second) and call move_and_slide(delta) once per
    tick: the body moves, sliding along what it hits; velocity itself isn't
    changed (get_real_velocity() is what really happened). On slow terrain the
    motion is scaled by the terrain's speed factor at the body's position,
    unless use_terrain_speed is False.

    Bodies stop at anything whose collision_layer is in their collision_mask:
    terrain, static bodies, other bodies. They don't push each other."""

    __slots__ = ("velocity", "max_slides", "wall_min_slide_angle", "use_terrain_speed",
                 "terrain_speed", "_collisions", "_exceptions", "_last_mx", "_last_my",
                 "_delta_x", "_delta_y", "_real_vx", "_real_vy", "_on_wall", "_wall_nx", "_wall_ny")

    def __init__(self, shapes=(), position=(0.0, 0.0), collision_layer=1, collision_mask=1, owner=None):
        super(Body, self).__init__(shapes, position, collision_layer, collision_mask, owner)
        self.velocity = Vector2()
        self.max_slides = 4
        # Hitting a wall closer than this to head-on stops instead of sliding.
        self.wall_min_slide_angle = math.radians(15.0)
        self.use_terrain_speed = True
        # The speed factor applied by the last move_and_slide.
        self.terrain_speed = 1.0
        self._collisions = []
        self._exceptions = None
        self._last_mx = self._last_my = 0.0
        self._delta_x = self._delta_y = 0.0
        self._real_vx = self._real_vy = 0.0
        self._on_wall = False
        self._wall_nx = self._wall_ny = 0.0

    ## Moving

    def move_and_slide(self, delta):
        """Moves by velocity * delta, sliding along whatever is hit. Returns
        True if anything was hit (see get_slide_collision())."""
        grid = self.grid
        if grid is None:
            raise RuntimeError("add the body to a CollisionGrid before moving it")
        collisions = self._collisions
        if collisions:
            collisions.clear()
        self._on_wall = False
        start_x = self._x
        start_y = self._y
        v = self.velocity
        vx = v.x
        vy = v.y

        speed = 1.0
        if self.use_terrain_speed:
            inv = grid._inv_cell
            cx = _floor(start_x * inv)
            cy = _floor(start_y * inv)
            if 0 <= cx < grid.columns and 0 <= cy < grid.rows:
                speed = grid._speed_table[grid._cells[cy * grid.columns + cx]]
            else:
                speed = grid._outside_speed
        self.terrain_speed = speed
        f = delta * speed
        mx = vx * f
        my = vy * f
        self._last_mx = self._last_my = 0.0

        if mx or my:
            first_slide = True
            for _ in range(self.max_slides):
                hit = grid._cast(self, mx, my)
                if hit is None:
                    self._move_by(mx, my)
                    self._last_mx = mx
                    self._last_my = my
                    break
                collision = self._resolve(hit, mx, my, False)
                collisions.append(collision)
                normal = collision.normal
                nx = normal.x
                ny = normal.y
                self._on_wall = True
                self._wall_nx = nx
                self._wall_ny = ny
                travel = collision.travel
                rx = mx - travel.x
                ry = my - travel.y
                if abs(rx) < CMP_EPSILON and abs(ry) < CMP_EPSILON:
                    break

                # Godot's _move_and_slide_floating().
                min_angle = self.wall_min_slide_angle
                stop = False
                if min_angle:
                    vlen = math.hypot(vx, vy)
                    cos_angle = -(nx * vx + ny * vy) / vlen
                    stop = math.acos(max(-1.0, min(1.0, cos_angle))) < min_angle + _ANGLE_THRESHOLD
                if stop:
                    mx = my = 0.0
                else:
                    dot = rx * nx + ry * ny
                    sx = rx - nx * dot
                    sy = ry - ny * dot
                    if first_slide:
                        # Keep the full remaining length, redirected along the wall.
                        slen = math.hypot(sx, sy)
                        if slen:
                            scale = (math.hypot(mx, my) - math.hypot(travel.x, travel.y)) / slen
                            sx *= scale
                            sy *= scale
                    mx = sx
                    my = sy
                if mx * vx + my * vy <= 0.0:
                    mx = my = 0.0
                if abs(mx) < CMP_EPSILON and abs(my) < CMP_EPSILON:
                    break
                first_slide = False

        dx = self._x - start_x
        dy = self._y - start_y
        self._delta_x = dx
        self._delta_y = dy
        if delta:
            self._real_vx = dx / delta
            self._real_vy = dy / delta
        else:
            self._real_vx = self._real_vy = 0.0
        return bool(collisions)

    def move_and_collide(self, motion, test_only=False):
        """Moves by motion (pixels, not scaled by terrain speed), stopping at
        the first thing hit. Returns a Collision, or None if the way was clear.
        With test_only, reports what would happen without moving."""
        if self.grid is None:
            raise RuntimeError("add the body to a CollisionGrid before moving it")
        mx, my = motion
        return self._collide(float(mx), float(my), test_only)

    def test_move(self, motion):
        """True if moving by motion would hit something."""
        return self.move_and_collide(motion, test_only=True) is not None

    def _collide(self, mx, my, test_only):
        hit = self.grid._cast(self, mx, my)
        if hit is None:
            if not test_only:
                self._move_by(mx, my)
                self._last_mx = mx
                self._last_my = my
            return None
        return self._resolve(hit, mx, my, test_only)

    def _resolve(self, hit, mx, my, test_only):
        """Moves up to a hit found by _cast (unless test_only) and describes it."""
        t, nx, ny, depth, collider, collider_shape, cell, own, geometry = hit

        # Stop SKIN short of the contact, measured along the normal.
        approach = -(mx * nx + my * ny)
        if approach > 0.0:
            t -= SKIN / approach
        if t < 0.0:
            t = 0.0
        tx = mx * t
        ty = my * t

        # Contact point: the closest point of what was hit to the shape's centre.
        if own.is_circle:
            ox = self._x + own.cx + tx
            oy = self._y + own.cy + ty
        else:
            ox = self._x + (own.x0 + own.x1) * 0.5 + tx
            oy = self._y + (own.y0 + own.y1) * 0.5 + ty
        if geometry[0]:
            _, gx, gy, grad = geometry
            px = gx + nx * grad
            py = gy + ny * grad
        else:
            _, gx0, gy0, gx1, gy1 = geometry
            px = gx0 if ox < gx0 else (gx1 if ox > gx1 else ox)
            py = gy0 if oy < gy0 else (gy1 if oy > gy1 else oy)

        if not test_only:
            self._move_by(tx, ty)
            self._last_mx = tx
            self._last_my = ty

        collision = Collision()
        collision.position = Vector2(px, py)
        collision.normal = Vector2(nx, ny)
        collision.travel = Vector2(tx, ty)
        collision.remainder = Vector2(mx - tx, my - ty)
        collision.collider = collider
        collision.collider_shape = collider_shape
        collision.local_shape = own
        collision.cell = Vector2i(cell[0], cell[1]) if cell is not None else None
        collision.depth = depth
        velocity = getattr(collider, "velocity", None)
        collision.collider_velocity = Vector2(velocity.x, velocity.y) if velocity is not None else Vector2()
        return collision

    def _move_by(self, dx, dy):
        x = self._x + dx
        y = self._y + dy
        if not (-_MAX_COORD < x < _MAX_COORD and -_MAX_COORD < y < _MAX_COORD):
            raise ValueError("body moved out of range: (%r, %r)" % (x, y))
        self._x = x
        self._y = y
        grid = self.grid
        inv = grid._inv_bucket
        keys = (_floor((x + self._lx0) * inv), _floor((y + self._ly0) * inv),
                _floor((x + self._lx1) * inv), _floor((y + self._ly1) * inv))
        if keys != self._bkeys:
            grid._unlink(self)
            grid._link(self, keys)
        if grid._area_count and not self._dirty:
            # Skip step()'s check while this body stays in buckets known to hold no area.
            if self._monitors or self._no_areas != (grid._area_version, keys):
                self._dirty = True
                grid._dirty.append(self)

    ## Results of the last move_and_slide()

    def get_slide_collision_count(self):
        return len(self._collisions)

    def get_slide_collision(self, slide_idx):
        return self._collisions[slide_idx]

    def get_last_slide_collision(self):
        return self._collisions[-1] if self._collisions else None

    def is_on_wall(self):
        """In floating mode everything hit counts as a wall."""
        return self._on_wall

    is_on_wall_only = is_on_wall

    def get_wall_normal(self):
        return Vector2(self._wall_nx, self._wall_ny) if self._on_wall else Vector2()

    def get_real_velocity(self):
        return Vector2(self._real_vx, self._real_vy)

    def get_position_delta(self):
        return Vector2(self._delta_x, self._delta_y)

    def get_last_motion(self):
        return Vector2(self._last_mx, self._last_my)

    ## Exceptions: objects this body passes through (say, its own projectiles)

    def add_collision_exception_with(self, obj):
        if self._exceptions is None:
            self._exceptions = set()
        self._exceptions.add(obj)

    def remove_collision_exception_with(self, obj):
        if self._exceptions is not None:
            self._exceptions.discard(obj)
            if not self._exceptions:
                self._exceptions = None

    def get_collision_exceptions(self):
        return list(self._exceptions or ())


class Area(CollisionObject):
    """Detects bodies and other areas overlapping it: Godot's Area2D. It never
    blocks anything.

    Signals body_entered(body), body_exited(body), area_entered(area) and
    area_exited(area) fire from CollisionGrid.step(), once per tick. An area
    detects objects whose collision_layer is in its collision_mask; it needs
    monitoring to detect, and other areas need monitorable to be detected.
    Removing either side of an overlap fires the exit at the next step()."""

    __slots__ = ("_monitoring", "_monitorable", "body_entered", "body_exited",
                 "area_entered", "area_exited", "_bodies", "_areas")

    _is_area = True

    def __init__(self, shapes=(), position=(0.0, 0.0), collision_layer=1, collision_mask=1, owner=None,
                 monitoring=True, monitorable=True):
        super(Area, self).__init__(shapes, position, collision_layer, collision_mask, owner)
        self._monitoring = bool(monitoring)
        self._monitorable = bool(monitorable)
        self.body_entered = Signal()
        self.body_exited = Signal()
        self.area_entered = Signal()
        self.area_exited = Signal()
        # Ordered sets of what this area currently detects.
        self._bodies = {}
        self._areas = {}

    @property
    def monitoring(self):
        return self._monitoring

    @monitoring.setter
    def monitoring(self, value):
        self._monitoring = bool(value)
        if self.grid is not None:
            self.grid._mark_dirty(self)

    @property
    def monitorable(self):
        return self._monitorable

    @monitorable.setter
    def monitorable(self, value):
        self._monitorable = bool(value)
        if self.grid is not None:
            self.grid._mark_dirty(self)

    def get_overlapping_bodies(self):
        return list(self._bodies)

    def get_overlapping_areas(self):
        return list(self._areas)

    def has_overlapping_bodies(self):
        return bool(self._bodies)

    def has_overlapping_areas(self):
        return bool(self._areas)

    def overlaps_body(self, body):
        return body in self._bodies

    def overlaps_area(self, area):
        return area in self._areas


## The grid

class CollisionGrid(object):
    """A room's collision world: a grid of terrain cells plus the objects in it.

    columns x rows cells of cell_size pixels. cells holds one terrain index
    (0-255) per cell, row by row (bytes, bytearray or a list of ints), such as
    the map editor's mask. terrains lists a Terrain (or a (layer, speed)
    tuple) per index; indices without one are open floor. The default is
    0 = floor, 1 = solid on layer 1. outside is the terrain index used beyond
    the edges: 0 lets bodies walk off the map, a solid one walls it in.

    Objects are kept in a spatial hash of bucket_size pixel buckets."""

    def __init__(self, columns, rows, cell_size, cells=None, terrains=None, outside=0, bucket_size=64):
        columns = int(columns)
        rows = int(rows)
        if columns < 1 or rows < 1 or not cell_size > 0 or not bucket_size > 0:
            raise ValueError("a CollisionGrid needs a positive size, cell size and bucket size")
        self.columns = columns
        self.rows = rows
        self.cell_size = cell_size
        self._inv_cell = 1.0 / cell_size
        self._width = columns * cell_size
        self._height = rows * cell_size
        self._cells = bytearray(columns * rows)
        if cells is not None:
            self._set_cells(cells)
        self._bucket = float(bucket_size)
        self._inv_bucket = 1.0 / bucket_size

        # Objects: one spatial hash for what blocks (bodies), one for areas.
        self._solids = {}
        self._area_buckets = {}
        self._objects = {}
        self._owners = {}
        self._statics = {}
        self._area_count = 0
        # Bumped whenever an area enters or leaves a bucket.
        self._area_version = 0
        self._stamp = 0
        self._dirty = []
        self._events = []

        # Bumped whenever terrain or static bodies change. `cache` holds data
        # derived from them (pathfinding maps) and is cleared at each bump.
        self.version = 0
        self.cache = {}

        self._outside = int(outside)
        self._blocked_cache = {}
        self.set_terrains(terrains if terrains is not None else (Terrain(0), Terrain(1)))

        w = columns * cell_size
        h = rows * cell_size
        self._outside_boxes = (
            (-_FAR, -_FAR, 0.0, h + _FAR),
            (w, -_FAR, w + _FAR, h + _FAR),
            (0.0, -_FAR, w, 0.0),
            (0.0, h, w, h + _FAR),
        )

    def __repr__(self):
        return "<CollisionGrid %dx%d cells of %s px, %d objects>" % (
            self.columns, self.rows, self.cell_size, len(self._objects))

    def _bump(self):
        self.version += 1
        self.cache.clear()

    ## Terrain

    @property
    def size(self):
        """Size in pixels."""
        return Vector2(self.columns * self.cell_size, self.rows * self.cell_size)

    def get_rect(self):
        return Rect2(0, 0, self.columns * self.cell_size, self.rows * self.cell_size)

    def set_terrains(self, terrains):
        terrains = [t if isinstance(t, Terrain) else Terrain(*t) for t in terrains]
        if len(terrains) > 256:
            raise ValueError("at most 256 terrain types")
        self.terrains = terrains
        layers = [0] * 256
        speeds = [1.0] * 256
        for i, terrain in enumerate(terrains):
            layers[i] = terrain.layer
            speeds[i] = terrain.speed
        self._layer_table = layers
        self._speed_table = speeds
        # Every layer some terrain is on, so masks without any skip the cells.
        self._terrain_layers = 0
        for layer in layers:
            self._terrain_layers |= layer
        self._outside_layer = layers[self._outside & 255]
        self._outside_speed = speeds[self._outside & 255]
        self._blocked_cache.clear()
        self._bump()

    @property
    def outside(self):
        return self._outside

    @outside.setter
    def outside(self, terrain):
        self._outside = int(terrain)
        self._outside_layer = self._layer_table[self._outside & 255]
        self._outside_speed = self._speed_table[self._outside & 255]
        self._bump()

    def _set_cells(self, cells):
        cells = bytearray(cells)
        if len(cells) != self.columns * self.rows:
            raise ValueError("expected %d cells, got %d" % (self.columns * self.rows, len(cells)))
        self._cells = cells

    def set_cells(self, cells):
        """Replaces every cell (one terrain index per cell, row by row)."""
        self._set_cells(cells)
        self._blocked_cache.clear()
        self._bump()

    def get_cells(self):
        """A copy of the cells, row by row."""
        return bytes(self._cells)

    def _index(self, cell):
        cx, cy = cell
        cx = int(cx)
        cy = int(cy)
        if 0 <= cx < self.columns and 0 <= cy < self.rows:
            return cy * self.columns + cx
        return -1

    def get_cell(self, cell):
        """The terrain index of a cell; outside the grid, the outside terrain."""
        i = self._index(cell)
        return self._cells[i] if i >= 0 else self._outside

    def set_cell(self, cell, terrain):
        i = self._index(cell)
        if i < 0:
            raise IndexError("cell %r is outside the grid" % (cell,))
        if self._cells[i] != terrain:
            self._cells[i] = terrain
            self._blocked_cache.clear()
            self._bump()

    def is_cell_blocked(self, cell, collision_mask=1):
        """Whether the cell's terrain is on a layer in collision_mask."""
        return bool(self._layer_table[self.get_cell(cell) & 255] & collision_mask)

    def local_to_map(self, point):
        """The cell containing a pixel position (Godot's TileMapLayer name)."""
        x, y = point
        cs = self.cell_size
        return Vector2i(math.floor(x / cs), math.floor(y / cs))

    def map_to_local(self, cell):
        """The centre of a cell, in pixels."""
        cx, cy = cell
        cs = self.cell_size
        return Vector2((cx + 0.5) * cs, (cy + 0.5) * cs)

    def terrain_at(self, point):
        """The terrain index under a pixel position."""
        return self.get_cell(self.local_to_map(point))

    def speed_at(self, point):
        """The terrain speed factor under a pixel position."""
        x, y = point
        return self._speed_at(float(x), float(y))

    def _speed_at(self, x, y):
        cs = self.cell_size
        cx = int(x // cs)
        cy = int(y // cs)
        if 0 <= cx < self.columns and 0 <= cy < self.rows:
            return self._speed_table[self._cells[cy * self.columns + cx]]
        return self._outside_speed

    def _blocked(self, mask):
        """One byte per cell, 1 where terrain blocks mask; None if nothing does."""
        try:
            return self._blocked_cache[mask]
        except KeyError:
            pass
        table = bytes(1 if layer & mask else 0 for layer in self._layer_table)
        blocked = self._cells.translate(table)
        if blocked.find(1) < 0:
            blocked = None
        self._blocked_cache[mask] = blocked
        return blocked

    def blocked_map(self, collision_mask=1):
        """One byte per cell, 1 where terrain or a static body on a layer in
        collision_mask blocks it (a static body blocks every cell it touches).
        For pathfinding; cached until terrain or static bodies change."""
        key = ("blocked", collision_mask)
        result = self.cache.get(key)
        if result is not None:
            return result
        blocked = self._blocked(collision_mask)
        result = bytearray(blocked) if blocked is not None else bytearray(len(self._cells))
        cs = self.cell_size
        cols = self.columns
        rows = self.rows
        for static in self._statics:
            if not static._layer & collision_mask:
                continue
            x = static._x
            y = static._y
            for shape in static._shapes:
                r0 = max(0, math.floor((y + shape.y0) / cs))
                r1 = min(rows - 1, math.ceil((y + shape.y1) / cs) - 1)
                for row in range(r0, r1 + 1):
                    if shape.is_circle:
                        # The circle's widest extent within this row of cells.
                        ccx = x + shape.cx
                        ccy = y + shape.cy
                        top = row * cs
                        gap = top - ccy if ccy < top else (ccy - top - cs if ccy > top + cs else 0.0)
                        if gap >= shape.radius:
                            continue
                        half = math.sqrt(shape.radius * shape.radius - gap * gap)
                        left = ccx - half
                        right = ccx + half
                    else:
                        left = x + shape.x0
                        right = x + shape.x1
                    c0 = max(0, math.floor(left / cs))
                    c1 = min(cols - 1, math.ceil(right / cs) - 1)
                    if c0 <= c1:
                        base = row * cols
                        result[base + c0:base + c1 + 1] = b"\x01" * (c1 - c0 + 1)
        result = bytes(result)
        self.cache[key] = result
        return result

    ## Objects

    def add(self, obj):
        """Adds a StaticBody, Body or Area. Returns it."""
        if obj.grid is not None:
            raise ValueError("%r is already in a grid" % (obj,))
        obj.grid = self
        self._objects[obj] = None
        if obj.owner is not None:
            self._owners.setdefault(id(obj.owner), []).append(obj)
        self._link(obj, self._bucket_range(obj))
        if obj._is_area:
            self._area_count += 1
        if obj._is_static:
            self._statics[obj] = None
            self._bump()
        self._mark_dirty(obj)
        return obj

    def remove(self, obj):
        """Removes an object. Areas it was in, or that it detected, report the
        exit at the next step()."""
        if obj.grid is not self:
            raise ValueError("%r isn't in this grid" % (obj,))
        for area in list(obj._monitors):
            self._exit(area, obj)
        if obj._is_area:
            for other in list(obj._bodies) + list(obj._areas):
                self._exit(obj, other)
            self._area_count -= 1
        self._unlink(obj)
        del self._objects[obj]
        if obj.owner is not None:
            key = id(obj.owner)
            owned = self._owners.get(key)
            if owned is not None:
                owned.remove(obj)
                if not owned:
                    del self._owners[key]
        if obj._is_static:
            del self._statics[obj]
            self._bump()
        obj.grid = None
        obj._dirty = False
        obj._no_areas = None

    def remove_owner(self, owner):
        """Removes every object whose owner is `owner`."""
        for obj in self.objects_of(owner):
            self.remove(obj)

    def objects_of(self, owner):
        """The objects whose owner is `owner`."""
        return list(self._owners.get(id(owner), ()))

    def get_objects(self):
        return list(self._objects)

    def __contains__(self, obj):
        return obj in self._objects

    ## Spatial hash

    def _bucket_range(self, obj):
        inv = self._inv_bucket
        x = obj._x
        y = obj._y
        return (_floor((x + obj._lx0) * inv), _floor((y + obj._ly0) * inv),
                _floor((x + obj._lx1) * inv), _floor((y + obj._ly1) * inv))

    def _link(self, obj, keys):
        if obj._is_area:
            table = self._area_buckets
            self._area_version += 1
        else:
            table = self._solids
        bx0, by0, bx1, by1 = keys
        for by in range(by0, by1 + 1):
            row = by * _KEY
            for bx in range(bx0, bx1 + 1):
                bucket = table.get(row + bx)
                if bucket is None:
                    table[row + bx] = [obj]
                else:
                    bucket.append(obj)
        obj._bkeys = keys

    def _unlink(self, obj):
        if obj._is_area:
            table = self._area_buckets
            self._area_version += 1
        else:
            table = self._solids
        bx0, by0, bx1, by1 = obj._bkeys
        for by in range(by0, by1 + 1):
            row = by * _KEY
            for bx in range(bx0, bx1 + 1):
                bucket = table[row + bx]
                bucket.remove(obj)
                if not bucket:
                    del table[row + bx]
        obj._bkeys = None

    def _object_moved(self, obj):
        keys = self._bucket_range(obj)
        if keys != obj._bkeys:
            self._unlink(obj)
            self._link(obj, keys)
        self._object_changed(obj)

    def _object_changed(self, obj):
        self._mark_dirty(obj)
        if obj._is_static:
            self._bump()

    def _mark_dirty(self, obj):
        if self._area_count and not obj._dirty:
            obj._dirty = True
            self._dirty.append(obj)

    def _query(self, table, x0, y0, x1, y1, keys=None):
        """Objects in `table` whose bounding box overlaps the box, once each,
        or None if the buckets (keys, if the caller has them) were all empty."""
        self._stamp += 1
        stamp = self._stamp
        if keys is None:
            inv = self._inv_bucket
            keys = (_floor(x0 * inv), _floor(y0 * inv), _floor(x1 * inv), _floor(y1 * inv))
        bx0, by0, bx1, by1 = keys
        found = None
        for by in range(by0, by1 + 1):
            row = by * _KEY
            for bx in range(bx0, bx1 + 1):
                bucket = table.get(row + bx)
                if bucket is None:
                    continue
                if found is None:
                    found = []
                for obj in bucket:
                    if obj._stamp == stamp:
                        continue
                    obj._stamp = stamp
                    ox = obj._x
                    oy = obj._y
                    if ox + obj._lx0 < x1 and x0 < ox + obj._lx1 and oy + obj._ly0 < y1 and y0 < oy + obj._ly1:
                        found.append(obj)
        return found

    ## Areas

    def step(self):
        """Updates what every area detects and fires the enter and exit
        signals. Call it once per tick, after moving things."""
        dirty = self._dirty
        if dirty:
            self._dirty = []
            for obj in dirty:
                obj._dirty = False
                if obj.grid is self:
                    self._update_overlaps(obj)
        events = self._events
        if events:
            self._events = []
            for signal, other in events:
                signal.emit(other)

    def _update_overlaps(self, obj):
        x0 = obj._x + obj._lx0
        y0 = obj._y + obj._ly0
        x1 = obj._x + obj._lx1
        y1 = obj._y + obj._ly1
        layer = obj._layer
        is_area = obj._is_area

        # Areas detecting obj.
        found = {}
        if not is_area or obj._monitorable:
            keys = obj._bkeys
            candidates = self._query(self._area_buckets, x0, y0, x1, y1, keys)
            if candidates is None:
                # No area in its buckets: remember that, so moving within them skips this.
                obj._no_areas = (self._area_version, keys)
            else:
                obj._no_areas = None
                for area in candidates:
                    if area is not obj and area._monitoring and area._mask & layer and _objects_overlap(area, obj):
                        found[area] = None
        old = obj._monitors
        for area in found:
            if area not in old:
                self._enter(area, obj)
        for area in [a for a in old if a not in found]:
            self._exit(area, obj)

        if not is_area:
            return

        # What obj detects.
        found = {}
        if obj._monitoring:
            mask = obj._mask
            for other in self._query(self._solids, x0, y0, x1, y1) or ():
                if other._layer & mask and _objects_overlap(obj, other):
                    found[other] = None
            for other in self._query(self._area_buckets, x0, y0, x1, y1) or ():
                if (other is not obj and other._monitorable and other._layer & mask
                        and _objects_overlap(obj, other)):
                    found[other] = None
        for other in found:
            if other not in obj._bodies and other not in obj._areas:
                self._enter(obj, other)
        for other in [o for o in list(obj._bodies) + list(obj._areas) if o not in found]:
            self._exit(obj, other)

    def _enter(self, area, other):
        if other._is_area:
            area._areas[other] = None
            signal = area.area_entered
        else:
            area._bodies[other] = None
            signal = area.body_entered
        other._monitors[area] = None
        self._events.append((signal, other))

    def _exit(self, area, other):
        if other._is_area:
            area._areas.pop(other, None)
            signal = area.area_exited
        else:
            area._bodies.pop(other, None)
            signal = area.body_exited
        other._monitors.pop(area, None)
        self._events.append((signal, other))

    ## Sweeping a body

    def _cast(self, body, mx, my):
        """The earliest hit for body moving by (mx, my), or None:
        (t, nx, ny, depth, collider, collider_shape, cell, own_shape, geometry)
        where geometry is (True, cx, cy, r) or (False, x0, y0, x1, y1)."""
        best_t = 2.0
        best = None
        x = body._x
        y = body._y
        mask = body._mask
        blocked = self._blocked(mask) if mask & self._terrain_layers else None
        outside = mask & self._outside_layer
        exceptions = body._exceptions
        cs = self.cell_size
        inv_cell = self._inv_cell
        cols = self.columns
        rows = self.rows
        solids = self._solids
        inv = self._inv_bucket

        for shape in body._shapes:
            circle = shape.is_circle
            if circle:
                r = shape.radius
                cx = x + shape.cx
                cy = y + shape.cy
            ax0 = x + shape.x0
            ay0 = y + shape.y0
            ax1 = x + shape.x1
            ay1 = y + shape.y1
            if mx < 0.0:
                sx0 = ax0 + mx
                sx1 = ax1
            else:
                sx0 = ax0
                sx1 = ax1 + mx
            if my < 0.0:
                sy0 = ay0 + my
                sy1 = ay1
            else:
                sy0 = ay0
                sy1 = ay1 + my

            # Terrain: the blocked cells under the swept box.
            if blocked is not None:
                c0 = _floor(sx0 * inv_cell)
                c1 = _floor(sx1 * inv_cell)
                if c0 < 0:
                    c0 = 0
                if c1 >= cols:
                    c1 = cols - 1
                if c0 <= c1:
                    r0 = _floor(sy0 * inv_cell)
                    r1 = _floor(sy1 * inv_cell)
                    if r0 < 0:
                        r0 = 0
                    if r1 >= rows:
                        r1 = rows - 1
                    for row in range(r0, r1 + 1):
                        base = row * cols
                        end = base + c1 + 1
                        i = blocked.find(1, base + c0, end)
                        while i >= 0:
                            col = i - base
                            gx0 = col * cs
                            gy0 = row * cs
                            gx1 = gx0 + cs
                            gy1 = gy0 + cs
                            if circle:
                                hit = _sweep_circle_box(cx, cy, r, mx, my, gx0, gy0, gx1, gy1)
                            else:
                                hit = _sweep_box_box(ax0, ay0, ax1, ay1, mx, my, gx0, gy0, gx1, gy1)
                            if hit is not None and hit[0] < best_t:
                                best_t = hit[0]
                                best = hit + (self, None, (col, row), shape, (False, gx0, gy0, gx1, gy1))
                            i = blocked.find(1, i + 1, end)

            # Beyond the edges, when the outside terrain blocks.
            if outside:
                if sx0 < 0.0 or sy0 < 0.0 or sx1 > self._width or sy1 > self._height:
                    for gx0, gy0, gx1, gy1 in self._outside_boxes:
                        if circle:
                            hit = _sweep_circle_box(cx, cy, r, mx, my, gx0, gy0, gx1, gy1)
                        else:
                            hit = _sweep_box_box(ax0, ay0, ax1, ay1, mx, my, gx0, gy0, gx1, gy1)
                        if hit is not None and hit[0] < best_t:
                            best_t = hit[0]
                            best = hit + (self, None, None, shape, (False, gx0, gy0, gx1, gy1))

            # Other bodies.
            self._stamp += 1
            stamp = self._stamp
            bx0 = _floor(sx0 * inv)
            bx1 = _floor(sx1 * inv) + 1
            for by in range(_floor(sy0 * inv), _floor(sy1 * inv) + 1):
                key_row = by * _KEY
                for bx in range(bx0, bx1):
                    bucket = solids.get(key_row + bx)
                    if bucket is None:
                        continue
                    for other in bucket:
                        if other._stamp == stamp:
                            continue
                        other._stamp = stamp
                        if other is body or not other._layer & mask:
                            continue
                        if exceptions is not None and other in exceptions:
                            continue
                        ox = other._x
                        oy = other._y
                        if (ox + other._lx0 >= sx1 or ox + other._lx1 <= sx0
                                or oy + other._ly0 >= sy1 or oy + other._ly1 <= sy0):
                            continue
                        for oshape in other._shapes:
                            if oshape.is_circle:
                                ocx = ox + oshape.cx
                                ocy = oy + oshape.cy
                                orad = oshape.radius
                                if circle:
                                    hit = _sweep_circle_circle(cx, cy, r, mx, my, ocx, ocy, orad)
                                else:
                                    # The circle moving the other way, against our box.
                                    hit = _sweep_circle_box(ocx, ocy, orad, -mx, -my, ax0, ay0, ax1, ay1)
                                    if hit is not None:
                                        hit = (hit[0], -hit[1], -hit[2], hit[3])
                                if hit is not None and hit[0] < best_t:
                                    best_t = hit[0]
                                    best = hit + (other, oshape, None, shape, (True, ocx, ocy, orad))
                            else:
                                gx0 = ox + oshape.x0
                                gy0 = oy + oshape.y0
                                gx1 = ox + oshape.x1
                                gy1 = oy + oshape.y1
                                if circle:
                                    hit = _sweep_circle_box(cx, cy, r, mx, my, gx0, gy0, gx1, gy1)
                                else:
                                    hit = _sweep_box_box(ax0, ay0, ax1, ay1, mx, my, gx0, gy0, gx1, gy1)
                                if hit is not None and hit[0] < best_t:
                                    best_t = hit[0]
                                    best = hit + (other, oshape, None, shape, (False, gx0, gy0, gx1, gy1))
        return best

    ## Queries

    def raycast(self, from_point, to_point, collision_mask=ALL_LAYERS, exclude=(),
                collide_with_bodies=True, collide_with_areas=False, hit_from_inside=False):
        """The first thing on the segment from_point -> to_point: a RayHit, or
        None. Terrain counts as a body. exclude lists objects to ignore.

        A ray starting inside something ignores it (for terrain, the solid
        cells it starts in), unless hit_from_inside, which reports a hit at
        from_point with a zero normal."""
        fx, fy = from_point
        tx, ty = to_point
        fx = float(fx)
        fy = float(fy)
        dx = float(tx) - fx
        dy = float(ty) - fy

        best_t = 1.0
        best = None
        if collide_with_bodies:
            hit = self._ray_terrain(fx, fy, dx, dy, collision_mask, hit_from_inside)
            if hit is not None:
                best_t = hit[0]
                best = (hit[0], hit[1], hit[2], self, None, hit[3])

        tables = []
        if collide_with_bodies:
            tables.append(self._solids)
        if collide_with_areas:
            tables.append(self._area_buckets)
        if tables:
            exclude = set(exclude) if exclude else ()
            self._stamp += 1
            stamp = self._stamp
            inv = self._inv_bucket
            for bx, by, t_enter in _walk_cells(fx * inv, fy * inv, dx * inv, dy * inv):
                if t_enter > best_t:
                    break
                for table in tables:
                    bucket = table.get(by * _KEY + bx)
                    if bucket is None:
                        continue
                    for obj in bucket:
                        if obj._stamp == stamp:
                            continue
                        obj._stamp = stamp
                        if not obj._layer & collision_mask or (exclude and obj in exclude):
                            continue
                        ox = obj._x
                        oy = obj._y
                        for shape in obj._shapes:
                            if shape.is_circle:
                                hit = _ray_circle(fx, fy, dx, dy, ox + shape.cx, oy + shape.cy, shape.radius,
                                                  best_t, hit_from_inside)
                            else:
                                hit = _ray_box(fx, fy, dx, dy, ox + shape.x0, oy + shape.y0, ox + shape.x1,
                                               oy + shape.y1, best_t, hit_from_inside)
                            if hit is not None and (best is None or hit[0] < best_t):
                                best_t = hit[0]
                                best = (hit[0], hit[1], hit[2], obj, shape, None)
                # Zero-length ray: only its own bucket.
                if not dx and not dy:
                    break

        if best is None:
            return None
        t, nx, ny, collider, shape, cell = best
        return RayHit(Vector2(fx + dx * t, fy + dy * t), Vector2(nx, ny), collider, shape,
                      Vector2i(cell[0], cell[1]) if cell is not None else None)

    def _ray_terrain(self, fx, fy, dx, dy, mask, hit_from_inside):
        """(t, nx, ny, cell or None) where the ray first enters blocking
        terrain, or None."""
        blocked = self._blocked(mask) if mask & self._terrain_layers else None
        outside = bool(mask & self._outside_layer)
        if blocked is None and not outside:
            return None
        cs = self.cell_size
        cols = self.columns
        rows = self.rows
        w = cols * cs
        h = rows * cs

        # Where the segment is inside the grid: t_in to t_out.
        t_in = 0.0
        t_out = 1.0
        in_axis = out_axis = -1
        for p, d, size, axis in ((fx, dx, w, 0), (fy, dy, h, 1)):
            if d:
                ta = -p / d
                tb = (size - p) / d
                if ta > tb:
                    ta, tb = tb, ta
                if ta > t_in:
                    t_in = ta
                    in_axis = axis
                if tb < t_out:
                    t_out = tb
                    out_axis = axis
            elif p < 0.0 or p >= size:
                t_in = INF

        start_inside = 0.0 <= fx < w and 0.0 <= fy < h
        if start_inside:
            col = min(int(fx // cs), cols - 1)
            row = min(int(fy // cs), rows - 1)
            solid = blocked is not None and blocked[row * cols + col]
            start_cell = (col, row)
        else:
            solid = outside
            start_cell = None
        if solid and hit_from_inside:
            return (0.0, 0.0, 0.0, start_cell)
        # Ignore the solid the ray starts in, until it reaches open cells.
        skipping = solid

        if t_in > t_out:
            # The segment never crosses the grid.
            return None

        if blocked is None:
            skipping = False
        else:
            t = t_in
            col = min(max(int((fx + dx * t) // cs), 0), cols - 1)
            row = min(max(int((fy + dy * t) // cs), 0), rows - 1)
            step_x = 1 if dx > 0 else -1
            step_y = 1 if dy > 0 else -1
            if dx:
                next_x = (((col + 1) if dx > 0 else col) * cs - fx) / dx
                delta_x = abs(cs / dx)
            else:
                next_x = delta_x = INF
            if dy:
                next_y = (((row + 1) if dy > 0 else row) * cs - fy) / dy
                delta_y = abs(cs / dy)
            else:
                next_y = delta_y = INF
            axis = in_axis if t_in > 0.0 else -1
            while True:
                if blocked[row * cols + col]:
                    if not skipping:
                        if axis == 0:
                            return (t, -float(step_x), 0.0, (col, row))
                        if axis == 1:
                            return (t, 0.0, -float(step_y), (col, row))
                        return (t, 0.0, 0.0, (col, row))
                else:
                    skipping = False
                if next_x < next_y:
                    t = next_x
                    col += step_x
                    next_x += delta_x
                    axis = 0
                else:
                    t = next_y
                    row += step_y
                    next_y += delta_y
                    axis = 1
                if t > t_out or not (0 <= col < cols and 0 <= row < rows):
                    break

        # Leaving the grid into blocking outside terrain.
        if outside and not skipping and out_axis >= 0 and t_out <= 1.0:
            ex = fx + dx
            ey = fy + dy
            if not (0.0 <= ex < w and 0.0 <= ey < h) or t_out < 1.0:
                if out_axis == 0:
                    return (t_out, -1.0 if dx > 0 else 1.0, 0.0, None)
                return (t_out, 0.0, -1.0 if dy > 0 else 1.0, None)
        return None

    def intersect_point(self, point, collision_mask=ALL_LAYERS, collide_with_bodies=True,
                        collide_with_areas=False, exclude=()):
        """The objects with a shape containing point (terrain isn't included:
        see get_cell / terrain_at)."""
        px, py = point
        px = float(px)
        py = float(py)
        found = []
        tables = []
        if collide_with_bodies:
            tables.append(self._solids)
        if collide_with_areas:
            tables.append(self._area_buckets)
        for table in tables:
            for obj in self._query(table, px - 1e-9, py - 1e-9, px + 1e-9, py + 1e-9) or ():
                if not obj._layer & collision_mask or (exclude and obj in exclude):
                    continue
                for shape in obj._shapes:
                    if _shape_has_point(shape, obj._x, obj._y, px, py):
                        found.append(obj)
                        break
        return found

    def intersect_shape(self, shape, position, collision_mask=ALL_LAYERS, collide_with_bodies=True,
                        collide_with_areas=False, exclude=(), max_results=32):
        """The objects overlapping shape placed at position (terrain isn't
        included: see is_free)."""
        x, y = position
        x = float(x)
        y = float(y)
        found = []
        tables = []
        if collide_with_bodies:
            tables.append(self._solids)
        if collide_with_areas:
            tables.append(self._area_buckets)
        for table in tables:
            for obj in self._query(table, x + shape.x0, y + shape.y0, x + shape.x1, y + shape.y1) or ():
                if not obj._layer & collision_mask or (exclude and obj in exclude):
                    continue
                for oshape in obj._shapes:
                    if _shapes_overlap(shape, x, y, oshape, obj._x, obj._y):
                        found.append(obj)
                        if len(found) >= max_results:
                            return found
                        break
        return found

    def is_free(self, shape, position, collision_mask=1, exclude=()):
        """Whether shape placed at position overlaps nothing that would block
        a body with this collision_mask: terrain (including outside the grid),
        static bodies and bodies. For checking a spawn point or a drop spot."""
        x, y = position
        x = float(x)
        y = float(y)
        x0 = x + shape.x0
        y0 = y + shape.y0
        x1 = x + shape.x1
        y1 = y + shape.y1
        cs = self.cell_size
        cols = self.columns
        rows = self.rows
        if collision_mask & self._outside_layer:
            if x0 < 0.0 or y0 < 0.0 or x1 > cols * cs or y1 > rows * cs:
                return False
        blocked = self._blocked(collision_mask) if collision_mask & self._terrain_layers else None
        if blocked is not None:
            c0 = max(0, int(x0 // cs))
            c1 = min(cols - 1, int(x1 // cs))
            for row in range(max(0, int(y0 // cs)), min(rows - 1, int(y1 // cs)) + 1):
                base = row * cols
                i = blocked.find(1, base + c0, base + c1 + 1) if c0 <= c1 else -1
                while i >= 0:
                    gx0 = (i - base) * cs
                    gy0 = row * cs
                    if _shape_overlaps_box(shape, x, y, gx0, gy0, gx0 + cs, gy0 + cs):
                        return False
                    i = blocked.find(1, i + 1, base + c1 + 1)
        return not self.intersect_shape(shape, position, collision_mask, True, False, exclude, 1)
