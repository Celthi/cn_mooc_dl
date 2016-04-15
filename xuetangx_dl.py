# -*- coding: utf-8 -*-

from __future__ import print_function

import re
import sys
import os
import requests
from bs4 import BeautifulSoup
import json
from multiprocessing.pool import Pool
import threading

from utils import *  # This usage is not suggested


test_site = ("http://www.xuetangx.com/courses/TsinghuaX/30240243X/2015_T1/courseware"
             "/d2b12c602c4b420b8bcc83003a035370/")

args = parse_args()

cookies_file = args.cookiesfile
course_link = args.course_url[0]
path = args.path
overwrite = args.overwrite
regex = r'(?:https?://)?(?P<site>[^/]+)/(?P<baseurl>[^/]+)/(?P<institution>[^/]+)/(?P<coursename>[^/]+)/(?P<offering>[^/]+).*'
m = re.match(regex, course_link)  

if m is None:
    print('The URL provided is not valid for xuetangx.')
    sys.exit(0)

homepage = 'https://' + m.group('site')
coursename = m.group('coursename')
cookies_file = args.cookiesfile
course_link = args.course_url[0]
path = args.path
overwrite = args.overwrite
session = requests.session()
def download_thread(syllabus):
    retry_list = []
    for (week_num, (week_name, week_content)) in enumerate(syllabus):
        if not week_name:
            break
        week_name = '%02d %s' % (week_num+1, clean_filename(week_name))
        for (lesson_num, (lesson_name, lesson_content)) in enumerate(week_content):

            lesson_name = '%02d %s' % (lesson_num+1, clean_filename(lesson_name))
            dir = os.path.join(path, coursename, week_name, lesson_name)
            if not os.path.exists(dir):
                mkdir_p(dir)

            for (lec_num, (lec_title, lec_video_url, lec_subtitle)) in enumerate(lesson_content):
                lec_title = '%02d %s' %(lec_num+1, clean_filename(lec_title))
                vfilename = os.path.join(dir, lec_title)
                print(vfilename + '.mp4')
                try:
                    resume_download_file(session, lec_video_url, vfilename + '.mp4', overwrite)
                except Exception as e:
                    print(e)
                    print('Error, add it to retry list')
                    retry_list.append((lec_video_url, vfilename + '.mp4'))

                for sub_url in lec_subtitle:
                    sfilename = vfilename
                    print(sfilename + '.srt')
                    if not os.path.exists(sfilename + '.srt') or overwrite:
                        try:
                            download_file(session, sub_url, sfilename + '.srt')
                        except Exception as e:
                            print(e)
                            print('Error, add it to retry list')
                            retry_list.append((sub_url, sfilename + '.srt'))
                            continue
                    else:
                        print('Already downloaded.')

    retry_times = 0
    while len(retry_list) != 0 and retry_times < 3:
        print('%d items should be retried, retrying...' % len(retry_list))
        retry_times += 1
        for (url, filename) in retry_list:
            try:
                print(url)
                print(filename)
                resume_download_file(session, url, filename, overwrite)
            except Exception as e:
                print(e)
                print('Error, add it to retry list')
                continue

            retry_list.remove((url, filename))
    if len(retry_list) != 0:
        print('%d items failed, please check it' % len(retry_list))
    else:
        print('All done.')

def main():


    session = requests.Session()

    with open(cookies_file) as f:
        cookies = json.loads(f.read())

    cj = requests.cookies.RequestsCookieJar()
    for cookie_dict in cookies:
        for item in cookie_dict:
            if cookie_dict[item] == True:
                cookie_dict[item] = 'true'
            if cookie_dict[item] == False:
                cookie_dict[item] = 'false'
            cookie_dict[item] = str(cookie_dict[item])
        requests.utils.add_dict_to_cookiejar(cj, {cookie_dict['name']: cookie_dict['value']})
    session.cookies.update(cj)

    c = [c.name + '=' + c.value for c in cj if c.domain == '.xuetangx.com']
    cookies_values = '; '.join(c)
    session.cookie_values = cookies_values

    print('Login done...')

    print('Parsing...', end="")
    r = session.get(course_link)
    courseware = r.content
    soup = BeautifulSoup(courseware)
    data = soup.find('nav', {'aria-label': '课程导航'})
    if data is None:
        print("fail to set cookie")
        sys.exit(0)
    syllabus = []

    for week in data.find_all('div', {'class': 'chapter'}):
        week_name = clean_filename(week.h3.a.string)
        print(week_name)
        week_content = []
        for lesson in week.ul.find_all('a'):
            lesson_name = lesson.p.getText()
            print(lesson_name)
            lesson_url = homepage + lesson['href']
            r = session.get(lesson_url)
            lesson_page = r.content
            lesson_soup = BeautifulSoup(lesson_page)

            lec_map = {}
            tab_lists = lesson_soup.find_all('a', {'role': 'tab'})
            for tab in tab_lists:
                lec_map[tab.get('id')] = tab.get('title')
            lesson_content = []
            text = lesson_soup.body.findAll(text=re.compile(r'data-ccsource=\'(?P<source>[^\']+)'))
            if not text:
                continue

            pattern = re.compile(r'data-ccsource=\'(?P<source>[^\']+)')
            sub_pattern = re.compile(r'href=\"(?P<sub_url>[^\"]+)')

            m = pattern.search(text[0].string)
            sub_m = sub_pattern.search(text[0].string)
            #####
            # 分析网址的数据保留
            # 6.1 -- D52DDC93AC16EC379C33DC5901307461
            # http://www.xuetangx.com/courses/TsinghuaX/30240243X/2015_T1/courseware/5fc34545f41b41ec96243d4ead29ac6f/971c652c9736442380c616036f339027/
            # get_vid_url = '...source'+ data-ccsource
            ########################
            get_vid_url = 'https://www.xuetangx.com/videoid2source/' + m.group('source')
            r = session.get(get_vid_url)
            data = r.content
            resp = json.loads(data)
            if resp['sources']:
                if resp['sources']['quality20']:
                    tab_video_link = resp['sources']['quality20'][0]
                elif resp['sources']['quality10']:
                    tab_video_link = resp['sources']['quality10'][0]
                else:
                    print('\nATTENTION: Video Missed for \"%s\"' % lec_map[tab.get('aria-labelledby')])
                    continue
            else:
                print('\nATTENTION: Faile to git video for \"%s\"' % lec_map[tab.get('aria-labelledby')])
                continue

            tab_title = lesson_name
            subs_url = homepage + sub_m.group('sub_url')
            tab_subs_url = []
            tab_subs_url.append(subs_url)

            lesson_content.append((tab_title, tab_video_link, tab_subs_url))

            # exclude lessons without video
            if lesson_content:
                week_content.append((lesson_name, lesson_content))

            print('.', end="")
        if week_content:
            syllabus.append((week_name, week_content))

    with open("syllabus.txt", 'w') as syllabus_save:
        json.dump(syllabus, syllabus_save)
    print("Done.")

    print("Downloading...")

def waitForThreadRunningCompleted(maxThread= -1):
    count = maxThread
    #while threading.threadID




if __name__ == '__main__':
    main()
    with open('syllabus.txt', 'r') as f:
        syllabus = json.loads(f.read())

    syllabus_un = syllabus
    for chapter in syllabus_un:
        ss = [chapter]
        t = threading.Thread(target=download_thread, kwargs={'syllabus': ss})
        t.start()
