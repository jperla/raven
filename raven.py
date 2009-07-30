#!/usr/bin/env python
import math
import StringIO
import itertools
import abc
from contextlib import contextmanager

import numpy
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

def identity_matrix():
    return numpy.array([[1,0,0],[0,1,0],[0,0,1]])

class ShapeFeature(DrawableFeature):
    __metaclass__ = abc.ABCMeta
    def __init__(self, transformation=identity_matrix(),
                       color=(0,0,0,1), 
                       line_width=default_line_width):
        self.transformation = transformation
        self.color = color
        self.line_width = line_width

    @contextmanager
    def transformed(self, cr):
        cr.save()
        t = self.transformation
        cr.transform(cairo.Matrix(t[0,0], t[1,0], t[0,1], t[1,1], t[0,2], t[1,2]))
        yield
        cr.restore()

class FillableShapeFeature(ShapeFeature):
    def __init__(self, transformation=identity_matrix(),
                       color=(0,0,0,1), 
                       line_width=default_line_width,
                       fill_color=None):
        self.fill_color = fill_color
        ShapeFeature.__init__(self, transformation, color, line_width)

class SimpleShapeFeature(ShapeFeature):
    __metaclass__ = abc.ABCMeta
    def draw(self, cr):
        cr.set_line_width(max(cr.device_to_user_distance(*self.line_width)))
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_source_rgba(*self.color)
        with self.transformed(cr):
            self.draw_lines(cr)
        cr.stroke()

    @abc.abstractmethod
    def draw_lines():
        pass

class SimpleFillableShapeFeature(FillableShapeFeature, SimpleShapeFeature):
    def draw(self, cr):
        cr.set_line_width(max(cr.device_to_user_distance(*self.line_width)))
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        if self.fill_color is not None:
            cr.set_source_rgba(*self.fill_color)
            with self.transformed(cr):
                self.draw_lines(cr)
            cr.fill()
        SimpleShapeFeature.draw(self, cr)

class Triangle(SimpleFillableShapeFeature):
    def draw_lines(self, cr):
        x,y = .5, .5
        radius = .25
        r32 = (math.sqrt(3) / 2 * radius)
        left, right = x - r32, x + r32
        bottom, top = y + (radius / 2.0), y - radius
        cr.move_to(left, bottom)
        cr.line_to((left + right) / 2.0, top)
        cr.line_to(right, bottom)
        cr.close_path ()

class Square(SimpleFillableShapeFeature):
    def draw_lines(self, cr):
        left, top = .25, .25
        side_length = .5
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.rectangle(left, top, side_length, side_length)

class Circle(SimpleFillableShapeFeature):
    def draw_lines(self, cr):
        cr.move_to(0.75, 0.5)
        cr.arc(.5, .5, .25, 0, 2 * math.pi)
        cr.close_path()

class FeatureSet(object):
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def __init__(self):
        pass

    @classmethod
    @abc.abstractmethod
    def suggested_features(cls, all_features):
        pass

class ValueFeature(Feature):
    __metaclass__ = abc.ABCMeta
    value = None

class ColorFeature(ValueFeature):
    __metaclass__ = abc.ABCMeta

class Blue(ColorFeature):
    value = (0,0,1,1)
class Red(ColorFeature):
    value = (1,0,0,1)
class Green(ColorFeature):
    value = (0,1,0,1)
class Yellow(ColorFeature):
    value = (1,1,0,1)
class Cyan(ColorFeature):
    value = (0,1,1,1)
class Magenta(ColorFeature):
    value = (1,0,1,1)

class SmallPositiveIntegerFeature(ValueFeature):
    __metaclass__ = abc.ABCMeta

class V1(SmallPositiveIntegerFeature):
    value = 1
class V2(SmallPositiveIntegerFeature):
    value = 2
class V4(SmallPositiveIntegerFeature):
    value = 4
class V8(SmallPositiveIntegerFeature):
    value = 8
class V16(SmallPositiveIntegerFeature):
    value = 16 

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
    @classmethod
    def suggested_features(self, all_features):
        sets = [s for s in itertools.combinations(all_features, 3)
                    if not (s[0] == s[1] == s[2])]
        return sets

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
    @classmethod
    def clean_suggested_features(self, all_features):
        shape_features = [f for f in all_features if issubclass(f, ShapeFeature)]
        return shape_features

