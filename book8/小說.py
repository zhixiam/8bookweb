# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 13:22:17 2024

@author: mot66
"""
import requests
from bs4 import BeautifulSoup
import re
from db import Database
from datetime import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

url = 'https://big5.quanben5.com/n/wozhenbushixieshenzougou/xiaoshuo.html'
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')
db = Database()
charset = soup.meta.get('charset')
if charset:
    soup = BeautifulSoup(response.content.decode(charset), 'html.parser')
    book_info = soup.find('div', class_='pic_txt_list')
    book_name = book_info.find('h3').find('span').text
    print(book_name)
    text_author = book_info.find('span', class_='author').text
    author = f"作者:{text_author}"
    print(author)
    img = book_info.find('img').get('src')
    if img:
        response = requests.get(img, headers=headers)
        images = response.content
       
    booklist = soup.find_all('li', class_='c3')

    sql_upsert_books = """
        INSERT INTO books(book, author, image)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
        book = VALUES(book),
        author = VALUES(author),
        image = VALUES(image)
    """
    
    db.execute_update(sql_upsert_books, (book_name, author, images))
    for i in booklist:  
        chapter_title = i.find('span').text
        a = i.find('a').get('href')
        chapter_url = a.split("/")[-1]
        url_text = url.replace('xiaoshuo.html', chapter_url) 
        response2 = requests.get(url_text, headers=headers)
        soup2 = BeautifulSoup(response2.content.decode(charset), 'html.parser')
        text = soup2.find('div', id='content').text
        cleaned_text = re.sub(r'[\a-z\0-5\(\)\）]', '', text)
        character_count = len(cleaned_text)
        
        currentDateAndTime = datetime.now()
        update_date = currentDateAndTime.strftime("%Y-%m-%d %H:%M:%S")
        print(update_date)
        
        sql_upsert_chapters = """
                INSERT INTO chapters(book_id, chapter_title, character_count, text, update_date)
                VALUES (
                    (SELECT book_id FROM books WHERE book = %s),
                    %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                chapter_title = VALUES(chapter_title),
                character_count = VALUES(character_count),
                text = VALUES(text),
                update_date = VALUES(update_date)
            """
            
        db.execute_update(sql_upsert_chapters, (book_name, chapter_title, character_count, cleaned_text, update_date))
db.close()
     
            
            
        