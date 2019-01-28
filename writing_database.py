import requests
from pymongo import MongoClient
import re
import time
from bs4 import BeautifulSoup
import random
# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
import urllib
import sys


def get_urls(reset = False):
    years = ["2018"]
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    dates = [str(n) for n in range(1,30)]


    # years = ["2017"]
    # months = ["jan"]
    # dates = [str(31)]


    # count of number of links
    i = 0

    # Initiating mongoDB. Using pymongo to connect the database
    client = MongoClient()
    db = client["guardian"] #This is the name of the database
    urls = db["urls"] # this is the table in that database
    data = db["data"]
    comment_tab = db["comment_tab"]

    if reset:
        result = db.urls.delete_many({}) # A fresh start to the DB table -> removing all entries
        result = db.data.delete_many({})
    all_links = []

    for year in years:
        for month in months:
            dates = [str(n) for n in range(1,30)]
            if month == 'feb':
                dates = [str(n) for n in range(1,28)]
            for date in dates:
                root_url = "https://www.theguardian.com/commentisfree/" + year  + "/" + month + "/" + date

                # This one contains all the URLs. Soup extracts those.
                list_of_urls = requests.get(root_url).text
                soup = BeautifulSoup(list_of_urls, "html.parser")

                # the .findAll method from re finds the _content_ that has
                # html tag - 'a', attribute - 'href' and
                # the pattern that begins with the root_url variable
                for link in soup.findAll('a', attrs={'href': re.compile(root_url)}):
                    all_links.append(link.get('href'))

    all_links = set(all_links)
    for n, link in enumerate(all_links):
        # urls is the name of the mongo DataBase. insert_one is the method
        #if n < 2:
        urls.insert_one({"id" : i, "url" : link})
    #             print link
        i += 1
    print ("Total number of links stored is ", i)

    return

def download_comments(guardianLink):
    '''
    This function downloads the comments, along with title, topic of the original thread
    comment_id, no_upvotes, no_replies, comment_author, comment_author_id, etc
    Returns BeautifulSoup; need more extraction from the soup for the above-mentioned
    parameters

    '''

    #Figuring out the PageId
    pageResponse = urllib2.urlopen(guardianLink)
    commentsMatch = re.search(r'/p/(.*?)"', pageResponse.read(), re.M|re.I)
    # print "Comments Match = ", commentsMatch()
    if commentsMatch:
        pageId = commentsMatch.group(1)
        print ('[+] pageId has been retrieved ('+pageId+')')
    else:
        sys.exit('[-] Could not retrieve pageId!')

    #Retrieving comments
    downloadCount = 1
    downloadError = 0

    text = ''

    while downloadError == 0:
        try:
            response = urllib2.urlopen('http://www.theguardian.com/discussion/p/' + pageId
                                       + '?page=' + str(downloadCount))
            html = response.read()
            length = len(text)
            text += html
            downloadCount = downloadCount + 1

        except:
            downloadError = 1

    return BeautifulSoup(text, 'html.parser')


# ## To extract data from soup
#
# #### Returns a list of lists - comment_od, comment_text, author_id, author_name, number_of_upvotes





# ### To extract topic(s) and text of an article



def article_topics_title(url):
    '''
    Given a URL, this function returns topics and contents of the article

    '''

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    topic_list = [topic.attrs['data-link-name'][9:] for topic in soup.findAll("a", {"class" : "submeta__link"})
        if 'data-link-name' in topic.attrs and 'keyword: ' in topic.attrs['data-link-name']]

    for title in soup.find("h1", {"class" : "content__headline"}):
        title = str(title.strip().encode('utf-8'))


    for tag in soup.find_all('svg'):
        tag.decompose()
    for tag in soup.find_all('figure'):
        tag.decompose()
    for tag in soup.find_all('aside'):
        tag.decompose()
    for tag in soup.find_all('span'):
        tag.decompose()

    article = [str(s) for s in soup.find("div", {"class" : "content__article-body from-content-api js-article__body"})]
    article = ' '.join(t.lower() for t in article)
    article = BeautifulSoup(article).get_text().replace("\n", " ")


    return topic_list, article, title



def download_articles():
    client = MongoClient()
    db = client["guardian"] #This is the name of the database
    urls = db["urls"] # this is the table in that database
    data = db["data"]

    i = 0

    cursor = urls.find({}, no_cursor_timeout= True)
    all_urls = [d['url'] for d  in db.urls.find()]
    data_url_set =  set([u['url'] for u in db.data.find({'url':{'$exists': 1}})])
    cursor.close()

    skip_count = len(data_url_set)

    for u in all_urls:
        if u not in data_url_set:
            # print ('URL = ', u)
            seconds = random.randint(5, 39)
            time.sleep(seconds)
            try:
                topic_list, article, title = article_topics_title(u)
                print ("Title of the article is: ", title)

                res = data.insert_one({'id' : skip_count, 'url' : u, 'article' : article,
                           'title' : title, 'topic_list' : topic_list})
                i += 1
                if i % 25 == 0:
                    print ("Message : {:d} documents downloaded.".format(i))
                    print ("\n")
            except :
                pass
            skip_count += 1

    return

def store_comments():
    client = MongoClient()
    db = client["guardian"] #This is the name of the database
    urls = db["urls"] # this is the table in that database
    comment_tab = db["comment_tab"]
    i = 0

    cursor = urls.find({}, no_cursor_timeout= True)
    for document in cursor:
        seconds = random.randint(5, 39)
        time.sleep(seconds)
        url = str(document['url'])
        id_n = document['_id']

        print ('URL = ', url)

        soup = download_comments(url)
        comment_text_list, comment_id_list, author_id_list, auth_name_lst, upvotes_count_list = getting_comment_data(soup)
    ##      comment_text_list, comment_id_list, author_id_list, auth_name_lst, upvotes_count_list
        res = comment_tab.insert_one({'id' : id_n, 'url': url, 'comment_ids' : comment_id_list,
                        'comment_text' : comment_text_list,
                        'author_ids' : author_id_list, 'author_name' : auth_name_lst,
                        'upvotes' : upvotes_count_list})


        i += 1
        if i % 25 == 0:
            print ("Message : {:d} documents downloaded.".format(i))
            print ("\n")

    return

if __name__ == "__main__":
    # get_urls(reset = True)
    # client = MongoClient()
    # db = client["guardian"] #This is the name of the database
    # result = db.data.delete_many({})

    # get_urls(reset = True)
    download_articles()
