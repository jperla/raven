import re
import webify
import web_raven

app = webify.wsgify(web_raven.app)
from webify.tests import get

def test_pages():
    with get(app, '/list') as r:
        assert(r.status == '200 OK')
        body = r.body
        #assert(body == 0)
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
