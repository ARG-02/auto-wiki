# ----- Settings ----- #
article_names = [u"Influenza", u"Panama", u"Algorithm", u"Badminton", u"Rice", u"Dog", u"Dragon", u"Scarlet_Johansson", u"Taco_Bell", u"Kidney"]  # Name of the articles to be generated
header_min_bound = 2  # Precision and Recall minimum heading amount to generate
initial_similar_article_count = 20  # The number of articles which are initially searched to be similar
similar_articles_cutoff = 7  # Max number of similar articles that can be used
similarity_threshold = 0.2  # Necessary cosine similarity for similar articles
cosine_similarity_requirement = 0.99

language = 'en'  # Language of wikipedia
blacklisted_categories = ['references', 'see also', 'external links', 'further reading', 'footnotes', 'notes']  # Headers which aren't allowed
wikipedia_model_file = 'wikipedia2vec_model.pkl'  # File name/location of wikipedia2vec model
sentence_transformers_model = 'whaleloops/phrase-bert'  # Model for sentence_transformers (recommended: 'whaleloops/phrase-bert', 'sentence-transformers/all-MiniLM-L6-v2')
headers_output_text_name = "Article Headers Evaluation.txt"  # File name/location of headers output information txt
pr_curve_graphs = "pr_curves"  # Directory name / path for the pr_curve graphs to save too
