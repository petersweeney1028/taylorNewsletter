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
    for article in articles[:4]:  # Limit to first 4 articles
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
        response = client.completions.create(model="text-davinci-003",  
        prompt="Write a punchy, engaging summary suitable for a newsletter: \n\n" + article_text,
        max_tokens=150)
        return response.choices[0].text.strip()
    except Exception as e:
        return "Error in summarization: " + str(e)

def process_and_summarize_articles(results):
    for article in results:
        content = fetch_article_content(article['url'])
        summary = summarize_article_with_gpt3(content)
        print(f"Title: {article['title']}\nSummary: {summary}\n")


# Function to run the scraper with a specified query
def run_scraper(query):
    return scrape_google_news_with_firefox(query)

scraped_articles = run_scraper('taylor swift when:1d')
process_and_summarize_articles(scraped_articles)


