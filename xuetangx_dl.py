# -*- coding: utf-8 -*-

from __future__ import print_function

import pdb
import json
import logging
import re
import sys
import os
import requests
from bs4 import BeautifulSoup
import HTMLParser
import StringIO
import cookielib
import json

from utils import *

test_site = "http://www.xuetangx.com/courses/TsinghuaX/30240243X/2015_T1/courseware/d2b12c602c4b420b8bcc83003a035370/"
def main():

    args = parse_args()

    if args.username is None:
        print ('No username specified.')
        sys.exit(1)
    if args.password is None:
        print ('No password specified.')
        sys.exit(1)

    user_email = args.username
    user_pswd = args.password
    cookies_file = args.cookiesfile
    course_link = args.course_url[0]
    path = args.path
    overwrite = args.overwrite

    regex = r'(?:https?://)?(?P<site>[^/]+)/(?P<baseurl>[^/]+)/(?P<institution>[^/]+)/(?P<coursename>[^/]+)/(?P<offering>[^/]+).*'
    m = re.match(regex, course_link)  

    if m is None:
        print ('The URL provided is not valid for xuetangx.')
        sys.exit(0)

    if m.group('site') in ['www.xuetangx.com']:
        login_suffix = 'login_ajax'
    else:
        print ('The URL provided is not valid for xuetangx.')
        sys.exit(0)

    homepage = 'https://' + m.group('site')
    # print(homepage)
    login_url = homepage + '/' + login_suffix
    dashboard = homepage + '/dashboard'
    coursename = m.group('coursename')
    course_id = '%s/%s/%s' % (m.group('institution'),
                              m.group('coursename'),
                              m.group('offering'))

    session = requests.Session()
    session.get(homepage)
    csrftoken = session.cookies['csrftoken']
    # print(csrftoken)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Referer': homepage,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrftoken,
    }

    post_data = {
                'email': user_email,
                'password':user_pswd 
                }
    # session.headers.update(headers)

    def load_cookies_file(cookies_file):
        '''
        '''
        cookies = StringIO.StringIO()
        cookies.write('# Netscape HTTP Cookie File')
        cookies.write(open(cookies_file, 'rU').read())
        cookies.flush()
        cookies.seek(0)
        
        return cookies
    def get_cookie_jar(cookies_file):
        cj = cookielib.MozillaCookieJar()
        # cj = cookielib.LWPCookieJar(cookies_file)
        # cj.load(ignore_discard=True)
        # cookies = load_cookies_file(cookies_file)
        # cj._really_load(cookies, 'StringIO.cookies', False, False)
        
        return cj

    def find_cookies_for_class(cookies_file):

        def cookies_filter(c):
            return c.domain == ".xuetangx.com" or c.domain == 'www.xuetangx.com'

        cj = get_cookie_jar(cookies_file)
        new_cj = requests.cookies.RequestsCookieJar()
        for c in filter(cookies_filter, cj):
            new_cj.set_cookie(c)
        return new_cj

    # cookies = find_cookies_for_class(cookies_file)
     # cookies = get_cookie_jar(cookies_file)
    with open(cookies_file) as f:
        cookies = json.loads(f.read())

    cj = requests.cookies.RequestsCookieJar()
    # for cookie_dict in cookies:
    # cookie_dict = cookies[1]
    for cookie_dict in cookies:
        for item in cookie_dict:
            if cookie_dict[item] == True:
                cookie_dict[item] = 'true'
            if cookie_dict[item] == False:
                cookie_dict[item] = 'false'
            cookie_dict[item] = str(cookie_dict[item])
        requests.utils.add_dict_to_cookiejar(cj,{cookie_dict['name']:cookie_dict['value']})
    # print(requests.utils.dict_from_cookiejar(cj))
    # print('------')
    session.cookies.update(cj)

    c = [c.name + '=' + c.value for c in cj if c.domain == '.xuetangx.com']
    cookies_values = '; '.join(c)
    # session.cookie_values = cookies_values
    # print(cookies_values)
    session.cookie_values = cookies_values
    # session.cookies = cj
    # session.cookies = cookies
    
    # new_cj.set_cookies(c)
    # r = session.post(login_url, data=post_data)
    # data = r.content.decode('utf-8')
    # resp = json.loads(data)

    # if not resp.get('success', False):
    #     print('Problems suppling credentials to xuetangx.')
    #     exit(2)

    print ('Login done...')
    # print(session.cookies)

    print ('Parsing...', end="")
    course_urls = []
    new_url = "%s/courses/%s/courseware" % (homepage, course_id)
    course_urls.append(new_url)
    url = course_urls[0]
    url2 = 'http://www.xuetangx.com/courses/TsinghuaX/30240243X/2015_T1/courseware/14def9edc58e4936abd418333f899836/'
    url3 = 'http://www.xuetangx.com/courses/TsinghuaX/30240243X/2015_T1/courseware/5fc34545f41b41ec96243d4ead29ac6f/971c652c9736442380c616036f339027/'
    r = session.get(url2)
    # print(r.status_code)
    print(r.history)
    courseware = r.content
    with open('file2.html', 'w') as file_to:
        file_to.write(r.content)
    soup = BeautifulSoup(courseware)
    data = soup.find('nav',{'aria-label':'课程导航'})
    if data is None:
        print("faile to set cookie")
        sys.exit(0)
    syllabus = []

    for week in data.find_all('div', {'class':'chapter'}):
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
            tab_lists = lesson_soup.find_all('a',{'role':'tab'})
            for tab in tab_lists:
                lec_map[tab.get('id')] = tab.get('title')
            
            lesson_content = []
            for tab in lesson_soup.find_all('div', attrs={'class':"seq_contents tex2jax_ignore asciimath2jax_ignore"}):
                pass
            text = lesson_soup.body.findAll(text=re.compile(r'data-ccsource=\'(?P<source>[^\']+)'))
            if text == [] :
                continue

            # print(text)
            pattern = re.compile(r'data-ccsource=\'(?P<source>[^\']+)')
            sub_pattern = re.compile(r'href=\"(?P<sub_url>[^\"]+)')

            # print(text[0])
            m = pattern.search(text[0].string)
            sub_m = sub_pattern.search(text[0].string)
            #####
            # 6.1 -- D52DDC93AC16EC379C33DC5901307461
            # http://www.xuetangx.com/courses/TsinghuaX/30240243X/2015_T1/courseware/5fc34545f41b41ec96243d4ead29ac6f/971c652c9736442380c616036f339027/
            # get_vid_url = '...source'+ data-ccsource
            ########################
            get_vid_url = 'https://www.xuetangx.com/videoid2source/' + m.group('source')
            r = session.get(get_vid_url)
            data = r.content
            resp = json.loads(data)
            if resp['sources']!=None:
                if resp['sources']['quality20']:
                    tab_video_link = resp['sources']['quality20'][0]
                    print(tab_video_link)
                    # sys.exit(0)
                elif resp['sources']['quality10']:
                    tab_video_link = resp['sources']['quality10'][0]
                else:
                    print('\nATTENTION: Video Missed for \"%s\"' %lec_map[tab.get('aria-labelledby')])
                    continue
            else:
                print('\nATTENTION: Faile to git video for \"%s\"' %lec_map[tab.get('aria-labelledby')])
                continue

            tab_title = lesson_name
            # sub_url = 'https://www.xuetangx.com' + lesson_soup.get('src')
            # sys.exit(0)
            tab_subs_url = homepage + sub_m.group('sub_url')
            print(tab_subs_url)
            lesson_content.append((tab_title,tab_video_link,tab_subs_url))

            # exclude lessons without video                           
            if lesson_content:
                week_content.append((lesson_name, lesson_content))

            print ('.', end="")
        if week_content:
            syllabus.append((week_name, week_content))

    print ("Done.")

    print ("Downloading...")

    retry_list = []
    for (week_num, (week_name, week_content)) in enumerate(syllabus):
        week_name = '%02d %s' %(week_num+1, clean_filename(week_name))
        for (lesson_num,(lesson_name, lesson_content)) in enumerate(week_content):

            lesson_name = '%02d %s' %(lesson_num+1, clean_filename(lesson_name))
            dir = os.path.join(path, coursename, week_name, lesson_name)
            if not os.path.exists(dir):
                mkdir_p(dir)

            for (lec_num, (lec_title, lec_video_url, lec_subtitle)) in enumerate(lesson_content):
                lec_title = '%02d %s' %(lec_num+1, clean_filename(lec_title))
                vfilename = os.path.join(dir, lec_title)
                # print (lec_video_url)
                print (vfilename + '.mp4')
                try:
                    resume_download_file(session, lec_video_url, vfilename + '.mp4', overwrite )
                except Exception as e:
                    print(e)
                    print('Error, add it to retry list')
                    retry_list.append((lec_video_url, vfilename + '.mp4'))

                for (sub_url, language) in lec_subtitle:
                    sfilename = vfilename + '.' + language
                    print (sub_url)
                    print (sfilename + '.srt')
                    if not os.path.exists(sfilename + '.srt') or overwrite:
                        try:
                            download_file(session, sub_url, sfilename + '.srt')
                        except Exception as e:
                            print (e)
                            print('Error, add it to retry list')
                            retry_list.append((sub_url, sfilename + '.srt'))
                            continue
                    else:
                        print ('Already downloaded.')

    retry_times = 0
    while len(retry_list) != 0 and retry_times < 3:
        print('%d items should be retried, retrying...' % len(retry_list))
        retry_times += 1
        for (url, filename) in retry_list:
            try:
                print(url)
                print(filename)
                resume_download_file(session, url, filename, overwrite )
            except Exception as e:
                print(e)
                print('Error, add it to retry list')
                continue

            retry_list.remove((url, filename)) 
    
    if len(retry_list) != 0:
        print('%d items failed, please check it' % len(retry_list))
    else:
        print('All done.')


if __name__ == '__main__':
    main()
