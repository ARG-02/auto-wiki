from flask import make_response, render_template, request, redirect, url_for
from flask_restful import Resource


class HomePage(Resource):
    @classmethod
    def get(cls):
        headers = {"Content-Type": "text/html"}
        return make_response(render_template("home_page.html"), 200, headers)

    @classmethod
    def post(cls):
        search_query = request.form.get("q")
        return redirect(f"{request.url_root[:-1]}/search_results?search_query={search_query}", code=302)
