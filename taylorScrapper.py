import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time
import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from openai import OpenAI
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# Assuming 'app', 'db', and 'Subscriber' are properly defined in 'app.py'
from app import app, db, Subscriber

# Initialize OpenAI client with environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

EMAIL_FROM = 'swiftie@taylortimes.news'
EMAIL_SUBJECT = 'Taylor Times Newsletter'

# Initialize WebDriver outside the loop
def init_webdriver():
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    service = Service('/Users/petersweeney/Downloads/geckodriver')
    return webdriver.Firefox(service=service, options=firefox_options)

def scrape_google_news_with_firefox(driver, query):
    articles = []
    driver.get('https://news.google.com/stories/CAAqNggKIjBDQklTSGpvSmMzUnZjbmt0TXpZd1NoRUtEd2k1cEpiUUNoRmFPYmh2RFEyVFNpZ0FQAQ?hl=en-US&gl=US&ceid=US%3Aen&so=1')
    time.sleep(5)  # Adjust sleep time as needed

    article_elements = driver.find_elements(By.CSS_SELECTOR, 'a.DY5T1d.RZIKme')
    for element in article_elements[:10]:  # Limit to first 10 articles
        url = element.get_attribute('href')
        title = element.text
        articles.append({'title': title, 'url': url})
    return articles

def fetch_subscribers():
    with app.app_context():
        subscriber_records = Subscriber.query.all()
        return [subscriber.email for subscriber in subscriber_records]

def send_email(recipients, html_content):
    sg_api_key = os.getenv('SENDGRID_API_KEY')
    if not sg_api_key:
        raise ValueError("SendGrid API key not found in environment variables.")
    sg = SendGridAPIClient(sg_api_key)

    for recipient in recipients:
        message = Mail(from_email=EMAIL_FROM, to_emails=recipient, subject=EMAIL_SUBJECT, html_content=html_content)
        sg.send(message)

def fetch_article_content_with_selenium(driver, url):
    driver.get(url)
    time.sleep(5)  # Wait for dynamic content to load
    try:
        paragraphs = driver.find_elements(By.TAG_NAME, 'p')
        return ' '.join([p.text for p in paragraphs])
    except Exception as e:
        print(f"Error fetching article: {url}, Error: {e}")
        return None

def summarize_article_with_gpt3(article_text):
    response = client.completions.create(model="gpt-3.5-turbo-instruct", prompt=f"Write a short engaging summary of this article, with a tone fit for millennials but please do not use the word millenial: {article_text}", max_tokens=150)
    return response.choices[0].text.strip()

def process_and_summarize_articles(driver, results):
    html_content = ""
    articles_included = 0
    included_articles_content = []  # Store contents of included articles for similarity check
    for article in results:
        content = fetch_article_content_with_selenium(driver, article['url'])
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

if __name__ == "__main__":
    print("Script started.")
    driver = init_webdriver()
    try:
        results = scrape_google_news_with_firefox(driver, 'Taylor Swift')
        if results:
            articles_html = process_and_summarize_articles(driver, results)
            if articles_html:
                subscribers = fetch_subscribers()
                if subscribers:
                    send_email(subscribers, articles_html)
                    print("Emails sent.")
                else:
                    print("No subscribers found. No emails sent.")
            else:
                print("No articles processed. Exiting script.")
        else:
            print("No articles found. Exiting script.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
        print("WebDriver quit. Script completed.")
