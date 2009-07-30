
from raven import *

def test_render_figure():
    f = OneSimpleFigure([TripleShapeFeatureSet,], [[Triangle, Square, Circle],])
    png = f.render([2,])

def test_fail_on_wrong_features():
    try:
        f = OneSimpleFigure([TripleShapeFeatureSet,], [[Triangle, Square, ],])
    except:
        pass
    else:
        raise Exception('failed to fail')

def test_transform():
    f = OneSimpleFigure([TripleShapeFeatureSet,], [[Triangle, Square, Circle],])
    assert [0,] == f.transform([1], [2,])
    assert [2,] == f.transform([1], [1,])
    assert [0,] == f.transform([2], [1,])
    assert [1,] == f.transform([2], [2,])

