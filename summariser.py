"""
Here, we take a list of URLs (maybe generated by gdelt.py, or more likely analyser.py, but could be anything) and we
pull their content then summarise them. This is done through the "newspaper" module (called "newspaper3k" on python 3).
"""

# Modules to install (see requirements.txt)
import newspaper
import nltk

# Needed for summarisation
nltk.download('punkt')

# Gets the urls, then one by one summarises them and prints the summaries
with open('urls.txt', 'r', encoding='utf-8') as f:
    urls = f.read().splitlines()
for url in urls:
    print(url)
    article = newspaper.Article(url)
    try:
        article.download()
        article.parse()
        article.nlp()
    except newspaper.article.ArticleException:
        print('Error fetching, parsing, or summarising article.')
        continue
    # print(article.text)  # Print the full text
    print(article.summary)  # Print a summary from nltk
    print()
