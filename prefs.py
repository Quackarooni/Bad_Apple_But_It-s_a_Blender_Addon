import os
import bpy
import numpy as np

from bpy import context
from bpy.types import Operator, AddonPreferences
from bpy.props import BoolProperty, IntProperty

width = 42
height = 24

ADDON_PATH = os.path.dirname(__file__)
CACHE_PATH = os.path.join(ADDON_PATH, "frames\\")


def np_array_from_image(name):
    def flip_index(i):
        inverted_index = width * height - i - 1
        row_index = inverted_index % width
        inverted_row_index = width - row_index - 1
        return inverted_index - row_index + inverted_row_index

    path = os.path.join(CACHE_PATH, name + ".jpg")

    image = bpy.data.images.load(path)
    raw_array = np.asarray(image.pixels)
    pixel_array = [row[0] for row in np.reshape(raw_array, (width * height, 4))]

    flipped_pixel_array = [pixel_array[flip_index(i)] for i in range(width * height)]

    return flipped_pixel_array


def update_props(self, context):
    prefs = fetch_user_prefs()

    frame = getattr(prefs, "frame_num")
    pixels = np_array_from_image(f"{frame}")

    for index, row in enumerate(pixels):
        value = row >= 0.5
        name = f"prop_{index}"
        setattr(prefs, name, value)

    for region in context.area.regions:
        region.tag_redraw()


def fetch_user_prefs(attr_id=None):
    prefs = context.preferences.addons[__package__].preferences
    if attr_id is None:
        return prefs
    else:
        return getattr(prefs, attr_id)


class BadAppleDisplay(AddonPreferences):
    bl_idname = __package__

    is_playing: BoolProperty()
    frame_num: IntProperty(name="frame_num", min=1, max=6572, update=update_props)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        split = row.split()
        subcol1 = split.column()
        subcol2 = split.column()

        if not self.is_playing:
            subcol1.operator("bad_apple.play_animation", icon="PLAY")
        else:
            subcol1.operator("bad_apple.pause_animation", icon="PAUSE")

        subcol2.enabled = not self.is_playing
        subcol2.prop(self, "frame_num", text="Frame")

        col = layout.column()
        col.use_property_split = False
        col.scale_x = 0.5

        for y in range(height):
            row = col.row()
            row.alignment = "CENTER"
            for x in range(width):
                row.prop(self, f"prop_{x+width*(y)}", text="")
                row.separator(factor=0.25)


class BAD_APPLE_OT_PLAY_ANIMATION(Operator):
    """Plays the Bad Apple Animation"""

    bl_idname = "bad_apple.play_animation"
    bl_label = "Play Animation"

    @classmethod
    def poll(cls, context):
        return True

    def modal(self, context, event):
        prefs = fetch_user_prefs()

        if event.type in {"TIMER"}:
            prefs.frame_num = prefs.frame_num + 1

        if (
            event.type in {"RIGHTMOUSE", "ESC"}
            or prefs.frame_num >= 6572
            or not prefs.is_playing
        ):
            prefs.is_playing = False

            context.window.cursor_modal_restore()
            context.window_manager.event_timer_remove(self._timer)
            context.area.tag_redraw()
            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        context.window.cursor_modal_set("CROSSHAIR")

        prefs = fetch_user_prefs()
        prefs.is_playing = True

        self._timer = context.window_manager.event_timer_add(
            1 / 30, window=context.window
        )
        return {"RUNNING_MODAL"}


class BAD_APPLE_OT_PAUSE_ANIMATION(Operator):
    """Pauses the Bad Apple Animation"""

    bl_idname = "bad_apple.pause_animation"
    bl_label = "Pause Animation"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        prefs = fetch_user_prefs()
        prefs.is_playing = False

        return {"FINISHED"}


for i in range(width * height):
    name = f"prop_{i}"
    BadAppleDisplay.__annotations__[name] = BoolProperty()


classes = (
    BadAppleDisplay,
    BAD_APPLE_OT_PLAY_ANIMATION,
    BAD_APPLE_OT_PAUSE_ANIMATION,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
