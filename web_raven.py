#!/usr/bin/env python
from raven import *
import webify
from webify.templates.helpers import html

from webify.middleware import EvalException, SettingsMiddleware

app = webify.defaults.app()

@app.subapp(u'/')
@webify.urlable()
def index(req, p):
    p(u'Hello, world!')

@app.subapp()
@webify.urlable()
def debug(req, p):
    f = OneSimpleFigure([TripleShapeFeatureSet,],
                                [[Triangle, Square, Circle],])
    c = [2,]
    cmatrix = cmatrix_from_one_transition(f, c, [1,])
    cmatrix = cmatrix_from_two_transitions(f, c, [1,], [2,])
    png = rpm_from_cmatrix(f, cmatrix)
    p.headers = [webify.http.headers.content_types.image_png]
    p(png)

@app.subapp()
@webify.urlable()
def example(req, p):
    WIDTH, HEIGHT = 256, 256

    surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context (surface)

    ctx.scale (WIDTH/1.0, HEIGHT/1.0) # Normalizing the canvas

    pat = cairo.LinearGradient (0.0, 0.0, 0.0, 1.0)
    pat.add_color_stop_rgba (1, 0.7, 0, 0, 0.5) # First stop, 50% opacity
    pat.add_color_stop_rgba (0, 0.9, 0.7, 0.2, 1) # Last stop, 100% opacity

    ctx.rectangle (0, 0, 1, 1) # Rectangle(x0, y0, x1, y1)
    ctx.set_source (pat)
    ctx.fill ()

    ctx.translate (0.1, 0.1) # Changing the current transformation matrix

    ctx.move_to (0, 0)
    ctx.arc (0.2, 0.1, 0.1, -math.pi/2, 0) # Arc(cx, cy, radius, start_angle, stop_angle)
    ctx.line_to (0.5, 0.1) # Line to (x,y)
    ctx.curve_to (0.5, 0.2, 0.5, 0.4, 0.2, 0.8) # Curve(x1, y1, x2, y2, x3, y3)
    ctx.close_path ()

    ctx.set_source_rgb (0.3, 0.2, 0.5) # Solid color
    ctx.set_line_width (0.02)
    ctx.stroke ()

    p.headers = [webify.http.headers.content_types.image_png]

    import StringIO
    s = StringIO.StringIO()
    surface.write_to_png(s) # Output to PNG
    png = s.getvalue()
    
    p(png)

from webify.http import server
if __name__ == '__main__':
    mail_server = webify.email.LocalMailServer()
    settings = {
                'mail_server': mail_server
               }

    wrapped_app = webify.wsgify(app, 
                                        SettingsMiddleware(settings),
                                        EvalException,
                                     )

    server.serve(wrapped_app, host='0.0.0.0', port=8087, reload=True)
