import json

import wikipedia as wiki
from collections import defaultdict, Counter
import re
import heapq
from threading import Thread
import time

from sentence_transformers import SentenceTransformer
from transformers import BertForSequenceClassification, BertTokenizer
import torch
import numpy as np
import spacy
import language_tool_python

import settings

from tqdm import tqdm
import urllib

import requests
from bs4 import BeautifulSoup
import html_text

import nltk

# from os.path import isfile, join
#
# from sklearn.metrics.pairwise import cosine_similarity
#
# import networkx as nx

from transformers import pipeline
from nltk.tokenize import word_tokenize

from helper_functions import get_google_results

# Removes extraneous s from the end of a title
def clean_title(title):
    return title[:-1].lower() if title[-1] == 's' else title.lower()

# Get filtered or raw (dependent on raw argument) sub sections for an article's content
def get_subsections(data, raw=False):
    subsections = re.findall('\n== ([a-zA-z ]+) ==', data)
    if raw:
        return [subsection.lower() for subsection in subsections]

    subsections = [clean_title(subsection) for subsection in subsections]
    blacklisted_articles = ["reference", "see also", "external link", "note", "further reading"]
    subsections = [subsection.lower() for subsection in subsections if subsection not in blacklisted_articles]
    return subsections


# extracts subsections and content from related pages (cleans formatting)
def get_important_subsections_and_content(related_titles):
    topics = []
    related_paper_section_content = defaultdict(list)
    for related_title in related_titles:
        # Get a WikipediaPage for every string title
        try:
            related_page = wiki.WikipediaPage(title=related_title)
        except wiki.DisambiguationError as e:
            continue

        content = (related_page.content).lower()
        subsections = get_subsections(content, raw=True)
        topics.extend(get_subsections(content))
        delimiters = ''
        for subsection in subsections:
            delimiters += '== ' + str(subsection) + ' ==|'
        delimiters = delimiters[:-1]
        words = re.split(delimiters, content)
        words = [word.replace('\n', '') for word in words]
        related_paper_section_content['intro'].append(str(words[0]))
        for i, subsection in enumerate(subsections):
            if subsection[-1] == 's':
                subsection = subsection[:-1]
            related_paper_section_content[subsection].append(str(words[i+1]))

    common_subsections = Counter(topics)
    important_subsections = heapq.nlargest(settings.SUBSECTIONS, common_subsections, key=common_subsections.__getitem__)
    return important_subsections, related_paper_section_content


def get_paragraphs(result, headers, url_to_title_mapping, raw_dataset, count_of_paras):
    temp_dataset = ''
    paragraphs = []
    temp_cleaned_para = []
    try:
        page = requests.get(result, timeout=(5, 10), headers=headers)
    except:
        return None
    soup = BeautifulSoup(page.content, "html.parser")
    p = soup.find_all('p')

    title = str(soup.find('title'))
    url_to_title_mapping[result] = html_text.extract_text(title)

    for x in p:
        paragraphs.append(str(x))
    for i, para in enumerate(paragraphs):
        if para != '':
            temp_cleaned_para.append(html_text.extract_text(para, guess_layout=False))

    for i, para in enumerate(temp_cleaned_para):
        if 30 < len(nltk.word_tokenize(para)) < 150:
            para = re.sub('[\[].*?[\]]', '', para)
            raw_dataset[result].append(para)
            count_of_paras[0] += 1

    # print(url_to_title_mapping, raw_dataset, count_of_paras)


def summarize_paragraph(paragraphs, tokenizer, nlp, summarizer, summarized_dataset, subheading, url, url_to_title_mapping):
    data = ''.join(paragraphs)
    if len(tokenizer([data])['input_ids'][0]) > 1023:
        count = 0
        data_nlp = nlp(data)
        sentences = list(data_nlp.sents)
        # print(sentences)
        data = ""
        for sentence in sentences:
            sentence = str(sentence)
            # print(type(sentence))
            count += (2 + len(word_tokenize(sentence)))
            if count < 900:
                data += sentence
    summary_text = summarizer(data, max_length=50, min_length=25)[0]['summary_text']  # + "..."
    # tool = language_tool_python.LanguageTool('en-US')
    # summary_text = tool.correct(summary_text)
    # tool.close()
    summarized_dataset[subheading][url] = {'title': url_to_title_mapping[url], 'description': summary_text}


def summarize_sections(tokenizer, nlp, summarizer, summarized_dataset, subheading, url_to_title_mapping, websites):
    threads = [Thread(target=summarize_paragraph, args=(paragraphs, tokenizer, nlp, summarizer, summarized_dataset, subheading, url, url_to_title_mapping)) for
               url, paragraphs in websites.items()]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

def generate_article(title: str):
    # Hyperparameters
    TITLE = clean_title(title)
    RELATED_TITLES = wiki.search(TITLE)

    important_subsections, related_paper_section_content = get_important_subsections_and_content(RELATED_TITLES)
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    topic_embeddings = defaultdict(list)
    # Creates word embeddings for subsection headings
    features = []
    for subsections in important_subsections:
        paras = related_paper_section_content[subsections]
        topic_emb = np.average(model.encode(paras), 0)
        features.append(list(topic_emb))
    features_tensor = torch.tensor(features)

    results = get_google_results(settings.num_queries, title)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    raw_dataset = defaultdict(list)
    count_of_paras = [0]
    url_to_title_mapping = defaultdict(str)

    # Get website urls and the paragraph tags in them
    threads = [Thread(target=get_paragraphs, args=(result, headers, url_to_title_mapping, raw_dataset, count_of_paras)) for result in results]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    count_of_paras = count_of_paras[0]

    topic_subheading_dataset = defaultdict(lambda: defaultdict(list))
    for webpage, data in raw_dataset.items():
        paragraph_embedding = torch.tensor(model.encode(data))
        labels = torch.argmax((features_tensor @ paragraph_embedding.T), axis=0)
        for paragraph, label in zip(data, labels):
            if len(topic_subheading_dataset[important_subsections[label]]) > 5:
                continue
            topic_subheading_dataset[important_subsections[label]][webpage].append(paragraph)

    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased',
                                              do_lower_case=True)
    summarizer = pipeline('summarization', model="sshleifer/distilbart-cnn-12-6")

    nlp = spacy.load('en_core_web_sm')

    # subtopic -> topic_url -> title, description
    summarized_dataset = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))

    threads = [Thread(target=summarize_sections, args=(tokenizer, nlp, summarizer, summarized_dataset, subheading, url_to_title_mapping, websites)) for subheading, websites in topic_subheading_dataset.items()]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    return summarized_dataset
