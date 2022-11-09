import json
import tornado.web
from app.backend.models import UsersTable, RoadmapVotesTable, OperationPointsTable, OperationPointSlugsTable
from app.backend.models import Vote, Milestone, UserLogin, UserRegister, OperationPoint, OperationPointSlug


def delete_none(_dict):
    """Delete None values recursively from all of the dictionaries, tuples, lists, sets"""
    if isinstance(_dict, dict):
        for key, value in list(_dict.items()):
            if isinstance(value, (list, dict, tuple, set)):
                _dict[key] = delete_none(value)
            elif value is None or key is None:
                del _dict[key]

    elif isinstance(_dict, (list, set, tuple)):
        _dict = type(_dict)(delete_none(item) for item in _dict if item is not None)

    return _dict


class BaseHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(f"{self.request.path[1:]}.html")

    def set_default_headers(self):
        if self.application.settings.get('debug'):
            self.set_dev_cors_headers()

    def set_dev_cors_headers(self):
        # For development only
        # Not safe for production
        origin = self.request.headers.get('Origin', '*')
        self.set_header("Access-Control-Allow-Origin", origin)
        self.set_header("Access-Control-Allow-Headers", "*, content-type, authorization, x-requested-with, x-xsrftoken, x-csrftoken")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET')
        # self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, PATCH')
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
    async def post(self):
        data = tornado.escape.json_decode(self.request.body)
        if self.request.uri == '/login':
            data = UserLogin(**data).dict()
            user_table = UsersTable()
            if user_table.username_exists(data['username']):
                if user_table.check_password(data['username'], data['password']):
                    self.set_secure_cookie("username", data['username'])
                    self.write({"status": "logged in",
                                "username": data['username']})
                else:
                    self.write({"status": "wrong password"})
            else:
                self.write({"status": "unknown username",
                            "username": data['username']})

        elif self.request.uri == '/register':
            data = UserRegister(**data).dict()
            user_table = UsersTable()
            if user_table.username_exists(data['username']):
                self.write({"status": "username exists",
                            "username": data['username']})
            elif user_table.email_exists(data['email']):
                self.write({"status": "email exists",
                            "email": data['email']})
            else:
                user_id = user_table.insert_user(**data)

                self.set_secure_cookie("username", data['username'])
                self.write({"status": "registered",
                            "user_id": user_id})


class OperationPointHandler(BaseHandler):
    async def post(self, id_or_slug=None):
        data = tornado.escape.json_decode(self.request.body)
        if id_or_slug is not None and id_or_slug != '/' and id_or_slug[0] == '/':
            id_or_slug = id_or_slug[1:]
        else:
            id_or_slug = None

        if '/operation_point_save' in self.request.uri:
            operation_point_id = id_or_slug
            data = OperationPoint(**data).dict()
            operation_points_table = OperationPointsTable()
            operation_points_table.connect()
            username = data.pop("username")
            if not operation_points_table.user_collection_exists(username):
                operation_points_table.create_user_collection(username)
            if id_or_slug is None:
                result = operation_points_table.insert_operation_points(username, delete_none(data))
            else:
                result = operation_points_table.update_operation_points(username, delete_none(data), operation_point_id)
            if result["result"] is not None:
                self.write({"status": "saved",
                            "operation_point_id": result["operation_point_id"]})
            else:
                self.write({"status": "error saving"})

        if '/operation_point_publish' in self.request.uri:
            data = OperationPointSlug(**data).dict()
            operation_points_table = OperationPointsTable()
            operation_points_slugs_table = OperationPointSlugsTable()
            operation_points_table.connect()
            username = data.pop("username")
            slug = data["slug"]
            if operation_points_slugs_table.slug_exists(slug):
                self.write({"status": "slug exists",
                            "slug": slug})
            else:
                operation_points_slugs_table.insert_slug(slug, username)
                self.write({"status": "published",
                            "slug": slug})
