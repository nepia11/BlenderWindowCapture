from time import time
import bpy
import bgl
import gpu
from gpu_extras.presets import draw_texture_2d

start_time = time()

IMAGE_WIDTH = 256
IMAGE_HEIGHT = 256

def time_diff(text: str = ""):
    global start_time
    now = time()
    diff = now - start_time
    print(text + ":time diff:" + str(diff))
    start_time = now


def get_image(image_name, width, height):
    if not image_name in bpy.data.images:
        return bpy.data.images.new(image_name, width, height, alpha=True)
    return bpy.data.images[image_name]

def get_uv_index(u, v, width, height):
    x = int(u * width)
    y = int(v * height)
    return y * width + x


# フルバッファーを読みたくない、間欠的に読み出す
def create_remapping_indexes(source_width, source_height, dest_width, dest_height):
    indexes = [0] * dest_width * dest_height * 4

    for y in range(dest_height):
        for x in range(dest_width):
            u = x / dest_width
            v = y / dest_width

            source_index = get_uv_index(u, v, source_width, source_height) * 4
            dest_index = get_uv_index(u, v, dest_width, dest_height) * 4

            indexes[dest_index] = source_index
            indexes[dest_index + 1] = source_index + 1
            indexes[dest_index + 2] = source_index + 2
            indexes[dest_index + 3] = source_index + 3

    print("indexes:" + str(indexes))
    return indexes


def remap(buffer, indexes):
    result = [0] * len(indexes)

    for index, buffer_index in enumerate(indexes):
        result[index] = buffer[buffer_index]

    return result


def draw_cursor(image, x, y):
    # とりあえず白い点をおく
    width = image.size[0]
    height = image.size[1]
    index = (int(y) * width + int(x)) * 4
    image.pixels[index] = 1.0
    image.pixels[index + 1] = 1.0
    image.pixels[index + 2] = 1.0
    image.pixels[index + 3] = 1.0


class WindowCapture:
    def __init__(self, image_name="WindowCapture", is_cursor_capture=False):
        self.image_name = image_name
        self.width = 0
        self.height = 0
        if is_cursor_capture:
            self.__create_buffer(1,1,self.image_name,1,1)
        else:
            self.__update_size()

    def __create_buffer(
        self, 
        src_width, 
        src_height, 
        image_name, 
        image_width, 
        image_height
        ):
        self.buffer = bgl.Buffer(bgl.GL_BYTE, src_width * src_height * 4)
        
        # self.image = get_image(self.image_name, self.width, self.height)
        self.image = get_image(image_name, image_width, image_height)
        self.image.scale(image_width, image_height)

    def __update_size(self):
        if (
            self.width != bpy.context.window.width
            and self.height != bpy.context.window.height
        ):
            self.width = bpy.context.window.width
            self.height = bpy.context.window.height

            self.remapping_indexes = create_remapping_indexes(
                self.width, self.height, IMAGE_WIDTH, IMAGE_HEIGHT
            )

            self.__create_buffer(
                self.width,
                self.height,
                self.image_name,
                IMAGE_WIDTH,
                IMAGE_HEIGHT
                )

    def __update_image(self, mouse_x, mouse_y):
        # self.image.pixels = [v / 255 for v in self.buffer]

        remapped_buffer = remap(self.buffer, self.remapping_indexes)
        time_diff("remap")
        self.image.pixels = [v / 255 for v in remapped_buffer]
        # self.image.pixels = [v for v in self.buffer]

        if mouse_x is not None and mouse_y is not None:
            draw_cursor(self.image, mouse_x / self.width * IMAGE_WIDTH, mouse_y / self.height * IMAGE_HEIGHT)

        time_diff("image.pixels")


    def capture(self, mouse_x=None, mouse_y=None):
        time_diff()
        self.__update_size()
        time_diff("__update_size")
        bgl.glReadBuffer(bgl.GL_FRONT)
        time_diff("glReadBuffer")
        # GL_FLOATでバッファ作って読むと馬鹿みたいに重いのでGL_BYTE,GL_UNSIGNED_BYTEになってる
        bgl.glReadPixels(
            0,
            0,
            self.width,
            self.height,
            bgl.GL_RGBA,
            bgl.GL_UNSIGNED_BYTE,
            # bgl.GL_FLOAT,
            self.buffer,
        )
        time_diff("glReadPixels")
        self.__update_image(mouse_x, mouse_y)

    def capture_under_cursor(self, mouse_x=None, mouse_y=None):
        bgl.glReadBuffer(bgl.GL_FRONT)
        time_diff("glReadBuffer")
        # GL_FLOATでバッファ作って読むと馬鹿みたいに重いのでGL_BYTE,GL_UNSIGNED_BYTEになってる
        bgl.glReadPixels(
            mouse_x,
            mouse_y,
            1,
            1,
            bgl.GL_RGBA,
            bgl.GL_UNSIGNED_BYTE,
            # bgl.GL_FLOAT,
            self.buffer,
        )
        time_diff("glReadPixels")
        # self.__update_image(mouse_x, mouse_y)
        self.image.pixels = [v / 255 for v in self.buffer]
        time_diff("image.pixels")


