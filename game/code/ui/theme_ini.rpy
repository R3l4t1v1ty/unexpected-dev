## ui colors and assets, in one place.
##
## Every image ui draws (besides Ren'Py's stock gui/ files) is defined here.
## Until the art and its folder layout exist, these are placeholders built in
## code: change a define to an image path (or a Frame of one) to swap in art.
##
## Runs at -400 so styles and screens (0) can use these values.

init offset = -400

init python in uix:

    import store

    def placeholder(label, size, color="#2a1f27", text_color="#cc0066"):
        """
        A flat box with a label, standing in for art that doesn't exist yet.
        `size` is (width, height) in pixels.
        """

        return store.Fixed(
            store.Solid(color),
            store.Text(label, size=20, color=text_color, align=(0.5, 0.5)),
            xysize=size,
            )


## Colors ######################################################################

define uix.accent = "#cc0066"
define uix.dark = "#191316"
define uix.idle = "#888888"
define uix.text = "#ffffff"
define uix.muted = "#cccccc"
define uix.locked = "#8888887f"


## Game menu ###################################################################

## Sidebar width, by layout.
define uix.menu_sidebar_width = 400
define uix.menu_sidebar_width_small = 510


## Main menu ###################################################################

## Arrows shown beside the focused main-menu button.
define uix.mm_arrow_left = Text("›", font="DejaVuSans.ttf", size=48, color="#cc0066")
define uix.mm_arrow_right = Text("‹", font="DejaVuSans.ttf", size=48, color="#cc0066")

## The panel behind the main-menu buttons, the logo above it, and the link bar.
define uix.mm_buttons_bg = Solid("#191316d0")
define uix.mm_logo = uix.placeholder("logo", (400, 110), color="#00000000")
define uix.mm_link_bar = Solid("#191316d0")

## The corner triangle that hides the interface and opens the art-set picker.
define uix.mm_corner = Text("◢", font="DejaVuSans.ttf", size=72, color="#cc0066")

## Sound played when a main-menu button gains focus. None for silence.
define uix.mm_hover_sound = None


## Textbox #####################################################################

## Skin backgrounds: normal lines and thought lines. A Frame of an image keeps
## the corners when the player resizes the textbox; a Solid stretches fine.
define uix.tb_simple = Solid("#000000")
define uix.tb_simple_thought = Solid("#1b1430")
define uix.tb_fade = Solid("#14080f")
define uix.tb_fade_thought = Solid("#1a1033")
define uix.tb_fancy = Solid("#2a0a1c")
define uix.tb_fancy_thought = Solid("#241040")


## HUD #########################################################################

define uix.hud_window_bg = Solid("#191316e6")
define uix.hud_title_bg = Solid("#cc0066")
define uix.hud_slot_bg = Solid("#ffffff1a")
define uix.hud_slot_hover_bg = Solid("#cc006660")
define uix.hud_selected_bg = Solid("#cc0066a0")
