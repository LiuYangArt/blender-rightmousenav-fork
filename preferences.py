import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
)
from bpy.types import AddonPreferences

def draw_cam_lock(self, context):
    preferences = context.preferences
    addon_prefs = preferences.addons[__package__].preferences
    cam_nav = addon_prefs.disable_camera_navigation

    layout = self.layout

    row = layout.row(align=True)
    row.alert = cam_nav
    row.operator(text="", operator="rmn.toggle_cam_navigation", icon="CAMERA_DATA")


def cam_lock_update(self, context):
    preferences = context.preferences
    addon_prefs = preferences.addons[__package__].preferences

    if addon_prefs.show_cam_lock_ui:
        bpy.types.VIEW3D_HT_tool_header.prepend(draw_cam_lock)
    else:
        bpy.types.VIEW3D_HT_tool_header.remove(draw_cam_lock)


def node_keymap(keyconfig):
    for key in keyconfig.keymaps["Node Editor"].keymap_items:
        if key.idname == "wm.call_menu" and key.type == "RIGHTMOUSE":
            key.active = not key.active


def update_node_keymap(self, context):
    wm = context.window_manager
    active_keyconfig = wm.keyconfigs.active
    blender_keyconfig = wm.keyconfigs["Blender"]
    user_keyconfig = wm.keyconfigs["Blender user"]

    try:
        node_keymap(active_keyconfig)
    except KeyError:
        node_keymap(blender_keyconfig)
    finally:
        node_keymap(user_keyconfig)

    addon_prefs = context.preferences.addons[__package__].preferences
    addon_keymap = wm.keyconfigs.addon.keymaps.get("Node Editor")
    if not addon_keymap:
        return

    for key in addon_keymap.keymap_items:
        if key.idname == "rmn.right_mouse_navigation" and key.type == "RIGHTMOUSE":
            key.active = addon_prefs.enable_for_node_editors


class RightMouseNavigationPreferences(AddonPreferences):
    bl_idname = __package__

    navigation_mode: EnumProperty(
        name="Navigation Mode",
        description="Choose how right-click drag navigates the viewport",
        items=[
            (
                "WALK",
                "Walk",
                "First-person walk navigation (default Blender behavior)",
            ),
            (
                "ORBIT",
                "Orbit",
                "Orbit around view center (like middle-mouse-button)",
            ),
        ],
        default="WALK",
    )

    time: FloatProperty(
        name="Time Threshold",
        description="How long you have hold right mouse to open menu",
        default=1.0,
        min=0.1,
        max=10,
    )

    reset_cursor_on_exit: BoolProperty(
        name="Reset Cursor on Exit",
        description="After exiting navigation, this determines if the cursor stays "
        "where RMB was clicked (if unchecked) or resets to the center (if checked)",
        default=False,
    )

    return_to_ortho_on_exit: BoolProperty(
        name="Return to Orthographic on Exit",
        description="After exiting navigation, this determines if the Viewport "
        "returns to Orthographic view (if checked) or remains in Perspective view (if unchecked)",
        default=True,
    )

    enable_for_node_editors: BoolProperty(
        name="Enable for Node Editors",
        description="Right Mouse will pan the view / open the Node Add/Search Menu",
        default=False,
        update=update_node_keymap,
    )

    disable_camera_navigation: BoolProperty(
        name="Disable Navigation for Camera View",
        description="Enable if you only want to navigate your scene, and not affect Camera Transform",
        default=False,
    )

    show_cam_lock_ui: BoolProperty(
        name="Show Camera Navigation Lock button",
        description="Displays the Camera Navigation Lock button in the 3D Viewport",
        default=False,
        update=cam_lock_update,
    )

    def draw(self, context):
        layout = self.layout

        # Navigation Mode & Menu / Movement Boxes
        row = layout.row()
        box = row.box()
        box.label(text="Navigation Mode", icon="ORIENTATION_GIMBAL")
        box.prop(self, "navigation_mode", text="")
        box = row.box()
        box.label(text="Menu / Movement", icon="DRIVER_DISTANCE")
        box.prop(self, "time")

        # Cursor & View Boxes
        row = layout.row()
        box = row.box()
        box.label(text="Cursor", icon="ORIENTATION_CURSOR")
        box.prop(self, "reset_cursor_on_exit")
        box = row.box()
        box.label(text="View", icon="VIEW3D")
        box.prop(self, "return_to_ortho_on_exit")

        # Camera Box
        row = layout.row()
        box = row.box()
        box.label(text="Camera", icon="CAMERA_DATA")
        row = box.row()
        row.prop(self, "disable_camera_navigation")
        row.prop(self, "show_cam_lock_ui")

        # Node Editor Box
        row = layout.row()
        box = row.box()
        box.label(text="Node Editor", icon="NODETREE")
        box.prop(self, "enable_for_node_editors")

        # Keymap Customization
        import rna_keymap_ui

        nav_names = [
            "FORWARD",
            "FORWARD_STOP",
            "BACKWARD",
            "BACKWARD_STOP",
            "LEFT",
            "LEFT_STOP",
            "RIGHT",
            "RIGHT_STOP",
            "UP",
            "UP_STOP",
            "DOWN",
            "DOWN_STOP",
            "LOCAL_UP",
            "LOCAL_UP_STOP",
            "LOCAL_DOWN",
            "LOCAL_DOWN_STOP",
        ]

        wm = bpy.context.window_manager
        active_keyconfig = wm.keyconfigs.active
        blender_keyconfig = wm.keyconfigs["Blender"]
        user_keyconfig = wm.keyconfigs["Blender user"]

        addon_keymaps = []

        def walk_keymaps(keyconfig):
            walk_km = keyconfig.keymaps["View3D Walk Modal"]

            for key in walk_km.keymap_items:
                addon_keymaps.append((walk_km, key))

        try:
            walk_keymaps(active_keyconfig)
        except KeyError:
            walk_keymaps(blender_keyconfig)
        finally:
            walk_keymaps(user_keyconfig)

        # Navigation Keymap Box
        header, panel = layout.panel(idname="keymap", default_closed=True)
        header.label(text="Navigation Keymap")

        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user
        old_km_name = ""
        get_kmi_l = []
        for km_add, kmi_add in addon_keymaps:
            for km_con in kc.keymaps:
                if km_add.name == km_con.name:
                    km = km_con
                    break

            for kmi_con in km.keymap_items:
                if kmi_add.idname == kmi_con.idname:
                    if kmi_add.name == kmi_con.name and kmi_con.propvalue in nav_names:
                        get_kmi_l.append((km, kmi_con))

        get_kmi_l = sorted(set(get_kmi_l), key=get_kmi_l.index)

        if panel:
            col = panel.column(align=True)
            addon_keyconfig = wm.keyconfigs.addon
            trigger_km = addon_keyconfig.keymaps.get("3D View")
            if trigger_km:
                for trigger_kmi in trigger_km.keymap_items:
                    if trigger_kmi.idname == "rmn.right_mouse_navigation":
                        col.label(text="UE Navigation Trigger", icon="MOUSE_RMB")
                        col.context_pointer_set("keymap", trigger_km)
                        rna_keymap_ui.draw_kmi([], addon_keyconfig, trigger_km, trigger_kmi, col, 0)
                        col.separator()
                        break

            for km, kmi in get_kmi_l:
                if km.name != old_km_name:
                    col.label(text=str(km.name), icon="DOT")
                col.context_pointer_set("keymap", km)
                rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
                col.separator()
                old_km_name = km.name
