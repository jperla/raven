
import abc

class Figure:
    __metaclass__ = abc.ABCMeta
    @abstractmethod
    def render():
        pass

class FeatureFigure(Figure):
    __metaclass__ = abc.ABCMeta
    def __init__(self, features, configuration):
        assert(len(features) == len(configuration))
        self.features = features
        self.configuration = configuration
    
    @classmethod
    def transform(cls, figure, amounts):
        assert(len(amounts) == len(figure.configuration))
        for a,f,c in zip(amounts, figure.features, figure.configurations):
            if a > 0:
                assert(isinstance(f, TransformableFeature))
                assert(f.can_transform(c, a))
        new_configurations = [f.transform(c, a) 
                                        for f,c,a in zip(figure.features, 
                                                         figure.configurations,
                                                         amounts)]
        new_figure = cls.__init__(figure.features, new_configuration)
        return new_figure

class OneSimpleFigure(FeatureFigure):
    def __init__(self, features, configuration):
        assert(len(features) == 1)
        assert(isinstance(features[0], DrawableFeature))
        FeatureFigure.__init__(self, features, configuration)
        
    def render():
        feature = self.features[0][self.configuration[0]]

class Feature(object):
    __metaclass__ = abc.ABCMeta

class DrawableFeature(Feature):
    __metaclass__ = abc.ABCMeta
    @abstractmethod
    def draw():
        pass

class ShapeFeature(DrawableFeature):
    __metaclass__ = abc.ABCMeta
    #TODO: jperla: fill this in

class Triangle(ShapeFeature):
    pass

class Square(ShapeFeature):
    pass

class Circle(ShapeFeature):
    pass

class FeatureSet(object):
    __metaclass__ = abc.ABCMeta

class TransformableFeatureSet(FeatureSet):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, features):
        self.features = features

    def transform(self, configuration, amount):
        return configuration + amount

    def can_transform(self, configuration, amount):
        return 0 < amount <= configuration + amount < len(self.features)

class DrawableFeatureSet(TransformableFeatureSet):
    __metaclass__ = abc.ABCMeta
    #TODO: jperla: assert all drawable

class RingFeatureSet(TransformableFeatureSet):
    __metaclass__ = abc.ABCMeta
    
    def transform(self, configuration, amount):
        t = TransformableFeatureSet.transform(self, configuration, amount)
        if t < len(self.features):
            return t
        else:
            return t - len(self.features)

    def can_transform(self, configuration, amount):
        return 0 < amount < len(configuration)

class TripleFeatureSet(RingFeatureSet):
    __metaclass__ = abc.ABCMeta
    def __init__(self, configurations):
        assert(len(configurations) == 3)
        RingFeature.__init__(self, configurations)

class TripleDrawableFeatureSet(TripleFeatureSet, DrawableFeatureSet):
    __metaclass__ = abc.ABCMeta
    #TODO: jperla: merge these

class ShapeFeatureSet(DrawableFeatureSet):
    __metaclass__ = abc.ABCMeta
    #TODO: jperla: assert everything shape

class TripleShapeFeatureSet(TripleFeatureSet, ShapeFeatureSet):
    #TODO: jperla: merge these
    __metaclass__ = abc.ABCMeta
    

def render(feature_sets, features, configurations):
    #TODO: jperla: do the magic
    pass
