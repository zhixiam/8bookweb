# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 18:08:39 2024

@author: mot66
"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from db import Database
db = Database()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}
session = requests.Session()

title = '漫威之超級毒液'
url = 'https://www.twbook.cc/181219835/dir'
response = session.get(url, headers=headers)
soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')  
for num in range(776, 1034):
    url1 = f'https://www.twbook.cc/181219835/{num}.html'
    response = session.get(url1, headers=headers)
    soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
    content = soup.find('div',class_="content")
    #chapter = content.find('p')
    print(content)
    '''
    content = soup.find('div',class_="content")
    full_text = content.get_text()
    cleaned_text = re.sub(r'[  ]', '', full_text)
    print(cleaned_text)
    character_count = len(cleaned_text)
    print(f'爬取成功 字數為{character_count}')
    
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
    
    existing_count = db.execute_query(sql_check_existing_chapter, (title, chapter))                  
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
        
        db.execute_update(sql_upsert_chapters, (title, chapter, character_count, cleaned_text, update_date))
    else:
        sql_update_chapter = """
            UPDATE chapters
            SET character_count = %s, text = %s, update_date = %s
            WHERE book_id = (SELECT book_id FROM books WHERE book = %s) 
            AND chapter_title = %s
        """
        db.execute_update(sql_update_chapter, (character_count, cleaned_text, update_date, title, chapter))
        print("該章節已存在已進行更新。")    
'''
db.close()    
    
    