import bpy
from bpy.types import Operator


class RMN_OT_right_mouse_navigation(Operator):
    """Timer that decides whether to display a menu after Right Click"""

    bl_idname = "rmn.right_mouse_navigation"
    bl_label = "UE Navigation"
    bl_options = {"REGISTER", "UNDO"}

    _timer = None
    _count = 0
    _finished = False
    _callMenu = False
    _back_to_ortho = False
    _trigger_type = "RIGHTMOUSE"
    _walk_confirm_state = None
    _supported_trigger_types = {
        "LEFTMOUSE",
        "MIDDLEMOUSE",
        "RIGHTMOUSE",
        "BUTTON4MOUSE",
        "BUTTON5MOUSE",
        "BUTTON6MOUSE",
        "BUTTON7MOUSE",
        "PEN",
        "ERASER",
    }
    menu_by_mode = {
        "OBJECT": "VIEW3D_MT_object_context_menu",
        "EDIT_MESH": "VIEW3D_MT_edit_mesh_context_menu",
        "EDIT_SURFACE": "VIEW3D_MT_edit_surface",
        "EDIT_TEXT": "VIEW3D_MT_edit_font_context_menu",
        "EDIT_ARMATURE": "VIEW3D_MT_edit_armature",
        "EDIT_CURVE": "VIEW3D_MT_edit_curve_context_menu",
        "EDIT_METABALL": "VIEW3D_MT_edit_metaball_context_menu",
        "EDIT_LATTICE": "VIEW3D_MT_edit_lattice_context_menu",
        "POSE": "VIEW3D_MT_pose_context_menu",
        "PAINT_VERTEX": "VIEW3D_PT_paint_vertex_context_menu",
        "PAINT_WEIGHT": "VIEW3D_PT_paint_weight_context_menu",
        "PAINT_TEXTURE": "VIEW3D_PT_paint_texture_context_menu",
        "SCULPT": "VIEW3D_PT_sculpt_context_menu",
    }

    def modal(self, context, event):
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        enable_nodes = addon_prefs.enable_for_node_editors

        space_type = context.space_data.type

        if space_type == "VIEW_3D":
            # Check if the Viewport is Perspective or Orthographic
            if not bpy.context.region_data.is_perspective:
                self._back_to_ortho = addon_prefs.return_to_ortho_on_exit

        # The _finished Boolean acts as a flag to exit the modal loop,
        # it is not made True until after the cancel function is called
        if self._finished:

            def reset_cursor():
                # Reset blender window cursor to previous position
                area = context.area
                x = area.x
                y = area.y
                x += int(area.width / 2)
                y += int(area.height / 2)
                bpy.context.window.cursor_warp(x, y)

            if self._callMenu:
                # Always reset the cursor if menu is called, as that implies a canceled navigation
                if addon_prefs.reset_cursor_on_exit and not space_type == "NODE_EDITOR":
                    reset_cursor()
                self.callMenu(context)
            else:
                # Exit of a full navigation. Only reset the cursor if the preference is enabled
                if addon_prefs.reset_cursor_on_exit:
                    reset_cursor()

            if self._back_to_ortho:
                bpy.ops.view3d.view_persportho()

            self.cancel(context)
            self.restore_walk_confirm_keymap()
            return {"CANCELLED"}

        if space_type == "VIEW_3D" or space_type == "NODE_EDITOR" and enable_nodes:
            if event.type == self._trigger_type and event.value in {"RELEASE"}:
                # This brings back our mouse cursor to use with the menu
                context.window.cursor_modal_restore()
                # If the length of time you've been holding down the trigger is shorter
                # than the threshold value, then set flag to call a context menu.
                if self._count < addon_prefs.time:
                    self._callMenu = True
                # Let Blender navigation see the release before cleanup.
                self._finished = True
                return {"PASS_THROUGH"}

            if event.type == "TIMER":
                if self._count <= addon_prefs.time:
                    self._count += 0.1
            return {"PASS_THROUGH"}

    def set_walk_confirm_to_trigger(self, context):
        if self._trigger_type not in self._supported_trigger_types:
            raise RuntimeError(
                f"Unsupported UE Navigation trigger for Walk navigation: {self._trigger_type}"
            )

        wm = context.window_manager
        self._walk_confirm_state = []

        for keyconfig in (
            wm.keyconfigs.active,
            wm.keyconfigs["Blender"],
            wm.keyconfigs["Blender user"],
        ):
            try:
                walk_km = keyconfig.keymaps["View3D Walk Modal"]
            except KeyError:
                continue

            for key in walk_km.keymap_items:
                if key.propvalue == "CONFIRM" and key.active:
                    self._walk_confirm_state.append(
                        (
                            key,
                            key.type,
                            key.value,
                            key.any,
                            key.shift,
                            key.ctrl,
                            key.alt,
                            key.oskey,
                        )
                    )
                    key.type = self._trigger_type
                    key.value = "RELEASE"
                    key.any = True
                    key.shift = False
                    key.ctrl = False
                    key.alt = False
                    key.oskey = False
                    return

    def restore_walk_confirm_keymap(self):
        if not self._walk_confirm_state:
            return

        for (
            key,
            key_type,
            value,
            any_key,
            shift,
            ctrl,
            alt,
            oskey,
        ) in self._walk_confirm_state:
            key.type = key_type
            key.value = value
            key.any = any_key
            key.shift = shift
            key.ctrl = ctrl
            key.alt = alt
            key.oskey = oskey

        self._walk_confirm_state = None

    def callMenu(self, context):
        wm = context.window_manager
        blender_keyconfig = wm.keyconfigs["Blender"]

        select_mouse = blender_keyconfig.preferences.select_mouse
        space_type = context.space_data.type

        if select_mouse == "LEFT":
            if space_type == "NODE_EDITOR":
                node_tree = context.space_data.node_tree
                if node_tree:
                    if node_tree.nodes.active is not None and node_tree.nodes.active.select:
                        bpy.ops.wm.call_menu(name="NODE_MT_context_menu")
                    else:
                        bpy.ops.wm.search_single_menu("INVOKE_DEFAULT", menu_idname="NODE_MT_add")
            else:
                try:
                    bpy.ops.wm.call_menu(name=self.menu_by_mode[context.mode])
                except RuntimeError:
                    bpy.ops.wm.call_panel(name=self.menu_by_mode[context.mode])
        else:
            if space_type == "VIEW_3D":
                bpy.ops.view3d.select("INVOKE_DEFAULT")

    def invoke(self, context, event):
        self._trigger_type = event.type
        self._walk_confirm_state = None

        if self._trigger_type not in self._supported_trigger_types:
            self.report(
                {"ERROR"},
                "UE Navigation trigger must be a mouse button; keyboard keys cannot use hold-to-release Walk navigation.",
            )
            return {"CANCELLED"}

        return self.execute(context)

    def execute(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        enable_nodes = addon_prefs.enable_for_node_editors
        disable_camera = addon_prefs.disable_camera_navigation
        navigation_mode = addon_prefs.navigation_mode

        space_type = context.space_data.type

        # Execute is the first thing called in our operator, so we start by
        # calling the appropriate navigation based on user preference
        if space_type == "VIEW_3D":
            view = context.space_data.region_3d.view_perspective
            if not (view == "CAMERA" and disable_camera):
                try:
                    if navigation_mode == "ORBIT":
                        bpy.ops.view3d.rotate("INVOKE_DEFAULT")
                    else:
                        self.set_walk_confirm_to_trigger(context)
                        bpy.ops.view3d.walk("INVOKE_DEFAULT")
                    # Adding the timer and starting the loop
                    wm = context.window_manager
                    self._timer = wm.event_timer_add(0.1, window=context.window)
                    wm.modal_handler_add(self)
                    return {"RUNNING_MODAL"}
                except RuntimeError as error:
                    self.restore_walk_confirm_keymap()
                    self.report({"ERROR"}, str(error))
                    return {"CANCELLED"}
            else:
                return {"CANCELLED"}

        elif space_type == "NODE_EDITOR" and enable_nodes:
            bpy.ops.view2d.pan("INVOKE_DEFAULT")
            wm = context.window_manager
            # Adding the timer and starting the loop
            self._timer = wm.event_timer_add(0.01, window=context.window)
            wm.modal_handler_add(self)
            return {"RUNNING_MODAL"}

        elif space_type == "IMAGE_EDITOR":
            bpy.ops.wm.call_panel(name="VIEW3D_PT_paint_texture_context_menu")
            return {"FINISHED"}

    def cancel(self, context):
        if self._timer is None:
            return

        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self._timer = None


class RMN_OT_toggle_cam_navigation(Operator):
    """Turn Mouse Navigation of Camera On and Off"""

    bl_idname = "rmn.toggle_cam_navigation"
    bl_label = "Toggle UE Camera Navigation"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        addon_prefs = context.preferences.addons[__package__].preferences
        addon_prefs.disable_camera_navigation = not addon_prefs.disable_camera_navigation
        return {"FINISHED"}
