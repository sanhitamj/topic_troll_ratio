import requests
from pymongo import MongoClient
import re
import time
from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
import urllib2
import sys


def get_urls():
    # years = ["2015", "2016", "2017"]
    # months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    # dates = [str(n) for n in xrange(1,28)]


    years = ["2017"]
    months = ["jan"]
    dates = [str(31)]


    # count of number of links
    i = 0

    # Initiating mongoDB. Using pymongo to connect the database
    client = MongoClient()
    db = client["guardian"] #This is the name of the database
    urls = db["urls"] # this is the table in that database

    result = db.urls.delete_many({}) # A fresh start to the DB table -> removing all entries
    all_links = []

    for year in years:
        for month in months:
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
    print "Total number of links stored is ", i

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
        print '[+] pageId has been retrieved ('+pageId+')'
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



def getting_comment_data(soup):
    '''
    This function takes in the soup of comments. Returns a list of list.
    Each element in the list is a list of -
    comment_id, comment, author_id, author, number_of_upvotes

    '''

    auth_name_lst = []
    comm_id_lst = []
    auth_id_lst = []
    for lis in soup.find_all('li'):
        if 'data-comment-author-id' in (lis.attrs) and 'data-comment-id' in (lis.attrs)and 'data-comment-author' in (lis.attrs):
            auth_name_lst.append(lis.attrs['data-comment-author'].encode('utf-8').replace("  ", " "))
            auth_id_lst.append(int(lis.attrs['data-comment-author-id']))
            comm_id_lst.append(int(lis.attrs['data-comment-id']))

    comments_text = soup.findAll("div", { "class" : "d-comment__body" })
    recommends = soup.findAll("span", {"class" : "d-comment__recommend-count--old"})
    users = soup.findAll("span", {"itemprop" : "givenName"})

    comment_data_list = []
    comment_text_list = []
    comment_id_list = []
    author_id_list = []
    author_name_list = []
    upvotes_count_list = []

    i = 0
    j = 0
    for comment_text, upvotes, user, auth_name, auth_id, comment_id in zip(comments_text, recommends, users, auth_name_lst, auth_id_lst, comm_id_lst):
        i += 1
        if 'comment was removed by a moderator ' not in comment_text.text:
            j += 1
#             This is the count of comments not removed by the moderator


#             if auth_name.strip() != user.text.encode('utf-8').strip():
#                 print "something is broken for -"+ auth_name.strip()+ "-"+ user.text.encode('utf-8').strip()
#             else :
            if not upvotes.txt:
                upvote = 0
            else :
                upvote = int(upvotes.txt)
            comment_text_list.append(comment_text.text)
            comment_id_list.append(comment_id)
            author_id_list.append(auth_id)
            author_name_list.append(auth_name)
            upvotes_count_list.append(upvote)

    return comment_text_list, comment_id_list, author_id_list, auth_name_lst, upvotes_count_list


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


    return topic_list, article, title



def real_download():
    client = MongoClient()
    db = client["guardian"] #This is the name of the database
    urls = db["urls"] # this is the table in that database

    cursor = urls.find({})
    for document in cursor:
        url = str(document['url'])
        id_n = document['_id']
        print "Working on this link", url


        soup = download_comments(url)
    #     #     comment_text_list, comment_id_list, author_id_list, auth_name_lst, upvotes_count_list
        comment_text_list, comment_id_list, author_id_list, auth_name_lst, upvotes_count_list = getting_comment_data(soup)

        topics_list, article, title = article_topics_title(url)
        print "Title of the article is: ", title

        urls.update_one({'url': url},
                        {"$set": {'title': title, 'article' : article, 'topics_list': topics_list,
                                'comment_ids' : comment_id_list, 'comment_text' : comment_text_list,
                                'author_ids' : author_id_list, 'author_name' : auth_name_lst,
                                'upvotes' : upvotes_count_list}}, upsert=True)

    return

if __name__ == "__main__":
    get_urls()
    real_download()
