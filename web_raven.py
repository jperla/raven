#!/usr/bin/env python
import zlib
import simplejson
import base64

import numpy

import webify
from webify.templates.helpers import html
from webify.controllers import webargs
from webify.middleware import EvalException, SettingsMiddleware

from raven import *


app = webify.defaults.app()

@app.subapp(u'/')
@webify.urlable()
def index(req, p):
    p(u'Hello, world!')

all_figures = [OneSimpleFigure, 
               ColoredLinedShapeFigure,
              ]
all_feature_sets = [TripleShapeFeatureSet,
                    TripleColorFeatureSet,
                    TripleSmallPositiveIntegerFeatureSet,
                   ]
all_features = [Triangle, Square, Circle,
                Blue, Red, Green, Yellow, Magenta, Cyan,
                V1, V2, V4, V8, V16,
               ]

def random_element(array):
    return array[numpy.random.randint(0, len(array))]

def random_matrix(all_figures, all_feature_sets, all_features):
    figure = random_element(all_figures)
    feature_sets = random_element(figure.suggested_feature_sets(all_feature_sets))
    features = [random_element(fs.suggested_features(all_features)) for fs in feature_sets]
    f = figure(feature_sets, features)
    c = [numpy.random.randint(0, 3) for a in features]
    t1 = [numpy.random.randint(0, 3) for a in features]
    t2 = [numpy.random.randint(0, 3) for a in features]
    return {'fg': figure, 'c': c, 't1': t1, 't2': t2, 'fs': feature_sets, 'f': features}
    

@app.subapp()
@webify.urlable()
def list(req, p):
    fg = 0
    fs = [0,]
    f = [[0,1,2],]
    c = [2,]
    t1 = [1,]
    t2 = [2,]
    id = id_from_data({'fg':fg,'fs':fs,'f':f,'c':c,'t1':t1,'t2':t2})
    p(template_list_puzzle([id]))

@webify.template()
def template_list_puzzle(p, ids):
    with p(html.ol()):
        for id in ids:
            p(html.li(html.a(ask_matrix.url(id), id)))

@app.subapp()
@webify.urlable()
def generate_random_matrix(req, p):
    pool = req.settings['fff']
    variables = random_matrix(*pool)
    print variables
    id = id_from_matrix_specification(variables, *pool)
    webify.http.redirect_page(p, ask_matrix.url(id))

def id_from_matrix_specification(spec, 
                                 all_figures, all_feature_sets, all_features):
    data = {'fg': all_figures.index(spec['fg']),
            'fs': [all_feature_sets.index(f) for f in spec['fs']],
            'f': [[all_features.index(f) for f in fs] for fs in spec['f']],
            'c': spec['c'],
            't1': spec['t1'],
            't2': spec['t2']}
    print data
    id = id_from_data(data)
    return id

def figure_id(figure, c):
    fg = all_figures.index(figure.__class__)
    assert(fg != -1)
    fs = [all_feature_sets.index(i) for i in figure.feature_sets]
    f = [[all_features.index(i) for i in features] for features in figure.features]
    return id_from_data({'fs':fs,'f':f,'fg':fg,'c':c})


@app.subapp()
@webargs.RemainingUrlableAppWrapper()
def ask_matrix(req, p, id):
    f, c, t1, t2 = matrix_from_id(id)
    cmatrix = cmatrix_from_one_transition(f, c, t1)
    cmatrix = cmatrix_from_two_transitions(f, c, t1, t2)
    answer_id = figure_id(f, cmatrix[2][2])
    if req.method == 'GET':
        choice_ids = [figure_id(f,i) for i in generate_choices(f, c, t1, t2, cmatrix[2][2])]
        p(template_ask_matrix(id, f, answer_id, choice_ids))
    else:
        guessed = req.params.get('figure', 'bob')
        p(template_answered_matrix(id,
                                   f,
                                   answer_id,
                                   guessed))

@webify.template()
def template_answered_matrix(p, matrix_id, f, answer, guessed):
    with p(html.html()):
        with p(html.head()):
            p(html.title('Answered a matrix'))
    with p(html.body()):
        if answer == guessed:
            p(html.h1('Correct!'))
        else:
            p(html.h1('Sorry, wrong answer :('))
        p(html.h2('You guessed: '))
        p(html.p(html.img(figure_image.url(guessed))))
        p(html.p(html.a(ask_matrix.url(matrix_id), 'Back to this matrix')))
        p(html.p(html.a(generate_random_matrix.url(), 'or Generate a new matrix')))
        p(html.p(html.img(matrix_guess.url(matrix_id))))
        

