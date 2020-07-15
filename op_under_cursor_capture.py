# if "bpy" in locals():
#     import imp
#     imp.reload(window_capture)
# else:
#     from . import window_capture

import bpy 
from . import window_capture

WindowCapture = window_capture.WindowCapture
INTERVAL = 0.2


class UnderCursorCaptureOperator(bpy.types.Operator):
    bl_idname = "object.undercursorcapture"
    bl_label = "WindowCapture"

    __timer = None
    __cap = None

    @classmethod
    def is_running(cls):
        return cls.__timer is not None

    def __handle_add(self, context):
        if not self.is_running():
            UnderCursorCaptureOperator.__timer = context.window_manager.event_timer_add(
                INTERVAL, window=context.window
            )
            UnderCursorCaptureOperator.__cap = WindowCapture(image_name="under_cursor_capture", is_cursor_capture=True)
            context.window_manager.modal_handler_add(self)

    def __handle_remove(self, context):
        if self.is_running():
            context.window_manager.event_timer_remove(UnderCursorCaptureOperator.__timer)
            UnderCursorCaptureOperator.__timer = None
            UnderCursorCaptureOperator.__cap = None

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        if not self.is_running():
            # 終了処理
            pass
            return {"FINISHED"}

        # タイマーイベントが来たときに処理？
        if event.type == "TIMER":
            # メイン処理
            UnderCursorCaptureOperator.__cap.capture_under_cursor(event.mouse_x, event.mouse_y)
        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        if not UnderCursorCaptureOperator.is_running():
            # 初期化処理
            self.__handle_add(context)
            return {"RUNNING_MODAL"}
        else:
            self.__handle_remove(context)
        return {"FINISHED"}

class UIPanel_cursor(bpy.types.Panel):
    bl_label = "UnderCursorCapture"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        if not UnderCursorCaptureOperator.is_running():
            layout.operator(UnderCursorCaptureOperator.bl_idname, text="start", icon="PLAY")
        else:
            layout.operator(UnderCursorCaptureOperator.bl_idname, text="end", icon="PAUSE")
