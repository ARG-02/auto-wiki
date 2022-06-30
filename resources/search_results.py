from flask import request, jsonify, make_response, render_template
from flask_restful import Resource
from markupsafe import Markup

from helper_functions import get_google_results, get_link_attributes
from settings import num_queries, json_results


class SearchResults(Resource):
    @classmethod
    def get(cls):
        search_query = request.args.get("search_query")

        results = get_google_results(num_queries, search_query)
        result_info = get_link_attributes(results)

        if json_results:
            return jsonify({result_info[i][2]: {"title": result_info[i][0], "description": result_info[i][1]} for i in range(len(result_info))})

        replace_info = [f'<div class="searchresult"><a href="{info[2]}" class="title">{info[0]}</a><br><a href="{info[2]}">{info[2]}</a><p>{info[1]}</p></div>' for info in result_info]

        headers = {"Content-Type": "text/html"}
        return make_response(render_template("search_results.html", searchresults=Markup("\n\n".join(replace_info)), search_input=search_query, results=len(result_info)), 200, headers)
