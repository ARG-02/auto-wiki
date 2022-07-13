from flask import request, make_response, render_template
from flask_restful import Resource
from markupsafe import Markup

from model import generate_article
from settings import json_results


class SearchResults(Resource):
    @classmethod
    def get(cls):
        search_query = request.args.get("search_query")

        # results = get_google_results(num_queries, search_query)
        result_info = generate_article(search_query)
        # result_info = get_link_attributes(results)

        if json_results:
            return result_info

        # if json_results:
        #     return jsonify({result_info[i][2]: {"title": result_info[i][0], "description": result_info[i][1]} \
        #     for i in range(len(result_info))})
        #

        sections = []
        footnotes = []

        footnote_count = 0
        for title in result_info.keys():
            text = f"<h2>{title.capitalize()}</h2>\n"

            links = result_info[title]
            for link in links.keys():
                footnote_count += 1
                text += links[link]['description']
                text += f'<sup><a href="#footnotes">[{footnote_count}]</a></sup> '
                footnotes.append(f'<a href="{link}">[{footnote_count}]. {links[link]["title"]}</a>')
            text += "</p>"
            sections.append(text)

        headers = {"Content-Type": "text/html"}
        return make_response(render_template("search_article.html", sections=Markup("\n\n".join(sections)), footnotes=Markup("\n".join(footnotes))), 200, headers)

        # headers = {"Content-Type": "text/html"}
        # return make_response(render_template("search_results.html", searchresults=Markup("\n\n".join(replace_info)), \
        # search_input=search_query, results=len(result_info)), 200, headers)

