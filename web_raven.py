import webify
from webify.templates.helpers import html


# Middleware
from webify.middleware import install_middleware, EvalException, SettingsMiddleware

app = webify.defaults.app()

@app.subapp(u'/')
@webify.urlable()
def index(req, p):
    

# Server
from webify.http import server
if __name__ == '__main__':
    mail_server = webify.email.LocalMailServer()
    settings = {
                'files_path': lib.location.Location('/home/jperla/Dropbox/         Labmeeting/Development/Docs/'),
                'mail_server': mail_server
               }

    wrapped_app = install_middleware(app, [
                                            SettingsMiddleware(settings),
                                            EvalException,
                                          ])

    server.serve(wrapped_app, host='0.0.0.0', port=8080)
