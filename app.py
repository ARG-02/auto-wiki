from flask import Flask
from flask_restful import Api
from dotenv import load_dotenv

load_dotenv(".env", verbose=True)

from resources.home_page import HomePage
from resources.search_results import SearchResults

app = Flask(__name__)

api = Api(app)

api.add_resource(HomePage, "/")
api.add_resource(SearchResults, "/search_results")

if __name__ == '__main__':
    app.run(debug=True)
