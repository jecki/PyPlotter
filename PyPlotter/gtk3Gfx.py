#!/usr/bin/python
# gtkGfx -    Implementation of the Gfx.Driver Interface with gtk



"""Implementes Gfx.Driver gtk3. WORK IN PROGRESS!!!
"""

import math

import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

try:
    import Gfx
except ImportError:
    from . import Gfx
try:
    from Compatibility import *
except ImportError:
    from . import Compatiblity
    globals().update(Compatibility.__dict__)


driverName = "gtk3Gfx"


class Dummy:
    pass

def dummy(*args, **kwargs):
    return None

gdk = Dummy()
gdk.bitmap_create_from_data = dummy
gdk.color_parse = dummy
# pango = Dummy()
# pango.Context = Dummy


########################################################################
#
#   class Driver
#
########################################################################

stipple_Solid    = gdk.bitmap_create_from_data(None,
                   "\xff\xff\xff\xff\xff\xff\xff\xff", 8, 8)
stipple_PatternA = gdk.bitmap_create_from_data(None,
                   "\xcc\x99\x33\x66\xcc\x99\x33\x66", 8, 8)
stipple_PatternB = gdk.bitmap_create_from_data(None,
                   "\xcc\x66\x33\x99\xcc\x66\x33\x99", 8, 8)
stipple_PatternC = gdk.bitmap_create_from_data(None,
                   "\xc3\x66\x3c\x99\xc3\x66\x3c\x99", 8, 8)

white = gdk.color_parse("white")
black = gdk.color_parse("black")


class PangoContextWrapper:
    def __init__(self):
        pass


class Driver(Gfx.Driver):
    """A simple graphics layer on top of gdk.
    See Gfx.py
    """

    def __init__(self, surface, w, h):
        """Initializes canvas on a cairo-surface."""
        Gfx.Driver.__init__(self)
        self.pango_layout = Dummy()
        self.pango_context = Dummy()
        self.pango_font = Dummy()
        self.changeSurface(surface, w, h)

    def changeSurface(self, surface, w, h):
        """sChange the cairo-surface."""
        self.surface = surface
        self.w = w
        self.h = h
        if self.surface:
            self.ctx = cairo.Context(surface)
            self.resizedGfx()
        else:
            self.ctx = None

    def resizedGfx(self):
        if isinstance(self.surface, cairo.ImageSurface):
            self.w = self.surface.get_width()
            self.h = self.surface.get_height()

    def getSize(self):
        return self.w, self.h

    def getResolution(self):
        return 100

    def setColor(self, rgbTuple):
        self.ctx.set_source_rgb(*rgbTuple)
        self.color = rgbTuple

    def setLineWidth(self, width):
        self.lineWidth = width
        if width == Gfx.THIN: self.gc_thickness = 1
        elif width == Gfx.MEDIUM: self.gc_thickness = 2
        elif width == Gfx.THICK: self.gc_thickness = 3
        else: raise ValueError("'thickness' must be 'thin', 'medium' or 'thick' !")
        self.gc.set_line_attributes(self.gc_thickness,
                                    self.gc_line_style,
                                    self.gc_cap_style,
                                    self.gc_join_style)

    def setLinePattern(self, pattern):
        self.linePattern = pattern
        if pattern == Gfx.CONTINUOUS:
            self.gc_line_style = gdk.LINE_SOLID
        elif pattern == Gfx.DASHED:
            self.gc_line_style = gdk.LINE_ON_OFF_DASH
            self.gc.set_dashes(0, (5, 5))
        elif pattern == Gfx.DOTTED:
            self.gc_line_style = gdk.LINE_ON_OFF_DASH
            self.gc.set_dashes(0, (1, 4))
        else: raise ValueError("'pattern' must be 'continuous', " + \
              "'dashed' or 'dotted' !")
        self.gc.set_line_attributes(self.gc_thickness,
                                    self.gc_line_style,
                                    self.gc_cap_style,
                                    self.gc_join_style)

    def setFillPattern(self, pattern):
        self.fillPattern = pattern
        if pattern == Gfx.SOLID:
            fp = gdk.SOLID
            pat = stipple_Solid
        elif pattern == Gfx.PATTERN_A:
            fp = gdk.STIPPLED
            pat = stipple_PatternA
        elif pattern == Gfx.PATTERN_B:
            fp = gdk.STIPPLED
            pat = stipple_PatternB
        elif pattern == Gfx.PATTERN_C:
            fp = gdk.STIPPLED
            pat = stipple_PatternC
        else: raise ValueError("'pattern' must be 'solid' or 'patternA', " + \
                    "'patternB', 'patternC' !")
        self.gc.set_fill(fp)
        self.gc.set_stipple(pat)

    def setFont(self, ftype, size, weight):
        self.fontType = ftype
        self.fontSize = size
        self.fontWeight = weight
        if ftype == Gfx.SANS:  ff = "sans"
        elif ftype == Gfx.SERIF:  ff = "serif"
        elif ftype == Gfx.FIXED:  ff = "monospace"
        else: raise ValueError("'type' must be 'sans', 'serif' or 'fixed' !")
        if size == Gfx.SMALL: fs = 5
        elif size == Gfx.NORMAL: fs = 10
        elif size == Gfx.LARGE: fs = 20
        else: raise ValueError("'size' must be 'small', 'normal' or 'large' !")
        fst = pango.STYLE_NORMAL
        fw = pango.WEIGHT_NORMAL
        if "i" in weight: fst = pango.STYLE_ITALIC
        elif "b" in weight: fw = pango.WEIGHT_BOLD
        self.pango_font.set_family(ff)
        self.pango_font.set_size(fs*pango.SCALE)
        self.pango_font.set_style(fst)
        self.pango_font.set_weight(fw)
        self.pango_layout.set_font_description(self.pango_font)

    def getTextSize(self, text):
        self.pango_layout.set_text(text)
        return self.pango_layout.get_pixel_size()

