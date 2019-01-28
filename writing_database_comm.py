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
from writing_database import download_comments, getting_comment_data

def store_comments():
    client = MongoClient()
    db = client["guardian"] #This is the name of the database
    urls = db["urls"] # this is the table in that database
    comment_tab = db["comment_tab"]
    i = 0

    cursor = urls.find({}, no_cursor_timeout= True)
    all_urls = [d['url'] for d  in db.urls.find()]
    comment_url_set =  set([u['url'] for u in db.comment_tab.find({'url':{'$exists': 1}})])
    cursor.close()

    skip_count = len(comment_url_set)


    for u in all_urls:
        if u not in comment_url_set:
            # print ('URL = ', u)
            seconds = random.randint(5, 39)
            time.sleep(seconds)
            try:
                url = str(document['url'])
                id_n = document['id']

                print ('URL = ', url)

                soup = download_comments(url)
                comment_text_list, comment_id_list, author_id_list, auth_name_lst, upvotes_count_list = getting_comment_data(soup)
            ##      comment_text_list, comment_id_list, author_id_list, auth_name_lst, upvotes_count_list

                insert_dict = {'id' : id_n, 'url': url, 'comment_ids' : comment_id_list,
                                'comment_text' : comment_text_list,
                                'author_ids' : author_id_list, 'author_name' : auth_name_lst,
                                'upvotes' : upvotes_count_list}
                res = comment_tab.insert_one(insert_dict)
                i += 1
                if i % 25 == 0:
                    print ("Message : {:d} documents downloaded.".format(i))
                    print ("\n")

            except :
                pass
            skip_count += 1
            if i % 25 == 0:
                    print ("Message : {:d} documents downloaded.".format(i))
                    print ("\n")

    return


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


if __name__ == '__main__':

    client = MongoClient()
    db = client["guardian"] #This is the name of the database
    urls = db["urls"] # this is the table in that database
    comment_tab = db["comment_tab"]



    store_comments()
