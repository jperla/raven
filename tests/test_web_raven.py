import re
import webify
from webify.middleware import EvalException, SettingsMiddleware
import web_raven

settings = {
    'fff': [web_raven.all_figures, 
            web_raven.all_feature_sets, 
            web_raven.all_features],
}

app = webify.wsgify(web_raven.app, SettingsMiddleware(settings))
from webify.tests import get

def test_pages():
    with get(app, '/list') as r:
        assert(r.status == '200 OK')
        body = r.body
        link = re.findall(r'href="(.*?)"', r.body)[0]
        assert(link.startswith('/ask_matrix/'))
        assert(len(link) > 15)
    with get(app, link) as r:
        assert(r.status == '200 OK')
        image_links = re.findall(r'src="(.*?)"', r.body)
        for link in image_links:
            assert(link.startswith('/matrix_guess/') or 
                   link.startswith('/figure_image/'))
            assert(len(link) > 15)
    for link in image_links:
        with get(app, link) as r:
            assert(r.status == '200 OK')


def check_data_integrity(data):
    id = web_raven.id_from_data(data)
    new_data = web_raven.data_from_id(id)
    assert(data == new_data)

def test_id():
    data = [{},
            {'moulanger':3},
            {'fg':3,'fg':6},
            {'fg':3,'fg':6,'f':[4,2,6,4,7,3,2,1]},
           ]
    for d in data:
        yield check_data_integrity, d

def test_random_matrix():
    #TODO: jperla: make this not random?
    for i in xrange(1):
        world = web_raven.world
        f = web_raven.random_matrix(*world)
        assert(len(web_raven.id_from_matrix_specification(f, *world)) > 10)

def test_generate_random_matrix():
    with get(app, '/generate_random_matrix') as r:
        assert(r.status == '302 Found')
        #TODO: jperla: check the redirect
        body = r.body
    
