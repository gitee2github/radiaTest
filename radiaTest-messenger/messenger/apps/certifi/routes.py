from flask import send_file
from flask_restful import Resource


class CaCheck(Resource):
    def get(self):
        return send_file("apps/certifi/check-return.html")