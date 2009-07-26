#!/usr/bin/env python
import math
import StringIO
import itertools
import abc
from contextlib import contextmanager

import cairo

figure_size = 99

def create_cairo_surface(width, height, color=cairo.FORMAT_ARGB32):
    s = cairo.ImageSurface(color, width, height)
    cr = cairo.Context(s)
    return s, cr

class Feature(object):
    __metaclass__ = abc.ABCMeta

class DrawableFeature(Feature):
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def draw(self, ctx):
        pass

default_line_width = (3, 3)

class ShapeFeature(DrawableFeature):
    __metaclass__ = abc.ABCMeta
    def __init__(self, center=(.5,.5), 
                       radius=.25, 
                       rotation=0,
                       mirror=False,
                       shear=1.0,
                       color=(0,0,0,1), 
                       line_width=default_line_width):
        self.center = center
        self.radius = radius
        self.rotation = rotation
        self.mirror = mirror
        self.shear = shear
        self.color = color
        self.line_width = line_width

    @contextmanager
    def fat_scale(self, cr):
        cr.save()
        cr.translate((1.0 - self.fatness) / 2, 0)
        cr.scale(self.fatness, 1.0)
        yield
        cr.restore()

    @contextmanager
    def reflected(self, cr):
        if self.mirror:
            cr.save()
            cr.translate(.5, .5)
            cr.transform(cairo.Matrix(-1,0,0,1))
            cr.translate(-.5, -.5)
            yield
            cr.restore()
        else:
            yield

    @contextmanager
    def rotated(self, cr):
        cr.save()
        cr.translate(.5, .5)
        cr.rotate(self.rotation)
        cr.translate(-.5, -.5)
        yield
        cr.restore()


class OblongShapeFeature(ShapeFeature):
    __metaclass__ = abc.ABCMeta
    def __init__(self, center=(.5,.5), 
                       radius=.25, 
                       rotation=0.0,
                       mirror=False,
                       shear=1.0,
                       color=(0,0,0,1), 
                       line_width=default_line_width,
                       fatness=1.0):
        self.fatness = fatness
        ShapeFeature.__init__(self, center, radius, rotation, mirror, shear, color, line_width)

class FillableShapeFeature(ShapeFeature):
    def __init__(self, center=(.5,.5), 
                       radius=.25, 
                       rotation=0.0,
                       mirror=False,
                       shear=1.0,
                       color=(0,0,0,1), 
                       line_width=default_line_width,
                       fill=False,
                       fill_color=(0,0,0,1)):
        self.fill = fill
        self.fill_color = fill_color
        ShapeFeature.__init__(self, center, radius, rotation, mirror, shear, color, line_width)

class OblongFillableShapeFeature(FillableShapeFeature, OblongShapeFeature):
    def __init__(self, center=(.5,.5), 
                       radius=.25, 
                       rotation=0.0,
                       mirror=False,
                       shear=1.0,
                       color=(0,0,0,1), 
                       line_width=default_line_width,
                       fatness=1.0,
                       fill=False,
                       fill_color=(0,0,0,1)):
        OblongShapeFeature.__init__(self, center, radius, rotation, mirror, shear, color, line_width, fatness)
        FillableShapeFeature.__init__(self, center, radius, rotation, mirror, shear, color, line_width, fill, fill_color)
    
class Triangle(OblongFillableShapeFeature):
    def draw(self, cr):
        cr.set_line_width(max(cr.device_to_user_distance(*self.line_width)))
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        if self.fill:
            cr.set_source_rgba(*self.fill_color)
            self.draw_lines(cr)
            cr.fill()
        cr.set_source_rgba(*self.color)
        with self.reflected(cr):
            with self.rotated(cr):
                self.draw_lines(cr)
        cr.stroke()

    def draw_lines(self, cr):
        x,y = self.center
        xradius = self.radius * self.fatness
        yradius = self.radius
        r32 = (math.sqrt(3) / 2 * xradius)
        left, right = x - r32, x + r32
        bottom, top = y + (yradius / 2.0), y - yradius
        cr.move_to (left, bottom)
        cr.line_to ((left + right) / 2.0, top) # Line to (x,y)
        cr.line_to (right, bottom) # Line to (x,y)
        cr.close_path ()

