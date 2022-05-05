import os

# retrieves english dump from the official wikimedia source and build
os.system("wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2")
os.system("wikipedia2vec train enwiki-latest-pages-articles.xml.bz2 wiki_model")
