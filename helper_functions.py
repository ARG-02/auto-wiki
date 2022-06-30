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
            print("No search results returned")
            return links
        links += [item['link'] for item in data.get("items")]
    if num_queries % 10 != 0:
        data = requests.get(
            f'https://www.googleapis.com/customsearch/v1?cx={os.environ["SEARCH_ENGINE_ID"]}&key={os.environ["API_KEY"]}&q="{search_query}"&num={num_queries % 10}').json()
        if not data.get("items"):
            print("No search results returned")
            return links
        links += [item['link'] for item in data.get("items")]
    return links


def allowed_tag(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    if "javascript" in element:
        return False
    return True


def get_link_attributes(links):
    link_info = []
    for link in links:
        # If an error occurs (from requests or soup), print it to the console and move on to the next link
        try:
            # Get html from link and soupify it
            soup = BeautifulSoup(requests.get(link).content, 'html.parser')
            # Get the title and if there is none, put the link in its place
            title = soup.find('head').find('title').text
            if not title:
                title = link
            # Make all text on the website as strings in a list
            descriptions = filter(allowed_tag, soup.findAll(text=True))
            # Take the biggest piece of text
            desc = max(descriptions, key=len)
            # If there was no text found, or if it wasn't big enough, replace it with this:
            if not desc or len(desc) < settings.min_description_length:
                desc = "Visit for more info!"
            # Else, cut it off if it was too big
            else:
                desc = desc if len(desc) < settings.description_cutoff else " ".join(desc[:settings.description_cutoff].split()[:-1]) + "..."

            # Old method for finding text by getting the first string of text that was considered big enough for a desc:
            # for desc_cur in desc:
            #     if len(desc_cur.strip()) >= settings.min_description_length and "javascript" not in desc_cur.lower():
            #         desc = desc_cur.strip()
            #         print(desc)
            #         break

            link_info.append((title, desc, link))
        except BaseException as e:
            print(e)
    return link_info