class Square(OblongFillableShapeFeature):
    def draw(self, cr):
        cr.set_line_width(max(cr.device_to_user_distance(*self.line_width)))
        if self.fill:
            cr.set_source_rgba(*self.fill_color)
            self.draw_lines(cr)
            cr.fill()
        cr.set_source_rgba(*self.color)
        with self.reflected(cr):
            with self.rotated(cr):
                self.draw_lines(cr)
        cr.stroke()

    def draw_lines(self, cr):
        x,y = self.center
        xradius = self.radius * self.fatness
        yradius = self.radius
        left, top = x - xradius, y - yradius
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.rectangle(left, top, 2 * xradius, 2 * yradius)

class Circle(OblongFillableShapeFeature):
    def draw(self, cr):
        cr.set_line_width(max(cr.device_to_user_distance(*self.line_width)))
        if self.fill:
            cr.set_source_rgba(*self.fill_color)
            with self.fat_scale(cr):
                self.draw_lines(cr)
            cr.fill()
        cr.set_source_rgba(*self.color)
        with self.fat_scale(cr):
            self.draw_lines(cr)
        cr.stroke()

    def draw_lines(self, cr):
        x,y = self.center
        cr.move_to(x + self.radius, y)
        cr.arc(x, y, self.radius, 0, 2 * math.pi)
        cr.close_path()

class FeatureSet(object):
    __metaclass__ = abc.ABCMeta
    def __init__(self):
        pass

class TransformableFeatureSet(FeatureSet):
    __metaclass__ = abc.ABCMeta

    def transform(self, configuration, amount):
        return configuration + amount

    def can_transform(self, configuration, amount):
        return 0 < amount <= configuration + amount < len(self.features)

class DrawableFeatureSet(TransformableFeatureSet):
    __metaclass__ = abc.ABCMeta
    def __init__(self, features):
        TransformableFeatureSet.__init__(self)
        for f in features:
            assert(issubclass(f, DrawableFeature))

class RingFeatureSet(TransformableFeatureSet):
    __metaclass__ = abc.ABCMeta
    
    def transform(self, configuration, amount):
        t = TransformableFeatureSet.transform(self, configuration, amount)
        if t < len(self.features):
            return t
        else:
            return t - len(self.features)

    def can_transform(self, configuration, amount):
        return 0 < amount and 0 <= configuration

class TripleFeatureSet(RingFeatureSet):
    __metaclass__ = abc.ABCMeta
    def __init__(self, features):
        assert(len(features) == 3)
        RingFeatureSet.__init__(self)

class TripleDrawableFeatureSet(TripleFeatureSet, DrawableFeatureSet):
    __metaclass__ = abc.ABCMeta
    def __init__(self, features):
        TripleFeatureSet.__init__(self, features)
        DrawableFeatureSet.__init__(self, features)

class ShapeFeatureSet(DrawableFeatureSet):
    __metaclass__ = abc.ABCMeta
    def __init__(self, features):
        DrawableFeatureSet.__init__(self, features)
        for f in features:
            assert(issubclass(f, ShapeFeature))

class TripleShapeFeatureSet(TripleFeatureSet, ShapeFeatureSet):
    def __init__(self, features):
        TripleFeatureSet.__init__(self, features)
        ShapeFeatureSet.__init__(self, features)
        self.features = features

class Figure:
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def render():
        pass

class FeatureFigure(Figure):
    __metaclass__ = abc.ABCMeta
    def __init__(self, feature_sets, features):
        assert(len(feature_sets) == len(features))
        self.feature_sets = feature_sets
        #TODO: jperla: make sure features match up with feature sets
        self.features = features
    
    def transform(self, configuration,  amounts):
        assert(len(amounts) == len(configuration))
        for a,fs,f,c in zip(amounts, self.feature_sets, self.features, configuration):
            if a > 0:
                assert(issubclass(fs, TransformableFeatureSet))
                assert(fs(f).can_transform(c, a))
        new_configuration = [fs(f).transform(c, a) 
                                        for fs,f,c,a in zip(self.feature_sets,
                                                            self.features,
                                                            configuration,
                                                            amounts)]
        return new_configuration

    @abc.abstractmethod
    def render(self, configuration):
        num_feature_sets = len(self.feature_sets)
        assert len(self.features) == num_feature_sets == len(configuration)

