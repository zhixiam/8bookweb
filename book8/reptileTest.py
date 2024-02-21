# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 19:00:15 2024

@author: mot66
"""
import requests
from bs4 import BeautifulSoup
import re
from db import Database
from urllib.parse import urljoin
from datetime import datetime
import os


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}
session = requests.Session()
url = 'https://8book.com'
url2 = 'https://8book.com/novelbooks/292696/'
selected_book = '終將走向戀愛喜劇的暗殺者'
selected_link = '292696'

response = session.get(url2, headers=headers)
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
        
    charset = soup.meta.get('charset')
    if charset:
        decoded_text = response.content.decode(charset)
        soup = BeautifulSoup(decoded_text, 'html.parser')
        author = soup.find('span', class_="mr-1 item-info-author").text
        print(author)
    
    book_img = soup.find('div', class_='d-none d-md-block col-md-2 p-0 item-cover').find('img')
    img = book_img['src']
    img_url = urljoin(url, img)
    print(img_url)
    if img_url:
        response = requests.get(img_url, headers=headers)
        if response.status_code == 200:
            # 將檔案名稱設置為希望的路徑格式
            images = os.path.join('static', 'images')
            filename = os.path.join(images, selected_book + '.jpg')           

            with open(filename, 'wb') as f:
                f.write(response.content)
                print("圖片已下載並儲存到:", filename)

        else:
            print("圖片下載失敗:", response.status_code)

    # 檢查書名是否已存在
    sql_check_existing_book = """
        SELECT COUNT(*) 
        FROM books 
        WHERE book = %s
    """
    
    existing_count = db.execute_query(sql_check_existing_book, (selected_book,))
    existing = existing_count[0][0]  # 如果書名存在，existing 將是 1，否則為 0
    
    # 如果書名不存在，插入新書籍
    if existing == 0:
        sql_insert_book = """
            INSERT INTO books (book, author, image)
            VALUES (%s, %s, %s)
        """
        db.execute_update(sql_insert_book, (selected_book, author, filename))
        print("成功插入新書籍")
    else:
        print("書名已存在，無需插入新書籍")
    
    chapters = soup.find_all('a', class_='col-sm-12 col-md-6 col-lg-4 py-2 episode_li')
    num_chapters = len(chapters)
    print(f'總共有{num_chapters}')
    for chapter in chapters:
        chapter_title = chapter.text.strip()
        chapter_link = url + chapter['href']
        print(f'章節名稱: {chapter_title}')

        url3 = chapter_link
        response = session.get(url3, headers=headers)
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
        final_url = url + f"/txt/{book_tag}/{selected_link}/{ca0g1s8}{desired_digits}.html"

        response = session.get(final_url)

        if response.status_code == 200:
            page_content = response.content.decode(charset)
            soup = BeautifulSoup(page_content, 'html.parser')

            text_content = soup.get_text()
            #清除防盜流水
            cleaned_text = re.sub(r'[вＯьoσк⑧ｋ．ｃm⑻ＢОК·См8Ь.cΟＫCｂом８kＢｏοOKСｍBсb⒏Ｃm　]', '', text_content)
            print(cleaned_text)
            character_count = len(cleaned_text)
            print(f'爬取成功 字數為{character_count}')
            print(f'連結 {final_url}')

            currentDateAndTime = datetime.now()
            update_date = currentDateAndTime.strftime("%Y-%m-%d %H:%M:%S")
            print(update_date)
            
            #確認該章節是否已在資料庫
            sql_check_existing_chapter = """
                SELECT COUNT(*) 
                FROM chapters 
                WHERE book_id = (SELECT book_id FROM books WHERE book = %s) 
                AND chapter_title = %s
            """
            
            existing_count = db.execute_query(sql_check_existing_chapter, (selected_book, chapter_title))                  
            #existing_count若有資料則返回資料，否則0
            existing = existing_count[0][0]#取其值確認是否為0

            if existing == 0:
                sql_upsert_chapters = """
                    INSERT INTO chapters(book_id, chapter_title, character_count, text, update_date)
                    VALUES (
                        (SELECT book_id FROM books WHERE book = %s),
                        %s, %s, %s, %s
                    )
                """
                
                db.execute_update(sql_upsert_chapters, (selected_book, chapter_title, character_count, cleaned_text, update_date))
            else:
                sql_update_chapter = """
                    UPDATE chapters
                    SET character_count = %s, text = %s, update_date = %s
                    WHERE book_id = (SELECT book_id FROM books WHERE book = %s) 
                    AND chapter_title = %s
                """
                db.execute_update(sql_update_chapter, (character_count, cleaned_text, update_date, selected_book, chapter_title))
                print("該章節已存在已進行更新。")

db.close()


