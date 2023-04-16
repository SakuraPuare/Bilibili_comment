import datetime
import json
import pathlib
import random
import re
import time

import httpx
from selenium import webdriver

httpx_cookies_list = []


def cookies():
    driver = webdriver.Chrome()
    driver.get('https://passport.bilibili.com/pc/passport/login')

    while driver.current_url == 'https://passport.bilibili.com/pc/passport/login':
        time.sleep(1)

    cookies = driver.get_cookies()
    driver.quit()

    with open('4.json', 'w') as f:
        json.dump(cookies, f)


def read_cookies():
    for i in pathlib.Path().glob('*.json'):
        with open(i, 'r') as f:
            cookies = json.load(f)

            httpx_cookies = httpx.Cookies()
            for cookie in cookies:
                httpx_cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
            httpx_cookies_list.append(httpx_cookies)


def get_cookies():
    return random.choice(httpx_cookies_list)


if __name__ == '__main__':
    # cookies()
    read_cookies()
    sleep = 0.2
    client = httpx.Client(cookies=get_cookies())

    url = 'https://api.bilibili.com/pgc/view/web/season'
    params = {'season_id': 26257}
    bangumi_list = [i.get('aid') for i in client.get(url, params=params).json()['result']['episodes']]

    # with open('data.csv', 'a') as f:
    #     f.write('time,mid,up,gender,label,like,comment,page,bangumi\n')

    url = 'https://api.bilibili.com/x/v2/reply'
    success = [476022007, 348605649]
    for bangumi in bangumi_list:
        if bangumi in success:
            continue
        page = 0
        count = 10000000000000
        while count > page * 49:
            page += 1
            params = {
                'type': 1,
                'oid': bangumi,
                'sort': 0,
                'nohot': 1,
                'pn': page,
                'ps': 49,
            }
            time.sleep(sleep)
            response = client.get(url, params=params, cookies=get_cookies())
            data = response.json().get('data', {})
            print(page, count)

            count = data.get('page', {}).get('count', 0)
            reply = data.get('replies', [])

            if reply is None:
                continue
            for i in reply:
                try:
                    t = datetime.datetime.fromtimestamp(i['ctime'])
                    mid = i['member']['mid']
                    up = i['member']['uname'].replace(',', '，').replace('\n', '')
                    gender = i['member']['sex']
                    label = i['member']['sign'].replace(',', '，').replace('\n', '').replace(' ', '')
                    like = i['like']
                    comment = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '',
                                     i['content']['message'].replace(',', '，')).replace('\n', '')
                except Exception as e:
                    print(e)
                    continue
                with open('data.csv', 'a') as f:
                    s = f'{t},{mid},{up},{gender},{label},{like},{comment},{page},{bangumi}\n'
                    f.write(s.encode('gbk', 'ignore').decode('gbk'))
                print(comment[:10])
        success.append(bangumi)
        print(success)
