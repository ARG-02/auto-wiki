import requests
from bs4 import BeautifulSoup
import wikipedia2vec

from settings import language, blacklisted_categories, initial_similar_article_count, similar_articles_cutoff, similarity_threshold


def get_similar_articles(article_name, wiki2vec):
    similar_articles = wiki2vec.most_similar(wiki2vec.get_entity(article_name.replace("_", " ")), initial_similar_article_count)

    # print(similar_articles)

    filtered_similar_articles = []

    for item in similar_articles:
        if type(item[0]) == wikipedia2vec.dictionary.Entity and "File:" not in item[0].title and item[0].title.lower() != article_name.lower():
            if item[1] > similarity_threshold:
                filtered_similar_articles.append([item[0].title.replace(" ", "_"), item[1]])
            else:
                break

    filtered_similar_articles = filtered_similar_articles[0:similar_articles_cutoff] if len(similar_articles) > 7 else filtered_similar_articles

    print(f"Similar articles: {filtered_similar_articles}")

    return filtered_similar_articles


# Get all top level section headers from article
def get_headings(article_name):
    page_content = requests.get(f"https://{language}.wikipedia.org/wiki/{article_name}").content
    soup = BeautifulSoup(page_content, "html.parser")
    top_level_fields = soup.select('.toclevel-1')
    text_fields = [field.findAll("span")[1].getText().lower() for field in top_level_fields]

    # Blacklist the references and see also
    return [field for field in text_fields if field not in blacklisted_categories]
