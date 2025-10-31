#!/usr/bin/python
# gtkGfx -    Implementation of the Gfx.Driver Interface with GTK 4

"""Implements Gfx.Driver for GTK 4 using Cairo and Pango.
"""

import math
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")

from gi.repository import Gtk, Gdk, Pango, PangoCairo
import cairo

try:
    import Gfx
except ImportError:
    from . import Gfx

try:
    from Compatibility import *  # noqa: F401,F403
except ImportError:
    try:
        from . import Compatibility  # type: ignore
        globals().update(Compatibility.__dict__)
    except Exception:
        pass


driverName = "gtk4Gfx"

# Utility: create 8x8 stipple patterns as cairo surfaces

def _make_stipple(pattern_bytes):
    """Create a cairo SurfacePattern from 8x8 1-bit mask encoded as bytes string of length 8*1.
    pattern_bytes: 8 bytes, each bit used across the row (msb first).
    """
    width = 8
    height = 8
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)
    # Draw white pixels where bits are 1, black transparent elsewhere
    ctx.set_source_rgba(1, 1, 1, 1)
    for y in range(height):
        b = pattern_bytes[y]
        for x in range(width):
            bit = (b >> (7 - x)) & 1
            if bit:
                ctx.rectangle(x, y, 1, 1)
    ctx.fill()
    pat = cairo.SurfacePattern(surface)
    pat.set_extend(cairo.EXTEND_REPEAT)
    return pat

# Define stipple patterns similar to the original
_stipple_solid = None  # solid handled by solid fills
_stipple_pattern_a = _make_stipple(bytes([0xCC, 0x99, 0x33, 0x66, 0xCC, 0x99, 0x33, 0x66]))
_stipple_pattern_b = _make_stipple(bytes([0xCC, 0x66, 0x33, 0x99, 0xCC, 0x66, 0x33, 0x99]))
_stipple_pattern_c = _make_stipple(bytes([0xC3, 0x66, 0x3C, 0x99, 0xC3, 0x66, 0x3C, 0x99]))