##     def selectFontSize(self, text, w,h):
##         for fs in range(3,0,-1):
##             self.setFont(self, self.fontType, fs, self.fontWeight)
##             sw,sh = self.getTextSize(text)
##             if sw <= w and sh <= h: break
##         else:
##             return 0
##         return 1

    def drawPoint(self, x, y):
        self.drawable.draw_point(self.gc, x, self.h-y-1)

    def __checkInLine(self):
        if self.linePattern != Gfx.CONTINUOUS and \
           self.fillPattern != Gfx.SOLID:
            self.gc.set_fill(gdk.SOLID)

    def __checkOutLine(self):
        if self.linePattern != Gfx.CONTINUOUS and \
           self.fillPattern != Gfx.SOLID:
            self.gc.set_fill(gdk.STIPPLED)

    def drawLine(self, x1, y1, x2, y2):
        self.__checkInLine()
        self.drawable.draw_line(self.gc, x1, self.h-y1-1, x2, self.h-y2-1)
        self.__checkOutLine()

    def drawRect(self, x, y, w, h):
        self.__checkInLine()
        self.drawable.draw_rectangle(self.gc,False,x,self.h-y-h,w-1,h-1)
        self.__checkOutLine()

    def drawPoly(self, array):
        if array:
            transformed = [(x, self.h-y-1) for x,y in array]
            self.__checkInLine()
            self.drawable.draw_lines(self.gc, transformed)
            self.__checkOutLine()

    def fillRect(self, x, y, w, h):
        self.drawable.draw_rectangle(self.gc,True,x,self.h-y-h,w,h)

    def fillPoly(self, array):
        transformed = [(x, self.h-y-1) for x,y in array]
        self.drawable.draw_polygon(self.gc, True, transformed)


    def writeStr(self, x, y, str, rotationAngle=0.0):
        self.pango_layout.set_text(str)
        w, h = self.pango_layout.get_pixel_size()
        if rotationAngle == 0.0:
            self.drawable.draw_layout(self.gc, x, self.h-y-h,
                                      self.pango_layout)
        else:
            a = rotationAngle / 180.0 * math.pi
            da = math.atan2(h,0)-a
            dw = int(h*math.cos(da)+0.5)
            dh = int(h*math.sin(da)+0.5)-h

            pixmap = gdk.Pixmap(self.drawable, w, h)
            gc = gdk.GC(pixmap)
            gc.set_rgb_fg_color(black)
            gc.set_fill(gdk.SOLID)
            pixmap.draw_rectangle(gc, True, 0, 0, w, h)
            gc.set_rgb_fg_color(white)
            pixmap.draw_layout(gc, 0, 0, self.pango_layout)
            image = pixmap.get_image(0, 0, w, h)
            for dy in range(h):
                for dx in range(w):
                    if (image.get_pixel(dx, dy) & 0x808080) != 0:
                        r = math.sqrt(dx**2+dy**2)
                        da = math.atan2(dy,dx) - a
                        xx = int(r * math.cos(da)+0.5)
                        yy = int(r * math.sin(da)+0.5)
                        self.drawable.draw_point(self.gc, x+xx-dw,
                                                 self.h-y-h+yy-dh)


########################################################################
#
#   class Window
#
########################################################################


class Window(Driver, Gfx.Window):

    def __init__(self, size=(640, 480), title="Gtk3Graph"):
        w, h = size
        self.win = Gtk.Window(title=title)
        self.win.set_default_size(*size)
        self.win.set_size_request(*size)
        self.win.set_resizable(False)
        self.win.set_title(title)
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        self.canvas = Gtk.DrawingArea()
        self.win.add(self.canvas)
        self.canvas.connect("configure-event", self.onConfigure)
        self.canvas.connect("draw", self.draw)
        self.win.connect("destroy", self.quit)
        Driver.__init__(self, self.surface, w, h)
        self.win.show_all()
        self.refresh()

    def refresh(self):
        """Refresh the display."""
        pass  # Not yet implemented :-()

    def quit(self, window):
        # window.destroy()
        if self.surface:
            self.surface.finish()
        Gtk.main_quit()

    def waitUntilClosed(self):
        Gtk.main()

    def onConfigure(self, da, event):
        w = da.get_allocated_width()
        h = da.get_allocated_height()
        if self.surface:
            oldW, oldH = self.getSize()
            if oldW == w and oldH == w:
                return
            self.surface.finish()
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        self.changeSurface(self.surface, w, h)
        # self.clear()
        return True

    def draw(self, da, cr):
        cr.save()
        cr.set_source_surface(self.surface, 0, 0)
        w, h = self.getSize()
        cr.rectangle(0, 0, w, h)
        cr.fill()
        cr.restore()


########################################################################
#
#   Test
#
########################################################################

if __name__ == "__main__":
    # import systemTest
    # systemTest.Test_gtkGfx()
    w = Window()
    w.waitUntilClosed()
