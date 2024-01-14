import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time
from openai import OpenAI
from config import OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)
import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity



def scrape_google_news_with_firefox(query):
    # Selenium FirefoxDriver
    firefox_options = Options()
    firefox_options.add_argument("--headless")  # headless browser mode
    service = Service('/Users/petersweeney/Downloads/geckodriver')  
    driver = webdriver.Firefox(service=service, options=firefox_options)

    # Open Google News search page
    driver.get('https://news.google.com/search?q=taylor%20swift%20when%3A1d&hl=en-US&gl=US&ceid=US%3Aen' + query)

    time.sleep(5)

    # Find all articles
    articles = driver.find_elements(By.CSS_SELECTOR, 'a.JtKRv')

    results = []
    for article in articles[:10]:  # Limit to first 10 articles
        title = article.text
        url = article.get_attribute('href')

        results.append({'title': title, 'url': url})

    # Close the browser
    driver.quit()
    return results

def fetch_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the main article tag
        main_article = soup.find('article') or \
                           soup.find('div', {'id': 'article-content_1-0'})
        if not main_article:
            return "Error: Main article tag not found"

        # Extract all paragraph texts within the article tag
        paragraphs = main_article.find_all('p')
        article_text = ' '.join(paragraph.get_text() for paragraph in paragraphs)

        return article_text
    except Exception as e:
        return "Error fetching article content: " + str(e)

    

def summarize_article_with_gpt3(article_text):

    try:
        response = client.completions.create(model="gpt-3.5-turbo-instruct",  
        prompt="Write a short engaging summary of this article, with a tone fit for millennials but please do not use the word millenial: \n\n" + article_text,
        max_tokens=200)
        return response.choices[0].text.strip()
    except Exception as e:
        return "Error in summarization: " + str(e)

def process_and_summarize_articles(results):
    html_content = ""
    articles_included = 0
    included_articles_content = []  # Store contents of included articles for similarity check

    for article in results:
        content = fetch_article_content(article['url'])

        if "Taylor Swift" not in content:
            continue  # Skip articles that do not mention Taylor Swift

        # Compare with already included articles to check for similarity
        is_similar = False
        for included_content in included_articles_content:
            tfidf_vectorizer = TfidfVectorizer()
            tfidf_matrix = tfidf_vectorizer.fit_transform([content, included_content])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])

            if cosine_sim[0][0] > 0.5:  # Threshold for similarity
                is_similar = True
                break

        if not is_similar and articles_included < 5:
            summary = summarize_article_with_gpt3(content)
            if summary:
                article_html = f'<h2><a href="{article["url"]}" target="_blank">{article["title"]}</a></h2>\n<p>{summary}</p>\n'
                html_content += article_html
                articles_included += 1
                included_articles_content.append(content)

    return html_content

current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
file_name = f"final_newsletter_{current_date_str}.html"

if __name__ == "__main__":
    current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    file_name = f"final_newsletter_{current_date_str}.html"

    results = scrape_google_news_with_firefox('taylor swift when:1d')
    articles_html = process_and_summarize_articles(results)

    with open('/Users/petersweeney/Desktop/Coding/taylorNewsletter/taylorFormat', 'r') as file:
        template_html = file.read()

    final_newsletter_html = template_html.replace('<!-- Insert Articles Here -->', articles_html)
    final_newsletter_html = final_newsletter_html.replace('<!-- Insert Date Here -->', current_date_str)

    with open(file_name, 'w') as file:
        file.write(final_newsletter_html)