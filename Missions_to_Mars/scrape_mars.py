#Import dependencies
import pandas as pd
import pymongo
import os
from bs4 import BeautifulSoup as bs
from splinter import Browser
import traceback
from time import sleep
from flask import Flask, render_template, redirect, Markup

#Create a connection to MongoDB
conn = 'mongodb://localhost:27017'

#Method for scraping mars data
def scrape():
    #Executable path for chromedriver
    path = os.path.join('..', 'ChromeDriver', 'chromedriver.exe')
    executable_path = {'executable_path':path}

    #Creating Browser object
    browser = Browser('chrome', **executable_path, headless=True)

    #Dictionary with all the data
    mars_data = {}

    #NASA Mars new
    #URL to visit
    news_url = 'https://mars.nasa.gov/news/'
    browser.visit(news_url)

    #Getting the html of the url visited and parse it with BeautifulSoup
    html = browser.html
    soup = bs(html, 'html.parser')

    #Get the latest News title and paragraph from website
    sleep(1) #Wait finish loading
    result = soup.find('div', class_='list_text')

    #scrape the title
    title_container = result.find('div', class_='content_title')
    news_title = title_container.find('a').text

    #scrape the paragraph
    news_p = result.find('div', class_='article_teaser_body').text

    mars_data['news_title'] = news_title
    mars_data['news_p'] = news_p

    #Mars space image
    #URL to visit (image)
    ftImg_url = 'https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars'
    base_url = 'https://www.jpl.nasa.gov'
    browser.visit(ftImg_url)
    #Navigate through the website to get the featured image full size url.
    try:
        browser.click_link_by_partial_text('FULL IMAGE')
        sleep(1) #Wait finish loading

        #src attribute of img element to full size image
        html = browser.html
        soup = bs(html, 'html.parser')
        result = soup.find('img', class_='fancybox-image')
        fullSize_url = result['src']

        #Formatting image url
        fullSize_url = base_url + fullSize_url
        print(fullSize_url)

    except:
        traceback.print_exc()

    mars_data['ft_img'] = fullSize_url

    #Mars Weather
    #URL to visit (latest tweet)
    tweet_url = 'https://twitter.com/marswxreport?lang=en'
    browser.visit(tweet_url)
    #Navigate through Mars weather twitter and get the latest weather
    try:
        sleep(1) #Wait finish loading
        html = browser.html
        soup = bs(html, 'html.parser')
        result = soup.find('article')
        mars_weather = result.find('div', attrs={'lang':True}).text
        print(mars_weather)
        
    except:
        print("Exception throw")
        traceback.print_exc()

    mars_data['weather'] = mars_weather

    #Mars Facts
    #URL to visit (mars facts)
    facts_url = 'https://space-facts.com/mars'
    facts_df = pd.read_html(facts_url)

    #Cleaning and formatting pandas dataframe to a html table
    table_string = facts_df[0].to_html(header=False, index=False)

    mars_data['facts'] = table_string

    #Mars Hemisphere images
    #URL to visit
    hemispheres_url = 'https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars'
    browser.visit(hemispheres_url)

    img_list = []
    try:
        sleep(1)
        html = browser.html
        soup = bs(html, 'html.parser')
        
        #Image title
        results = soup.find_all('div', class_="item")
        for result in results:
            title = result.find('h3')
            
            #Full size img url
            browser.click_link_by_partial_text(title.text)
            html = browser.html
            soup = bs(html, 'html.parser')
            url = soup.find('a', string='Sample')
            url = url['href']      
            browser.back()
            img_dict = {'title':title.text, 'url':url}
            img_list.append(img_dict)
            
    except:
        print("Exception throw")
        traceback.print_exc()

    for x in img_list:
        print(x)

    mars_data['hemispheres'] = img_list

    return mars_data
    

app = Flask(__name__)

@app.route('/')
def home():
    client = pymongo.MongoClient(conn)
    db = client.scraping_db
    mars = db.mars

    data = mars.find_one()
    
    return render_template('index.html', mars_data=data)

@app.route('/scrape')
def scrapeInfo():
    client = pymongo.MongoClient(conn)
    db = client.scraping_db
    mars = db.mars

    new_data = scrape()
    mars.update({}, new_data)

    return redirect("/", code=302)


if __name__ == "__main__":
    app.run(debug=True)