from wikipedia2vec import Wikipedia2Vec
import time
from sentence_transformers import SentenceTransformer

from helper_functions.cosine_similarity import cosine_similarity
from helper_functions.obtain_articles import get_similar_articles, get_headings
from settings import *


start = time.time()

print("Starting Load")
wiki2vec = Wikipedia2Vec.load(wikipedia_model_file)
sentence_transformer = SentenceTransformer(sentence_transformers_model)
print("Loaded models")

text = ""

for article_name in article_names:
    print(article_name+":")

    print("Getting section headers (Using wiki2vec similarity)...")
    sectioned_headers = [[get_headings(article[0]), article[1]] for article in get_similar_articles(article_name, wiki2vec)]
    print(sectioned_headers)
    header_scores = {}
    for article in sectioned_headers:
        # get all headers in the similar article
        for header in article[0]:
            if header in list(header_scores.keys()):
                header_scores[header] += article[1]
            else:
                header_scores[header] = article[1]

    header_set = [[header_score[0], header_score[1]] for header_score in header_scores.items()]  # [("symptoms", 14.3234), ("history", 11.4321), etc.]

    similarity_pairs = []  # [(("symptoms", 14.3234), ("signs and symptoms", 15.3221), 0.994), etc.]
    for header_1 in range(len(header_set)):
        for header_2 in range(header_1+1, len(header_set)):
            similarity_pairs.append([header_set[header_1], header_set[header_2], cosine_similarity(header_set[header_1][0], header_set[header_2][0], sentence_transformer)])
    similarity_pairs = [pair for pair in sorted(similarity_pairs, key=lambda x: x[2], reverse=True) if pair[2] > cosine_similarity_requirement]

    for pair in range(len(similarity_pairs)):
        if len(header_set) <= 5:
            break

        if similarity_pairs[pair][0] in header_set and similarity_pairs[pair][1] in header_set:
            # first header has bigger score
            if similarity_pairs[pair][0][1] > similarity_pairs[pair][1][1]:
                # add small score to big score and get rid of the smaller score
                header_set[header_set.index(similarity_pairs[pair][0])][1] += \
                header_set[header_set.index(similarity_pairs[pair][1])][1]
                header_set.remove(similarity_pairs[pair][1])
            else:
                header_set[header_set.index(similarity_pairs[pair][1])][1] += \
                header_set[header_set.index(similarity_pairs[pair][0])][1]
                header_set.remove(similarity_pairs[pair][0])

    print(f"Header set: {header_set}")

    # Cut off if it is more than header_requirement
    if len(header_set) > header_requirement:
        generated_headings = [header[0] for header in sorted(header_set[:header_requirement], key=lambda x: x[1], reverse=True)]
    else:
        generated_headings = [header[0] for header in sorted(header_set, key=lambda x: x[1], reverse=True)]

    average_headers = sum([len(article_headers[0]) for article_headers in sectioned_headers]) // len(sectioned_headers)
    print(f"Average number of headers in similar articles: {average_headers}")

    print(generated_headings)

    true_positive = 0
    false_positive = 0
    count = 0

    gt_headings = get_headings(article_name)
    keyword_matches = {}
    ordered_keywords = []
    for keyword in generated_headings:
        if count == len(gt_headings):
            break

        keywords_found = []
        for gt_heading in gt_headings:
            if gt_heading in list(keyword_matches.values()):
                continue
            cosine_sim = cosine_similarity(keyword, gt_heading, sentence_transformer)
            if cosine_sim > cosine_similarity_requirement:
                keywords_found.append((gt_heading, cosine_sim))
                true_positive += 1
                break
            if keyword in gt_heading or gt_heading in keyword:
                keywords_found.append((gt_heading, 1))
                true_positive += 1
                break

        if not keywords_found:
            false_positive += 1

        else:
            best_keyword_match = ("", 0)
            for keyword_found in keywords_found:
                if keyword_found[1] > best_keyword_match[1]:
                    best_keyword_match = keyword_found
            keyword_matches[keyword] = best_keyword_match[0]
            ordered_keywords.append(keyword)

    false_negative = len(gt_headings) - count
    # (Impossible to divide by 0 unless ground truth has 0 headings)
    precision = true_positive / (true_positive + false_positive)
    recall = true_positive / (true_positive + false_negative)

    ordering_metric = 0
    pairs = []
    for header_1 in range(len(ordered_keywords)):
        for header_2 in range(header_1+1, len(ordered_keywords)):
            pairs.append((ordered_keywords[header_1], ordered_keywords[header_2]))

    print("Keyword matches: " + str(keyword_matches))

    for pair in pairs:
        if gt_headings.index(keyword_matches[pair[0]]) < gt_headings.index(keyword_matches[pair[1]]):
            ordering_metric += 1

    if len(pairs) == 0:
        ordering_metric = 0
    else:
        ordering_metric /= len(pairs)

    print(f"Precision {precision}")
    print(f"Recall {recall}")
    print(f"Heading order {ordering_metric}")

    text += \
        f"""
    {article_name.replace("_", " ")}

    Generated headings: {[generated_headings]}
    Wikipedia headings: {gt_headings}
    Precision: {precision}
    Recall: {recall}
    Heading order: {ordering_metric}

    {"-"*25}
    """

    with open(headers_output_text_name, "w+") as document:
        document.write(text)

print("Done!")
print("Time elapsed in seconds: " + str(round(time.time() - start)))
