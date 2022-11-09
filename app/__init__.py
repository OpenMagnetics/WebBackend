import os
import tornado.web
from app.backend import views
import tornado.options

tornado.options.define("SECRET_KEY", default=os.environ.get('SECRET_KEY') or 'you-will-never-guess', type=str)
tornado.options.define("LOCAL_DB_PATH", default='/etc/openmagnetics/', type=str)
tornado.options.define("LOCAL_DB_FILENAME", default='local.db', type=str)

tornado.options.define("OM_USERS_DB_USER", default='alfvii', type=str)
tornado.options.define("OM_USERS_DB_PASSWORD", default='2Galletas!', type=str)
# tornado.options.define("OM_USERS_DB_ADDRESS", default='localhost', type=str)
tornado.options.define("OM_USERS_DB_ADDRESS", default='autop.cvwabe7wiekt.eu-west-1.rds.amazonaws.com', type=str)
tornado.options.define("OM_USERS_DB_NAME", default='OpenMagnetics', type=str)
tornado.options.define("OM_USERS_DB_PORT", default='5432', type=str)
tornado.options.define("OM_USERS_DB_DRIVER", default='pgsql', type=str)

tornado.options.define("OM_OPERATION_POINTS_DB_USER", default='AlfVII', type=str)
tornado.options.define("OM_OPERATION_POINTS_DB_PASSWORD", default='AAaa7111492!', type=str)
tornado.options.define("OM_OPERATION_POINTS_DB_ADDRESS", default='openmagnetics.owo3m1h.mongodb.net', type=str)
tornado.options.define("OM_OPERATION_POINTS_DB_DRIVER", default='mongodb+srv', type=str)



class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/is_vote_casted", views.RoadmapHandler),
            (r"/get_number_votes", views.RoadmapHandler),
            (r"/get_all_number_votes", views.RoadmapHandler),
            (r"/cast_vote", views.RoadmapHandler),
            (r"/login", views.UserHandler),
            (r"/register", views.UserHandler),
            (r"/operation_point_publish", views.OperationPointHandler),
            (r"/operation_point_save(/[^/]*)?", views.OperationPointHandler),
        ]
        settings = {
            "blog_title": "Open Magnetics web",
            "template_path": os.path.join(os.path.dirname(__file__), "templates"),
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
            "xsrf_cookies": False,
            "cookie_secret": "Light is the left hand of darkness and darkness the right hand of light. Two are one, life and death, lying together like lovers in kemmer, like hands joined together, like the end and the way.",
            "login_url": "/",
            "debug": True,
        }
        super().__init__(handlers, **settings)
