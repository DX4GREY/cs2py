import glfw
from OpenGL.GL import *
from OpenGL.GLUT import (
    glutInit,
    glutBitmapCharacter,
    GLUT_BITMAP_HELVETICA_18
)
import math


class SpectatorRenderer:
    def __init__(self, title="Spectator"):
        self.width = 300
        self.height = 120
        self.title = title

        self.window = None
        self.initialized = False
        self.enabled = True

        self.pos_x = 50
        self.pos_y = 50

        # ================= STYLE =================
        self.padding = 10
        self.line_height = 20
        self.char_width = 9
        self.radius = 10
        self.bg_color = (0.0, 0.0, 0.0, 0.5)

    # =================================================
    def init(self) -> bool:
        if not glfw.init():
            return False

        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
        glfw.window_hint(glfw.FLOATING, glfw.TRUE)
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        glfw.window_hint(glfw.DECORATED, glfw.FALSE)

        self.window = glfw.create_window(
            self.width,
            self.height,
            self.title,
            None,
            None
        )

        if not self.window:
            glfw.terminate()
            return False

        glfw.make_context_current(self.window)
        glutInit()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.setup_2d()
        glfw.set_window_pos(self.window, self.pos_x, self.pos_y)

        self.initialized = True
        return True

    # =================================================
    def setup_2d(self):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    # =================================================
    def draw_text(self, x, y, text):
        glColor4f(1, 1, 1, 1)
        glWindowPos2f(x, y)
        for ch in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # =================================================
    def draw_rounded_rect(self, x, y, w, h, r, segments=16):
        r = min(r, w * 0.5, h * 0.5)

        glBegin(GL_QUADS)
        # center
        glVertex2f(x + r, y)
        glVertex2f(x + w - r, y)
        glVertex2f(x + w - r, y + h)
        glVertex2f(x + r, y + h)

        # left
        glVertex2f(x, y + r)
        glVertex2f(x + r, y + r)
        glVertex2f(x + r, y + h - r)
        glVertex2f(x, y + h - r)

        # right
        glVertex2f(x + w - r, y + r)
        glVertex2f(x + w, y + r)
        glVertex2f(x + w, y + h - r)
        glVertex2f(x + w - r, y + h - r)
        glEnd()

        # bottom-left
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(x + r, y + r)
        for i in range(segments + 1):
            a = math.pi + (i / segments) * (math.pi / 2)
            glVertex2f(
                x + r + math.cos(a) * r,
                y + r + math.sin(a) * r
            )
        glEnd()

        # bottom-right
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(x + w - r, y + r)
        for i in range(segments + 1):
            a = math.pi * 1.5 + (i / segments) * (math.pi / 2)
            glVertex2f(
                x + w - r + math.cos(a) * r,
                y + r + math.sin(a) * r
            )
        glEnd()

        # top-right
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(x + w - r, y + h - r)
        for i in range(segments + 1):
            a = 0 + (i / segments) * (math.pi / 2)
            glVertex2f(
                x + w - r + math.cos(a) * r,
                y + h - r + math.sin(a) * r
            )
        glEnd()

        # top-left
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(x + r, y + h - r)
        for i in range(segments + 1):
            a = math.pi * 0.5 + (i / segments) * (math.pi / 2)
            glVertex2f(
                x + r + math.cos(a) * r,
                y + h - r + math.sin(a) * r
            )
        glEnd()


    # =================================================
    def auto_resize(self, lines):
        max_len = max(len(line) for line in lines)
        self.width = max_len * self.char_width + self.padding * 2
        self.height = len(lines) * self.line_height + self.padding * 2

        glfw.set_window_size(self.window, self.width, self.height)
        self.setup_2d()

    # =================================================
    def render(self, spectators: list[str]):
        if not self.initialized:
            return

        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT)

        if self.enabled:
            lines = ["Spectator List"] + spectators
            self.auto_resize(lines)

            r, g, b, a = self.bg_color
            glColor4f(r, g, b, a)

            self.draw_rounded_rect(
                0,
                0,
                self.width,
                self.height,
                self.radius
            )

            y = self.height - self.padding - self.line_height
            boolean_first_line = True
            for line in lines:
                if boolean_first_line:
                    # Title line
                    self.draw_text(self.padding, y, line)
                else:
                    self.draw_text(self.padding, y, "> " + line)
                y -= self.line_height
                boolean_first_line = False

        glfw.swap_buffers(self.window)

    # =================================================
    def poll(self):
        glfw.poll_events()

    def should_close(self):
        return glfw.window_should_close(self.window)

    def shutdown(self):
        glfw.destroy_window(self.window)
        glfw.terminate()

    # =================================================
    def set_position(
        self,
        *,
        x=None,
        y=None,
        top=False,
        bottom=False,
        left=False,
        right=False,
        center=False,
        margin=20
    ):
        monitor = glfw.get_primary_monitor()
        if not monitor:
            return

        video = glfw.get_video_mode(monitor)

        # === FIX KOMPATIBILITAS GLFW ===
        if hasattr(video, "size"):
            sw, sh = video.size.width, video.size.height
        else:
            sw, sh = video.width, video.height

        if x is not None and y is not None:
            self.pos_x, self.pos_y = x, y
        else:
            if left:
                self.pos_x = margin
            elif right:
                self.pos_x = sw - self.width - margin
            elif center:
                self.pos_x = (sw - self.width) // 2

            if top:
                self.pos_y = margin
            elif bottom:
                self.pos_y = sh - self.height - margin
            elif center:
                self.pos_y = (sh - self.height) // 2

        self.pos_x = max(0, min(self.pos_x, sw - self.width))
        self.pos_y = max(0, min(self.pos_y, sh - self.height))

        if self.window:
            glfw.set_window_pos(self.window, self.pos_x, self.pos_y)
