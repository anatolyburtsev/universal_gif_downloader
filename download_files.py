#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'onotole'


from bs4 import BeautifulSoup
import time
import urllib2
#from urllib import urlretrieve
from urlparse import urljoin
from socket import timeout
import sys
import re
from urllib import urlretrieve
import os.path
import datetime
import logging
import config
import signal

logging_format = u'%(filename)s[line:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s'
logging_level = logging.DEBUG
logging_filename = u"download_gifs.log"

logging.basicConfig(format=logging_format, level=logging_level, filename=logging_filename)


class TimeoutError(Exception):
    def __init__(self, value="Timed Out"):
        self.value = value

    def __str__(self):
        return repr(self.value)


def timeout(seconds_before_timeout):
    def decorate(f):
        def handler(signum, frame):
            raise TimeoutError

        def new_f(*args, **kwargs):
            old = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds_before_timeout)
            try:
                result = f(*args, **kwargs)
            finally:
                signal.signal(signal.SIGALRM, old)
            signal.alarm(0)
            return result
        new_f.func_name = f.func_name
        return new_f
    return decorate


def loadHelper(uri):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/6.0')]
    try:
        thing = opener.open(uri, None, 10)
        soup = BeautifulSoup(thing.read(), "lxml")
        if not (soup is None):
            return soup
        else:
            print ("soup is None")
            loadHelper(uri)
    except (timeout, urllib2.HTTPError, urllib2.URLError) as error:
        sys.stdout.write("{} encountered, hold on, bro".format(error))
        sys.stdout.flush()
        time.sleep(30)
        loadHelper(uri)


def extract_posts_from_page(page_number):
    assert type(page_number) == int
    logging.info("start page number:" + str(page_number))
    if page_number == 0:
        return []
    elif page_number == 1:
        url_to_page = config.initial_page
    else:
        url_to_page = config.initial_page + config.page_additional + str(page_number)

    page_with_posts = loadHelper(url_to_page)
    urls_to_posts = []
    for i in page_with_posts.find_all(config.extrp_1, attrs={config.extrp_2: config.extrp_3}):
        urls_to_posts.append(urljoin(config.post_prefix, i.find('a').attrs["href"]))
    return urls_to_posts


def extract_files_from_post(url_to_post):
    assert type(url_to_post) == str
    logging.debug('start processing post: ' + url_to_post)
    page_with_post = loadHelper(url_to_post)
    files_list = []
    files_block = page_with_post.find(config.extrf_1, attrs={config.extrf_2: config.extrf_3})
    for file_data in files_block.find_all("img"):
        files_list.append(file_data.attrs["src"])
    return files_list

@timeout(config.file_downloading_limit)
def save_file(url_opener, url_to_file):
    assert type(url_to_file) == str
    start_time = time.time()
    if not url_to_file.startswith("http"):
        url_to_file = urljoin(config.file_prefix, url_to_file)
    dir_to_save = config.files_dir
    filename = "".join(re.findall(r'\w+', url_to_file))
    filename += '.gif'
    if not os.path.exists(dir_to_save):
        os.mkdir(dir_to_save)
    path_to_file = os.path.join(dir_to_save, filename)
    logging.debug('start saving: ' + url_to_file + ' to ' + path_to_file)

    download_file = url_opener.open(url_to_file)
    local_file = open(path_to_file, 'w')
    while 1:
        packet = download_file.read()
        if not packet:
            break
        local_file.write(packet)
    download_file.close()
    local_file.close()
    logging.debug('saved in sec: ' + str(time.time() - start_time))
    return True


def dump_gifs(start_page=config.start_page, max_page=config.max_page):
    assert type(max_page) == int
    for page_number in range(start_page, max_page + 1):
        for url_to_post in extract_posts_from_page(page_number):
            opener = urllib2.build_opener()
            opener.addheaders = [('Referer', url_to_post)]
            for url_to_gif in extract_files_from_post(url_to_post):
                try:
                    save_file(opener, url_to_gif)
                except TimeoutError:
                    logging.error("saving file killed. link to big gif: " + url_to_gif)


if __name__ == "__main__":
    dump_gifs(1)


#save_file("http://media.ifun.ru/4/q/4q01etnk.gif")
# for i in extract_files_from_post_ifun("http://ifun.ru/view/292051"):
#     print i
    #save_file(i)
#print extract_posts_from_page(1)
    #extract_files_from_post('http://ifun.ru/view/292051')