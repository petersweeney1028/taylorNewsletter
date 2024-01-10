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
    for article in articles[:10]:  # Limit to first 4 articles
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
        prompt="Write a short engaging summary of this article, with a tone fit for millennials: \n\n" + article_text,
        max_tokens=200)
        return response.choices[0].text.strip()
    except Exception as e:
        return "Error in summarization: " + str(e)

def process_and_summarize_articles(results):
    all_summaries = []
    for article in results:
        content = fetch_article_content(article['url'])
        summary = summarize_article_with_gpt3(content)
        all_summaries.append({'title': article['title'], 'url': article['url'], 'summary': summary})
    return all_summaries

def extract_features(summaries):
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(summaries)
    return tfidf_matrix

def get_similarity_matrix(tfidf_matrix):
    return cosine_similarity(tfidf_matrix)

def filter_similar_and_taylor_related_articles(all_summaries, similarity_matrix, threshold=0.01):
    filtered_summaries = []
    for i, article in enumerate(all_summaries):
        if "Taylor Swift" not in article['summary']:
            continue  # Skip articles not mentioning Taylor Swift

        if any(similarity_matrix[i][j] > threshold for j in range(i)):
            continue  # Skip articles that are too similar to previous ones

        filtered_summaries.append(article)
        if len(filtered_summaries) >= 5:
            break  # Limit to 5 articles

    return filtered_summaries


current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
file_name = f"final_newsletter_{current_date_str}.html"

if __name__ == "__main__":
    results = scrape_google_news_with_firefox('taylor swift when:1d')

    # Process and summarize articles, and collect their summaries
    all_summarized_articles = process_and_summarize_articles(results)

    # Extract features for similarity analysis
    summaries_text = [article['summary'] for article in all_summarized_articles]
    tfidf_matrix = extract_features(summaries_text)

    # Calculate similarity and filter articles
    similarity_matrix = get_similarity_matrix(tfidf_matrix)
    unique_and_relevant_articles = filter_similar_and_taylor_related_articles(all_summarized_articles, similarity_matrix)

    # Generate HTML content
    html_content = ""
    for article in unique_and_relevant_articles:
        articles_html = f'<h2><a href="{article["url"]}" target="_blank">{article["title"]}</a></h2>\n<p>{article["summary"]}</p>\n'
        html_content += articles_html

    # Read the template HTML
    with open('/Users/petersweeney/Desktop/Coding/taylorNewsletter/taylorFormat', 'r') as file:
        template_html = file.read()

    # Replace the placeholder in the template with actual content
    final_newsletter_html = template_html.replace('<!-- Insert Articles Here -->', articles_html)
    final_newsletter_html = final_newsletter_html.replace('<!-- Insert Date Here -->', current_date_str)

    # Save the final newsletter HTML to a file
    with open(file_name, 'w') as file:
        file.write(final_newsletter_html)