class Driver(Gfx.Driver):
    """Graphics layer on top of Cairo for GTK 4.
    See Gfx.py for expected API.
    """

    def __init__(self, drawing_area: Gtk.DrawingArea):
        super().__init__()
        self.drawing_area = drawing_area
        self.color = (0, 0, 0)
        self.linePattern = getattr(Gfx, "CONTINUOUS", "continuous")
        self.fillPattern = getattr(Gfx, "SOLID", "solid")
        self.gc_thickness = 1
        self.gc_line_style = "solid"
        self.gc_cap_style = cairo.LINE_CAP_ROUND
        self.gc_join_style = cairo.LINE_JOIN_MITER
        self.fontType = getattr(Gfx, "SANS", "sans")
        self.fontSize = getattr(Gfx, "NORMAL", "normal")
        self.fontWeight = ""
        self._width = 0
        self._height = 0
        # Pango layout will be created on demand per draw
        self._needs_clear = True

    # GTK 4 draw function will provide Cairo context and current allocation size
    def _update_size(self, width, height):
        self._width = width
        self._height = height

    def resizedGfx(self):
        # no-op; size is managed by allocation
        pass

    def getSize(self):
        return self._width, self._height

    def getResolution(self):
        return 100

    # Color helpers
    def setColor(self, rgbTuple):
        self.color = rgbTuple

    def setLineWidth(self, width):
        self.lineWidth = width
        if width == getattr(Gfx, "THIN", "thin"):
            self.gc_thickness = 1
        elif width == getattr(Gfx, "MEDIUM", "medium"):
            self.gc_thickness = 2
        elif width == getattr(Gfx, "THICK", "thick"):
            self.gc_thickness = 3
        else:
            raise ValueError("'thickness' must be 'thin', 'medium' or 'thick' !")

    def setLinePattern(self, pattern):
        self.linePattern = pattern
        if pattern == getattr(Gfx, "CONTINUOUS", "continuous"):
            self.gc_line_style = "solid"
        elif pattern == getattr(Gfx, "DASHED", "dashed"):
            self.gc_line_style = "dashed"
        elif pattern == getattr(Gfx, "DOTTED", "dotted"):
            self.gc_line_style = "dotted"
        else:
            raise ValueError("'pattern' must be 'continuous', 'dashed' or 'dotted' !")

    def setFillPattern(self, pattern):
        self.fillPattern = pattern

    def setFont(self, ftype, size, weight):
        self.fontType = ftype
        self.fontSize = size
        self.fontWeight = weight

    # internal: apply stroke style to context
    def _apply_stroke_style(self, cr: cairo.Context):
        cr.set_line_width(self.gc_thickness)
        cr.set_line_cap(self.gc_cap_style)
        cr.set_line_join(self.gc_join_style)
        if self.gc_line_style == "solid":
            cr.set_dash([])
        elif self.gc_line_style == "dashed":
            cr.set_dash([5.0, 5.0], 0)
        elif self.gc_line_style == "dotted":
            cr.set_dash([1.0, 4.0], 0)

    # internal: apply fill style to context
    def _apply_fill_style(self, cr: cairo.Context):
        r, g, b = self.color
        if self.fillPattern == getattr(Gfx, "SOLID", "solid"):
            cr.set_source_rgb(r, g, b)
        elif self.fillPattern == getattr(Gfx, "PATTERN_A", "patternA"):
            cr.set_source(_stipple_pattern_a)
            cr.set_operator(cairo.OPERATOR_OVER)
        elif self.fillPattern == getattr(Gfx, "PATTERN_B", "patternB"):
            cr.set_source(_stipple_pattern_b)
            cr.set_operator(cairo.OPERATOR_OVER)
        elif self.fillPattern == getattr(Gfx, "PATTERN_C", "patternC"):
            cr.set_source(_stipple_pattern_c)
            cr.set_operator(cairo.OPERATOR_OVER)
        else:
            cr.set_source_rgb(r, g, b)

    def _apply_source_color(self, cr: cairo.Context):
        r, g, b = self.color
        cr.set_source_rgb(r, g, b)

    # Coordinate transform: given y from bottom-left to cairo top-left
    def _ty(self, y):
        return self._height - y - 1

    # Drawing API (recorded immediate drawing into a back buffer) — in GTK 4 we trigger redraws and draw on demand.
    # To keep API, we'll store a list of drawing commands and replay them in draw func.

    def reset(self):
        # Start fresh command list
        self._commands = []

    def clear(self):
        self.reset()
        # Clear background to white by default
        self._commands.append(("clear", (1, 1, 1)))
        self.queue_draw()

    def queue_draw(self):
        if self.drawing_area:
            self.drawing_area.queue_draw()

    # Drawing recorders
    def drawPoint(self, x, y):
        self._commands.append(("point", (x, y, self.color, self.gc_thickness)))
        self.queue_draw()

    def drawLine(self, x1, y1, x2, y2):
        self._commands.append(("line", (x1, y1, x2, y2, self.color, self.gc_thickness, self.gc_line_style)))
        self.queue_draw()

    def drawRect(self, x, y, w, h):
        self._commands.append(("rect", (x, y, w, h, self.color, self.gc_thickness, self.gc_line_style)))
        self.queue_draw()

    def drawPoly(self, array):
        self._commands.append(("poly", (list(array), self.color, self.gc_thickness, self.gc_line_style)))
        self.queue_draw()

    def fillRect(self, x, y, w, h):
        self._commands.append(("fill_rect", (x, y, w, h, self.color, self.fillPattern)))
        self.queue_draw()

    def fillPoly(self, array):
        self._commands.append(("fill_poly", (list(array), self.color, self.fillPattern)))
        self.queue_draw()

    def writeStr(self, x, y, s, rotationAngle=0.0):
        self._commands.append(("text", (x, y, s, rotationAngle, self.color, self.fontType, self.fontSize, self.fontWeight)))
        self.queue_draw()

    # Replay drawing
    def _replay(self, cr: cairo.Context):
        # background clear first if present
        for cmd, args in self._commands:
            if cmd == "clear":
                r, g, b = args
                cr.save()
                cr.set_source_rgb(r, g, b)
                cr.paint()
                cr.restore()
        for cmd, args in self._commands:
            if cmd == "clear":
                continue
            if cmd == "point":
                x, y, color, thickness = args
                cr.save()
                r, g, b = color
                cr.set_source_rgb(r, g, b)
                cr.set_line_width(max(1, thickness))
                cr.move_to(x, self._ty(y))
                cr.line_to(x + 0.1, self._ty(y))
                cr.stroke()
                cr.restore()
            elif cmd == "line":
                x1, y1, x2, y2, color, thickness, style = args
                cr.save()
                r, g, b = color
                cr.set_source_rgb(r, g, b)
                cr.set_line_width(thickness)
                if style == "dashed":
                    cr.set_dash([5.0, 5.0])
                elif style == "dotted":
                    cr.set_dash([1.0, 4.0])
                else:
                    cr.set_dash([])
                cr.move_to(x1, self._ty(y1))
                cr.line_to(x2, self._ty(y2))
                cr.stroke()
                cr.restore()
            elif cmd == "rect":
                x, y, w, h, color, thickness, style = args
                cr.save()
                r, g, b = color
                cr.set_source_rgb(r, g, b)
                cr.set_line_width(thickness)
                if style == "dashed":
                    cr.set_dash([5.0, 5.0])
                elif style == "dotted":
                    cr.set_dash([1.0, 4.0])
                else:
                    cr.set_dash([])
                cr.rectangle(x + 0.5, self._ty(y) - h + 0.5, w - 1, h - 1)
                cr.stroke()
                cr.restore()
            elif cmd == "poly":
                pts, color, thickness, style = args
                if not pts:
                    continue
                cr.save()
                r, g, b = color
                cr.set_source_rgb(r, g, b)
                cr.set_line_width(thickness)
                if style == "dashed":
                    cr.set_dash([5.0, 5.0])
                elif style == "dotted":
                    cr.set_dash([1.0, 4.0])
                else:
                    cr.set_dash([])
                x0, y0 = pts[0]
                cr.move_to(x0, self._ty(y0))
                for (x, y) in pts[1:]:
                    cr.line_to(x, self._ty(y))
                cr.stroke()
                cr.restore()
            elif cmd == "fill_rect":
                x, y, w, h, color, fillPat = args
                cr.save()
                r, g, b = color
                if fillPat == getattr(Gfx, "SOLID", "solid"):
                    cr.set_source_rgb(r, g, b)
                elif fillPat == getattr(Gfx, "PATTERN_A", "patternA"):
                    cr.set_source(_stipple_pattern_a)
                elif fillPat == getattr(Gfx, "PATTERN_B", "patternB"):
                    cr.set_source(_stipple_pattern_b)
                elif fillPat == getattr(Gfx, "PATTERN_C", "patternC"):
                    cr.set_source(_stipple_pattern_c)
                else:
                    cr.set_source_rgb(r, g, b)
                cr.rectangle(x, self._ty(y) - h + 1, w, h)
                cr.fill()
                cr.restore()
            elif cmd == "fill_poly":
                pts, color, fillPat = args
                if not pts:
                    continue
                cr.save()
                r, g, b = color
                if fillPat == getattr(Gfx, "SOLID", "solid"):
                    cr.set_source_rgb(r, g, b)
                elif fillPat == getattr(Gfx, "PATTERN_A", "patternA"):
                    cr.set_source(_stipple_pattern_a)
                elif fillPat == getattr(Gfx, "PATTERN_B", "patternB"):
                    cr.set_source(_stipple_pattern_b)
                elif fillPat == getattr(Gfx, "PATTERN_C", "patternC"):
                    cr.set_source(_stipple_pattern_c)
                else:
                    cr.set_source_rgb(r, g, b)
                x0, y0 = pts[0]
                cr.move_to(x0, self._ty(y0))
                for (x, y) in pts[1:]:
                    cr.line_to(x, self._ty(y))
                cr.close_path()
                cr.fill()
                cr.restore()
            elif cmd == "text":
                x, y, s, angle, color, ftype, fsize, fweight = args
                cr.save()
                r, g, b = color
                cr.set_source_rgb(r, g, b)
                layout = PangoCairo.create_layout(cr)
                # font mapping
                if ftype == getattr(Gfx, "SANS", "sans"):
                    ff = "sans"
                elif ftype == getattr(Gfx, "SERIF", "serif"):
                    ff = "serif"
                elif ftype == getattr(Gfx, "FIXED", "fixed"):
                    ff = "monospace"
                else:
                    ff = "sans"
                if fsize == getattr(Gfx, "SMALL", "small"):
                    fs = 5
                elif fsize == getattr(Gfx, "NORMAL", "normal"):
                    fs = 10
                elif fsize == getattr(Gfx, "LARGE", "large"):
                    fs = 20
                else:
                    fs = 10
                style = Pango.Style.ITALIC if (isinstance(fweight, str) and "i" in fweight) else Pango.Style.NORMAL
                weight = Pango.Weight.BOLD if (isinstance(fweight, str) and "b" in fweight) else Pango.Weight.NORMAL
                desc = Pango.FontDescription()
                desc.set_family(ff)
                desc.set_size(int(fs * Pango.SCALE))
                desc.set_style(style)
                desc.set_weight(weight)
                layout.set_font_description(desc)
                layout.set_text(s, -1)
                # get text size in pixels
                pw, ph = layout.get_pixel_size()
                # Position baseline at (x, y) with our coordinate transform
                ty = self._ty(y) - ph
                if angle and abs(angle) > 1e-6:
                    cr.translate(x, ty + ph)
                    cr.rotate(-angle * math.pi / 180.0)
                    PangoCairo.show_layout(cr, layout)
                else:
                    cr.move_to(x, ty)
                    PangoCairo.show_layout(cr, layout)
                cr.restore()