@webify.template()
def template_ask_matrix(p, id, figure, answer, choices):
    with p(html.html()):
        with p(html.head()):
            p(html.title('Answer a matrix'))
    with p(html.body()):
        p(html.p(html.img(matrix_guess.url(id))))
        choice_html = [helper_choice(figure, c) 
                        for c in choices] + [helper_choice(figure, answer)]
        numpy.random.shuffle(choice_html)
        with p(html.form()):
            for c in choice_html:
                p.sub(c)
            p(html.input_submit(value='Answer'))

@webify.template()
def helper_choice(p, figure, choice):
    with(p(html.input_radio('figure', choice))):
        p(html.img(figure_image.url(choice)))
    

def data_from_id(id):
    data = base64.b64decode(id)
    return simplejson.loads(zlib.decompress(data, -15))

def id_from_data(data):
    #return base64.b64encode(zlib.compress(simplejson.dumps(data), 9), u'-_')
    c = zlib.compress(simplejson.dumps(data), 9)[2:-4]
    return base64.b64encode(c)


@app.subapp()
@webargs.RemainingUrlableAppWrapper()
def matrix_guess(req, p, id):
    f, c, t1, t2 = matrix_from_id(id)
    cmatrix = cmatrix_from_one_transition(f, c, t1)
    cmatrix = cmatrix_from_two_transitions(f, c, t1, t2)
    png,_,_ = rpm_images(f, cmatrix, [])
    #TODO: jperla: make this simpler
    k,v = webify.http.headers.content_types.image_png
    p.headers[k] = v
    p.encoding = None
    p(png)


@app.subapp()
@webargs.RemainingUrlableAppWrapper()
def figure_image(req, p, id):
    f, c = figure_from_id(id)
    png = f.render(c)
    #TODO: jperla: make this simpler
    k,v = webify.http.headers.content_types.image_png
    p.headers[k] = v
    p.encoding = None
    p(png)

def figure_from_id(id):
    data = data_from_id(id)
    figure = all_figures[data['fg']]
    fs = [all_feature_sets[i] for i in data['fs']]
    features = [[all_features[i] for i in features] for features in data['f']]
    f = figure(fs, features)
    c = data['c']
    return f, c
    

def matrix_from_id(id):
    data = data_from_id(id)
    figure = all_figures[data['fg']]
    feature_sets = [all_feature_sets[fs] for fs in data['fs']]
    features = [[all_features[f] for f in features] for features in data['f']]
    c = data['c']
    t1, t2 = data['t1'], data['t2']
    f = figure(feature_sets, features)
    return f, c, t1, t2


@app.subapp()
@webify.urlable()
def debug(req, p):
    '''
    f = OneSimpleFigure([TripleShapeFeatureSet,],
                                [[Triangle, Square, Circle],])
    c = [2,]
    cmatrix = cmatrix_from_one_transition(f, c, [1,])
    cmatrix = cmatrix_from_two_transitions(f, c, [1,], [2,])
    '''
    f = ColoredLinedShapeFigure([TripleShapeFeatureSet,
                                 TripleColorFeatureSet,
                                 TripleSmallPositiveIntegerFeatureSet,],
                                    [[Triangle, Square, Circle],
                                     [Yellow, Blue, Red],
                                     [V2, V8, V16]])
    c = [2,1,0]
    t1, t2 = [1,1,1], [2,1,2]
    cmatrix = cmatrix_from_one_transition(f, c, t1)
    cmatrix = cmatrix_from_two_transitions(f, c, t1, t2)
    #TODO: jperla: take these from settings
    data = random_matrix(all_figures, all_feature_sets, all_features)
    f, c, t1, t2 = data['fg'], data['c'], data['t1'], data['t2']
    cmatrix = cmatrix_from_two_transitions(f, c, t1, t2)
    png = rpm_from_cmatrix(f, cmatrix)
    p.headers = [webify.http.headers.content_types.image_png]
    p(png)

from webify.http import server
if __name__ == '__main__':
    mail_server = webify.email.LocalMailServer()
    settings = {
                'mail_server': mail_server,
                'fff': [all_figures, all_feature_sets, all_features],
               }
    wsgi_app = webify.wsgify(app, 
                                        SettingsMiddleware(settings),
                                        EvalException,
                                     )

    print 'Loading server...'
    server.serve(wsgi_app, host='0.0.0.0', port=8087, reload=True)
