import requests
import os
from bs4 import BeautifulSoup
from bs4.element import Comment

import settings


def get_google_results(num_queries, search_query):
    links = []
    for i in range(num_queries // 10):
        data = requests.get(
            f'https://www.googleapis.com/customsearch/v1?cx={os.environ["SEARCH_ENGINE_ID"]}&key={os.environ["API_KEY"]}&q="{search_query}"&num=10&start={1 + i}').json()
        if not data.get("items"):
            print("You ran out of search queries")
            return links
        links += [item['link'] for item in data.get("items")]
    if num_queries % 10 != 0:
        data = requests.get(
            f'https://www.googleapis.com/customsearch/v1?cx={os.environ["SEARCH_ENGINE_ID"]}&key={os.environ["API_KEY"]}&q="{search_query}"&num={num_queries % 10}').json()
        if not data.get("items"):
            print("You ran out of search queries")
            return links
        links += [item['link'] for item in data.get("items")]
    return links


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def get_link_attributes(links):
    link_info = []
    for link in links:
        try:
            soup = BeautifulSoup(requests.get(link).content, 'html.parser')
            title = soup.find('head').find('title').text
            if not title:
                title = link
            desc = filter(tag_visible, soup.findAll(text=True))
            for desc_cur in desc:
                if len(desc_cur.strip()) >= settings.min_description_length and "javascript" not in desc_cur.lower():
                    desc = desc_cur.strip()
                    print(desc)
                    break
            if desc == None:
                desc = "Visit for more info!"
            else:
                desc = desc if len(desc) < settings.description_cutoff else " ".join(desc[:settings.description_cutoff].split()[:-1]) + "..."
            link_info.append((title, desc, link))
        except BaseException as e:
            print(e)
    return link_info
