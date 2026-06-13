import bpy

from .operators import (
    RMN_OT_right_mouse_navigation,
    RMN_OT_toggle_cam_navigation,
)
from .preferences import RightMouseNavigationPreferences

addon_keymaps = []

classes = [
    RightMouseNavigationPreferences,
    RMN_OT_right_mouse_navigation,
    RMN_OT_toggle_cam_navigation,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    if bpy.app.background:
        return

    wm = bpy.context.window_manager
    addon_kc = wm.keyconfigs.addon
    addon_prefs = bpy.context.preferences.addons[__package__].preferences

    km = addon_kc.keymaps.new(
        name="3D View",
        space_type="VIEW_3D",
    )
    kmi = km.keymap_items.new(
        "rmn.right_mouse_navigation",
        "RIGHTMOUSE",
        "PRESS",
    )
    kmi.active = False

    km2 = addon_kc.keymaps.new(
        name="Node Editor",
        space_type="NODE_EDITOR",
    )
    kmi2 = km2.keymap_items.new(
        "rmn.right_mouse_navigation",
        "RIGHTMOUSE",
        "PRESS",
    )
    kmi2.active = addon_prefs.enable_for_node_editors

    addon_keymaps.append((km, kmi))
    addon_keymaps.append((km2, kmi2))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    if bpy.app.background:
        return

    for km, kmi_orig in addon_keymaps:
        try:
            km.keymap_items.remove(kmi_orig)
        except Exception as e:
            print(
                f"[UE Navigation] Could not remove keymap item {getattr(kmi_orig, 'idname', 'unknown')} from {km.name}: {e}"
            )
    addon_keymaps.clear()


if __name__ == "__main__":
    register()