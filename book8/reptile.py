
"""
Created on Mon Dec 18 05:18:07 2023

@author: mot66
"""

import requests
from bs4 import BeautifulSoup
import re
from db import Database
from urllib.parse import urljoin
from datetime import datetime

class NovelScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        }
        self.session = requests.Session()
        self.url = 'https://8book.com'

    def search(self, data):
        """
        到該網站，搜尋小說關鍵字資訊，並將其標題存儲到session中。

        Parameters:
        - data (str): 小說的名稱
        """   
        search_data = {'key': data}
        search_url = self.url + '/search/'
        print('search_url',search_url)
        response = self.session.get(search_url, params=search_data, headers=self.headers)
        search_results = BeautifulSoup(response.content, 'html.parser')

        if search_results is None:
            print('未找到搜索結果')
            return []

        titles = search_results.find_all('div', class_='col-12 col-sm-12 col-md-6 col-lg-4 p-2')
        title_list = []

        try:
            for i, title_element in enumerate(titles):
                book_name = title_element.find('li', class_='nowraphide').text
                novel_link = title_element.find('a', class_='w-100 nowraphide').get('href')
                match = re.search(r'/(\d+)', novel_link)
                if match:
                    link = match.group(1)
                    title_list.append((book_name, link))
        except AttributeError as e:
            print('請重抓element屬性', e)
        return title_list

    def select_novel(self, title_list, user_input):
        """
        取得使用者所選擇的小說。

        Parameters:
        - title_list (list): session全部的小說標題
        - user_input (str): 使用者選擇的小說編號
        """ 
        
        selected_book = None
        selected_link = None
    
        if user_input is not None and user_input.isdigit():
            selected_index = int(user_input) - 1
            if 0 <= selected_index < len(title_list):
                selected_book, selected_link = title_list[selected_index]
    
        if selected_book is not None and selected_link is not None:
            url2 = self.url + f'/novelbooks/{selected_link}/'
            return url2, selected_link, selected_book
        else:
            return None, None

    def scrape_and_store_novel_info(self, url2, selected_link, selected_book):
        """
        爬取小說資訊，並將其存儲到資料庫中。

        Parameters:
        - url2 (str): 該小說的網址
        - headers (dict): HTTP 請求標頭
        - selected_link (int): 爬取小說編號
        - selected_book (str): 書籍名稱
        """
        response = self.session.get(url2, headers=self.headers)
        db = Database()
        if response.status_code == 200:
            soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
            tag = {"仙俠武俠": 2, "仙武": 2, "玄幻奇幻": 8, "玄幻": 8, "都市言情": 3, "言情": 3, "穿越重生": 4, "穿越": 4, "魔法異界": 1, "魔法": 1,
                   "網游競技": 6, "競技": 6, "恐怖靈異": 5, "靈異": 5, "日輕小說": 9, "日輕": 9, "動漫同人": 14, "同人": 14, "軍事紀實": 10, "紀實": 10,
                   "歷史名著": 11, "名著": 11}

            meta_tag = soup.find('meta', attrs={'name': 'cat'})
            if meta_tag:
                category = meta_tag['content']

            if category in tag:
                book_tag = tag[category]
                print(f"小說類型 {category} 對應的數字代號是: {book_tag}")
            else:
                print(f"未找到小說類型 {category}")

            
            book_img = soup.find('div', class_='d-none d-md-block col-md-2 p-0 item-cover').find('img')
            img_url = book_img['src']
            img_url = urljoin(self.url, img_url)
            print(img_url)

            charset = soup.meta.get('charset')
            if charset:
                decoded_text = response.content.decode(charset)
                soup = BeautifulSoup(decoded_text, 'html.parser')
                author = soup.find('span', class_="mr-1 item-info-author").text
                print(author)

            chapters = soup.find_all('a', class_='col-sm-12 col-md-6 col-lg-4 py-2 episode_li')
            for chapter in chapters:
                chapter_title = chapter.text.strip()
                chapter_link = self.url + chapter['href']
                print(f'章節名稱: {chapter_title}')

                url3 = chapter_link
                response = self.session.get(url3, headers=self.headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                scripts = soup.find_all('script')
                
                #開始解析js
                pattern = r"var (\w+)=\"(\d+(?:,\d+)*)\"\.split\('\s*,\s*'\);"
                matches = []

                for script in scripts:
                    script_text = script.text
                    matches.extend(re.findall(pattern, script_text, re.DOTALL))
                    if matches:
                        for match in matches:
                            variable_name = match
                            pattern = r"(\d+)$"
                            matches = re.search(pattern, variable_name[1])

                            if matches:
                                last_group_of_numbers = matches.group(1)

                real_link = chapter['href']
                match = re.search(r'/(\d+)/\?(\d+)', real_link)
                if match:
                    extracted_number = match.group(2)
                
                ca0g1s8 = extracted_number
                b7y404w = 3
                wq__17kjr1 = 100
                mr2d75 = 5
                index = (int(ca0g1s8) * b7y404w) % wq__17kjr1
                input_string = last_group_of_numbers
                end_index = index + mr2d75
                desired_digits = input_string[index:end_index]
                final_url = self.url + f"/txt/{book_tag}/{selected_link}/{ca0g1s8}{desired_digits}.html"

                response = self.session.get(final_url)

                if response.status_code == 200:
                    page_content = response.content.decode(charset)
                    soup = BeautifulSoup(page_content, 'html.parser')

                    text_content = soup.get_text()
                    #清除防盜流水
                    cleaned_text = re.sub(r'[^\u4e00-\u9fa5，。？！、]+', '', text_content)
                    character_count = len(cleaned_text)
                    print(f'爬取成功 字數為{character_count}')
                    print(f'連結 {final_url}')

                    currentDateAndTime = datetime.now()
                    currentTime = currentDateAndTime.strftime("%Y-%m-%d %H:%M:%S")
                    print(currentTime)


                    sql_upsert = """
                        INSERT INTO book8(book, img, author, chapter_title, character_count, text, book_url, post_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        book = VALUES(book),
                        img = VALUES(img),
                        author = VALUES(author),
                        chapter_title = VALUES(chapter_title),
                        character_count = VALUES(character_count),
                        text = VALUES(text),
                        book_url = VALUES(book_url),
                        post_date = VALUES(post_date)
                    """

                    db.execute_update(sql_upsert, (selected_book, img_url, author, chapter_title, character_count, cleaned_text, final_url, currentTime))
        db.close()


        return selected_book, img_url, author, currentTime