class TripleShapeFeatureSet(TripleFeatureSet, ShapeFeatureSet):
    def __init__(self, features):
        TripleFeatureSet.__init__(self, features)
        ShapeFeatureSet.__init__(self, features)
        self.features = features
    @classmethod
    def suggested_features(self, all_features):
        shape_features = ShapeFeatureSet.clean_suggested_features(all_features)
        sets = TripleFeatureSet.suggested_features(shape_features)
        return sets

class ColorFeatureSet(FeatureSet):
    __metaclass__ = abc.ABCMeta
    def __init__(self, features):
        FeatureSet.__init__(self)
        self.features = features
        for f in features:
            assert(issubclass(f, ColorFeature))
    @classmethod
    def clean_suggested_features(self, all_features):
        return [f for f in all_features if issubclass(f, ColorFeature)]

class TripleColorFeatureSet(TripleFeatureSet, ColorFeatureSet):
    def __init__(self, features):
        TripleFeatureSet.__init__(self, features)
        ColorFeatureSet.__init__(self, features)
        self.features = features
    @classmethod
    def suggested_features(self, all_features):
        color_features = ColorFeatureSet.clean_suggested_features(all_features)
        sets = TripleFeatureSet.suggested_features(color_features)
        return sets

class SmallPositiveIntegerFeatureSet(FeatureSet):
    __metaclass__ = abc.ABCMeta
    def __init__(self, features):
        FeatureSet.__init__(self)
        for f in features:
            assert(issubclass(f, SmallPositiveIntegerFeature))
    @classmethod
    def clean_suggested_features(self, all_features):
        return [f for f in all_features if issubclass(f, SmallPositiveIntegerFeature)]

class TripleSmallPositiveIntegerFeatureSet(TripleFeatureSet, SmallPositiveIntegerFeatureSet):
    def __init__(self, features):
        TripleFeatureSet.__init__(self, features)
        SmallPositiveIntegerFeatureSet.__init__(self, features)
        self.features = features
    @classmethod
    def suggested_features(self, all_features):
        features = SmallPositiveIntegerFeatureSet.clean_suggested_features(all_features)
        sets = TripleFeatureSet.suggested_features(features)
        return sets


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
        self.features = features
        for fs,f in zip(self.feature_sets, self.features):
            # makes sure that features match up to feature sets
            fs(f)
    
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

    @classmethod
    def suggested_feature_sets(cls, all_feature_sets):
        return [[f] for f in all_feature_sets if issubclass(f, DrawableFeatureSet)]

class ColoredLinedShapeFigure(FeatureFigure, CairoFigure):
    def __init__(self, feature_sets, features):
        assert(len(feature_sets) == 3)
        assert(issubclass(feature_sets[0], ShapeFeatureSet))
        assert(issubclass(feature_sets[1], ColorFeatureSet))
        assert(issubclass(feature_sets[2], SmallPositiveIntegerFeatureSet))
        FeatureFigure.__init__(self, feature_sets, features)
        
    def render(self, configuration):
        FeatureFigure.render(self, configuration)
        surface, cr = self.create_context(figure_size, figure_size)
        shape = self.features[0][configuration[0]]
        color = self.features[1][configuration[1]].value
        w = self.features[2][configuration[2]].value
        shape(color=color, line_width=(w,w)).draw(cr)
        return self.surface_to_png(surface)

    @classmethod
    def suggested_feature_sets(cls, all_feature_sets):
        fs1 = [f for f in all_feature_sets if issubclass(f, ShapeFeatureSet)]
        fs2 = [f for f in all_feature_sets if issubclass(f, ColorFeatureSet)]
        fs3 = [f for f in all_feature_sets if issubclass(f, SmallPositiveIntegerFeatureSet)]
        return list(itertools.product(fs1, fs2, fs3))

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
    t3 = [numpy.random.randint(0, 3) for r in range(len(c))]
    for i in xrange(10):
        c = f.transform(c, t3)
        choices[str(c)] = c
    t4 = [numpy.random.randint(0, 3) for r in range(len(c))]
    for i in xrange(10):
        c = f.transform(c, t4)
        choices[str(c)] = c
    if str(answer) in choices:
        del(choices[str(answer)])
    return choices.values()
        


if __name__ == '__main__':
    f = OneSimpleFigure([TripleShapeFeatureSet,], 
                        [[Triangle, Square, Circle],])
    png = f.render([2,])

