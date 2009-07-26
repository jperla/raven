#!/usr/bin/env python
import zlib
import simplejson
import base64

from raven import *
import webify
from webify.templates.helpers import html
from webify.controllers import webargs

from webify.middleware import EvalException, SettingsMiddleware

app = webify.defaults.app()

@app.subapp(u'/')
@webify.urlable()
def index(req, p):
    p(u'Hello, world!')

all_figures = [OneSimpleFigure, ]
all_feature_sets = [TripleShapeFeatureSet,]
all_features = [Triangle, Square, Circle,]

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
@webargs.RemainingUrlableAppWrapper()
def ask_matrix(req, p, id):
    f, c, t1, t2 = matrix_from_id(id)
    cmatrix = cmatrix_from_one_transition(f, c, t1)
    cmatrix = cmatrix_from_two_transitions(f, c, t1, t2)
    answer = cmatrix[2][2]
    choices = generate_choices(f, c, t1, t2, cmatrix[2][2])
    p(template_ask_matrix(matrix_guess.url(id), f, answer, choices))

import numpy

@webify.template()
def template_ask_matrix(p, matrix_url, figure, answer, choices):
    with p(html.html()):
        with p(html.head()):
            p(html.title('Answer a matrix'))
    with p(html.body()):
        p(html.p(html.img(matrix_url)))
        choice_html = [helper_choice(figure, c) 
                        for c in choices] + [helper_choice(figure, answer, True)]
        numpy.random.shuffle(choice_html)
        with p(html.form()):
            for c in choice_html:
                p.sub(c)
            p(html.input_submit(value='Answer'))

@webify.template()
def helper_choice(p, figure, choice, answer=False):
    with(p(html.input_radio('figure', str(answer)))):
        p(html.img(figure_image.url(figure_id(figure, choice))))

def figure_id(figure, c):
    fg = all_figures.index(figure.__class__)
    assert(fg != -1)
    fs = [all_feature_sets.index(i) for i in figure.feature_sets]
    f = [[all_features.index(i) for i in features] for features in figure.features]
    return id_from_data({'fs':fs,'f':f,'fg':fg,'c':c})
    

def data_from_id(id):
    id = str(id)
    return simplejson.loads(zlib.decompress(base64.b64decode(id, u'-_')))

def id_from_data(data):
    #return base64.b64encode(zlib.compress(simplejson.dumps(data), 9), u'-_')
    c = zlib.compress(simplejson.dumps(data), 9)
    return c.encode('base64')


@app.subapp()
@webargs.RemainingUrlableAppWrapper()
def matrix_guess(req, p, id):
    f, c, t1, t2 = matrix_from_id(id)
    cmatrix = cmatrix_from_one_transition(f, c, t1)
    cmatrix = cmatrix_from_two_transitions(f, c, t1, t2)
    png,_,_ = rpm_images(f, cmatrix, [])
    p.headers = [webify.http.headers.content_types.image_png]
    p(png)


@app.subapp()
@webargs.RemainingUrlableAppWrapper()
def figure_image(req, p, id):
    f, c = figure_from_id(id)
    png = f.render(c)
    p.headers = [webify.http.headers.content_types.image_png]
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
    f = OneSimpleFigure([TripleShapeFeatureSet,],
                                [[Triangle, Square, Circle],])
    c = [2,]
    cmatrix = cmatrix_from_one_transition(f, c, [1,])
    cmatrix = cmatrix_from_two_transitions(f, c, [1,], [2,])
    png = rpm_from_cmatrix(f, cmatrix)
    p.headers = [webify.http.headers.content_types.image_png]
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