def surface_to_png(surface):
    buffer = StringIO.StringIO()
    surface.write_to_png(buffer)
    png = buffer.getvalue()
    buffer.close()
    return png

class CairoFigure(Figure):
    def create_context(self, width, height, color=cairo.FORMAT_ARGB32):
        s, cr = create_cairo_surface(width, height, color)
        cr.scale(width/1.0, height/1.0)
        return s, cr

    def surface_to_png(self, surface):
        return surface_to_png(surface)

class OneSimpleFigure(FeatureFigure, CairoFigure):
    def __init__(self, feature_sets, features):
        assert(len(feature_sets) == 1)
        assert(issubclass(feature_sets[0], DrawableFeatureSet))
        FeatureFigure.__init__(self, feature_sets, features)
        
    def render(self, configuration):
        FeatureFigure.render(self, configuration)
        surface, cr = self.create_context(figure_size, figure_size)
        drawable = self.features[0][configuration[0]]()
        drawable.draw(cr)
        return self.surface_to_png(surface)

def rpm_from_pngs(pngs):
    width, height = figure_size * 3, figure_size * 3
    rpm, cr = create_cairo_surface(width, height)
    for x,y,png in zip([0, figure_size, figure_size*2] * 3, [0] * 3 + [figure_size] * 3 + [figure_size*2] * 3, pngs):
        figure = cairo.ImageSurface.create_from_png(StringIO.StringIO(png))
        cr.set_source_surface(figure, x, y)
        cr.paint()
    buffer = StringIO.StringIO()
    rpm.write_to_png(buffer)
    png = buffer.getvalue()
    buffer.close()
    return png

def rpm_from_cmatrix(f, cmatrix):
    pngs = [f.render(c) for c in itertools.chain(*cmatrix)]
    return rpm_from_pngs(pngs)

def cmatrix_from_one_transition(figure, configuration, transition):
    c = [configuration]
    for i in xrange(0,8):
        c.append(figure.transform(c[i], transition))
    cmatrix = [[c[0], c[1], c[2]], [c[3], c[4], c[5]], [c[6], c[7], c[8]]]
    return cmatrix

def cmatrix_from_two_transitions(figure, configuration, transition1, transition2):
    f = figure
    cmatrix = [[None,None,None], [None,None,None], [None,None,None]]
    cmatrix[0][0] = configuration
    c = cmatrix[0][0]
    for i in xrange(1,3):
        c = f.transform(c, transition2)
        cmatrix[i][0] = c
    for i in xrange(3):
        c = cmatrix[i][0]
        for j in xrange(1,3):
            c = f.transform(c, transition1)
            cmatrix[i][j] = c
    for j in xrange(1,3):
        c = cmatrix[0][j]
        for i in xrange(1,3):
            c = f.transform(c, transition2)
            assert(cmatrix[i][j] == c)
    return cmatrix
    
def create_blank_png(width, height):
    s, cr = create_cairo_surface(width, height)
    return surface_to_png(s)

def rpm_images(figure, cmatrix, choices):
    pngs = [figure.render(c) for c in itertools.chain(*cmatrix)]
    blank_png = create_blank_png(figure_size, figure_size)
    answer, pngs[8] = pngs[8], blank_png
    rpm = rpm_from_pngs(pngs)
    choice_images = [figure.render(c) for c in choices]
    return rpm, answer, choice_images

def generate_choices(f, c, t1, t2, answer):
    choices = {str(c):c}
    for i in xrange(10):
        c = f.transform(c, t1)
        choices[str(c)] = c
    for i in xrange(10):
        c = f.transform(c, t2)
        choices[str(c)] = c
    if str(answer) in choices:
        del(choices[str(answer)])
    return choices.values()
        


if __name__ == '__main__':
    f = OneSimpleFigure([TripleShapeFeatureSet,], 
                        [[Triangle, Square, Circle],])
    png = f.render([2,])

