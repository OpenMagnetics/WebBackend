import json
import tornado.web
from app.backend.models import Vote, RoadmapVotesTable, User, Milestone


class BaseHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(f"{self.request.path[1:]}.html")

    def set_default_headers(self):
        if self.application.settings.get('debug'): # debug mode is True
            self.set_dev_cors_headers()

    def set_dev_cors_headers(self):
        # For development only
        # Not safe for production
        origin = self.request.headers.get('Origin', '*') # use current requesting origin
        self.set_header("Access-Control-Allow-Origin", origin)
        self.set_header("Access-Control-Allow-Headers", "*, content-type, authorization, x-requested-with, x-xsrftoken, x-csrftoken")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, PATCH')
        self.set_header('Access-Control-Expose-Headers', 'content-type, location, *, set-cookie')
        self.set_header('Access-Control-Request-Headers', '*')
        self.set_header('Access-Control-Allow-Credentials', 'true')

    def options(self, *args, **kwargs):
        # also set a 204 status code for OPTIONS request
        if self.application.settings.get('debug'):
            self.set_status(204)
        else:
            # perhaps do some checks in production mode
            # before setting the status code
            # ...
            self.set_status(204)
        self.finish()


class RoadmapHandler(BaseHandler):
    async def post(self):
        data = tornado.escape.json_decode(self.request.body)
        if self.request.uri == '/is_vote_casted':
            data = Vote(**data).dict()
            vote = RoadmapVotesTable().is_vote_casted(**data)
            self.write({"already_voted": vote})
        elif self.request.uri == '/get_number_votes':
            data = Milestone(**data).dict()
            number_votes = RoadmapVotesTable().get_number_votes(**data)
            self.write({"number_votes": number_votes})
        elif self.request.uri == '/get_all_number_votes':
            number_votes = RoadmapVotesTable().get_all_number_votes()
            number_votes = number_votes.to_dict('records')
            self.write(json.dumps(number_votes))
        elif self.request.uri == '/cast_vote':
            roadmap_votes_table = RoadmapVotesTable()
            if roadmap_votes_table.is_vote_casted(**data):
                self.write({"voted": False})
            else:
                vote = roadmap_votes_table.insert_vote(**data)
                self.write({"voted": vote})


class UserHandler(BaseHandler):
    async def get(self):
        self.render("login.html")
