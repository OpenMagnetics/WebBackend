import os
import tornado.web
from app.backend import views
import tornado.options

tornado.options.define("SECRET_KEY", default=os.environ.get('SECRET_KEY') or 'you-will-never-guess', type=str)
tornado.options.define("LOCAL_DB_PATH", default='/etc/openmagnetics/', type=str)
tornado.options.define("LOCAL_DB_FILENAME", default='local.db', type=str)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/is_vote_casted", views.RoadmapHandler),
            (r"/get_number_votes", views.RoadmapHandler),
            (r"/get_all_number_votes", views.RoadmapHandler),
            (r"/cast_vote", views.RoadmapHandler),
            (r"/login", views.UserHandler),
        ]
        settings = dict(
            blog_title="Open Magnetics web",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            debug=True,
        )
        super().__init__(handlers, **settings)
