import random
import time
from datetime import datetime
import os

from bs4 import BeautifulSoup
from selenium import webdriver

import pandas as pd
import json
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


class PytorchScraper:
    # The maximum number of topics you want to scape > 0
    max_topic = 50000
    count = 0
    driver = None  # Selenium webdriver object
    topic_dict = {}  # Dictionary of all topics and their attributes
    topic_data_frame = \
        pd.DataFrame(columns=[  # Pandas dataframe of all topic attributes
            'topic_title',
            'category',
            'author',
            'commenters',
            'leading_comment',
            'other_comments',
            'likes',
            'views'])

    def __init__(self, driver_path):
        # Set up webdriver
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')  # Ignore security certificates
        options.add_argument('--incognito')  # Use Chrome in Incognito mode
        options.add_argument('--headless')  # Run in background
        self.driver = webdriver.Chrome(
            executable_path=driver_path,
            options=options)

    def get_links_texts(self, link_class):
        link_elements = self.driver.find_elements_by_class_name(link_class)
        urls = []
        texts = []
        for link_element in link_elements:
            urls.append(link_element.get_attribute('href'))
            texts.append(link_element.text)
        return urls, texts

    def get_text(self, css_class):
        try:
            return self.driver.find_element_by_class_name(css_class).text.replace('\n', '').strip()
        except NoSuchElementException:
            return ""

    def get_texts(self, css_class):
        try:
            texts = self.driver.find_elements_by_class_name(css_class)
            return [text.text.replace('\n', '').strip() for text in texts]
        except NoSuchElementException:
            return []

    # Topic Attributes
    def get_topic_title(self):
        return self.get_text('fancy-title')

    def get_category_name(self):
        try:
            return self.driver.find_element_by_class_name('category-name').find_element_by_tag_name('span').text
        except:
            return ""

    def get_author_and_commenters(self):
        names = self.get_texts('names.trigger-user-card')
        return names[0], names[1:]

    def get_comments(self):
        comments = self.get_texts('cooked')
        return comments[0], comments[1:]

    def get_views(self):
        try:
            return self.driver.find_element_by_class_name('secondary.views').find_element_by_tag_name('span').text
        except:
            return "0"

    def get_likes(self):
        try:
            return self.driver.find_element_by_class_name('secondary.likes').find_element_by_tag_name('span').text
        except:
            return "0"

    def export_topic(self):
        # Get unique timestamp of the webscraping
        time_stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        # Save data in JSON and CSV files and store in the save folder as this program
        json_filename = 'Pytorch_Forum_' + time_stamp + '.json'
        csv_filename = 'Pytorch_Forum_' + time_stamp + '.csv'
        export_path = "pytorch"
        if not os.path.exists(export_path):
            os.makedirs(export_path)
        json_file_full_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), export_path, json_filename)
        csv_file_full_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), export_path, csv_filename)
        with open(json_file_full_path, 'w') as f:
            json.dump(self.topic_dict, f)
        self.topic_data_frame.to_csv(csv_file_full_path)

    def run(self, url):
        # Get main url
        self.driver.get(url)
        # Find all categories
        category_urls, category_texts = self.get_links_texts('category-title-link')
        # print(category_urls, "\n", category_texts)
        category_urls.reverse()
        category_texts.reverse()
        for i, category_url in enumerate(category_urls):
            print("" + category_url)
            if self.count > self.max_topic:
                break
            self.driver.get(category_url)
            topic_urls, topic_texts = self.get_links_texts('raw-topic-link')
            # print(topic_urls, "\n", topic_texts)
            for topic_url in topic_urls:
                if self.count >= self.max_topic:
                    break
                self.driver.get(topic_url)
                try:
                    WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, 'ember50')))
                except Exception:
                    pass
                topic_title = self.get_topic_title()
                category = category_texts[i]
                view = self.get_views()
                likes = self.get_likes()
                author, commenters = self.get_author_and_commenters()
                leading_comment, other_comments = self.get_comments()
                # Create attribute dictionary for topic
                attribute_dict = {
                    'topic_title': topic_title,
                    'category': category,
                    'author': author,
                    'commenters': commenters,
                    'leading_comment': leading_comment,
                    'other_comments': other_comments,
                    'likes': likes,
                    'views': view}
                # Print attributes
                print("\nTopic: " + topic_title)
                print("- Category: ", category)
                print("- Author: ", author)
                print("- Commenters: ", commenters)
                print("- Leading: ", leading_comment)
                print("- Comments: ", other_comments)
                print("- Likes: ", likes)
                print("- View: ", view)
                # Add the new entry to the topic dictionary and Pandas dataframe
                self.topic_dict[topic_title] = attribute_dict
                self.topic_data_frame = self.topic_data_frame.append(attribute_dict, ignore_index=True)
                self.count += 1
        self.export_topic()


if __name__ == '__main__':
    # Local path to web driver
    # Window
    # web_driver_path = ".\drivers\webdriver\chromedriver.exe"

    # Mac
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    web_driver_path = os.path.join(PROJECT_ROOT, "drivers/chromedriver")
    # web_driver_path = ".\drivers\webdriver\chromedriver"

    # Pytorch base URL
    BASE_URL = 'https://discuss.pytorch.org/'
    # Scraper
    pytorch_scraper = PytorchScraper(web_driver_path)
    # Run Scraper and save data
    pytorch_scraper.run(BASE_URL)