class Window(Driver, Gfx.Window):
    def __init__(self, size=(640, 480), title="gtkGraph"):
        self.win = Gtk.Window()
        self.win.set_title(title)
        self.win.set_default_size(size[0], size[1])
        self.win.set_resizable(False)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_content_width(size[0])
        self.canvas.set_content_height(size[1])

        # draw func
        def on_draw(area, cr, width, height, data=None):
            self._update_size(width, height)
            self._replay(cr)
        self.canvas.set_draw_func(on_draw, None)

        # track allocation size
        def on_resize(widget, allocation, data=None):
            self._update_size(allocation.width, allocation.height)
        self.canvas.connect("size-allocate", on_resize)

        self.win.set_child(self.canvas)
        self.win.connect("close-request", self._on_close_request)
        self.win.present()

        Driver.__init__(self, self.canvas)
        self.clear()

    def refresh(self):
        # In GTK 4, draw is on-demand; queue a redraw
        self.queue_draw()

    def quit(self):
        if self.win:
            self.win.destroy()
        app = Gtk.Application.get_default()
        if app:
            app.quit()

    def waitUntilClosed(self):
        # For backward compatibility: run a minimal Gtk application loop
        app = Gtk.Application(application_id="com.example.gtkGfx")

        def on_activate(application):
            # Reparent window into this application if needed
            self.win.set_application(application)
            self.win.present()

        app.connect("activate", on_activate)
        app.run(sys.argv)

    def _on_close_request(self, *args):
        app = Gtk.Application.get_default()
        if app:
            app.quit()
        return False


if __name__ == "__main__":
    import systemTest
    systemTest.Test_gtkGfx()
