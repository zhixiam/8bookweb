# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 05:23:44 2023

@author: mot66
"""

from flask import Flask, render_template, request, url_for, session, redirect
from db import Database
from reptile import NovelScraper 
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
db = Database()

'''sql結構
create table IF NOT EXISTS book8(
id int primary key auto_increment,
book varchar(20) NOT NULL,
img varchar(255),
author varchar(20) NOT NULL,
chapter_title varchar(50) NOT NULL,
character_count varchar(20) NOT NULL,
text LONGTEXT,
book_url varchar(200),
post_date datetime);
''' 
@app.route('/')
def home():
    """
    首頁
    """
    try:
        sql = "SELECT book, author, img, COUNT(*) as book_count, MAX(post_date) as latest_update FROM book8 GROUP BY book, author order by latest_update DESC limit 36;"   
        result = db.execute_query(sql)
    except Exception as e:
        print(f"An error occurred: {e}")
  
    return render_template('home.html', result=result)
@app.route('/search', methods=['GET'])
def search_books():
    query = request.args.get('query')
    try:
        sql = "SELECT book, author, img, COUNT(*) as book_count FROM book8 where book like %s or author like %s;"   
        result = db.execute_query(sql, ('%' + query + '%', '%' + query +'%'))
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")

    back_link = url_for('home')

    return render_template('search_results.html',query=query, result = result,back_link = back_link)


@app.route('/book')
def book():
    """   
    書籍目錄  
    """
    #章節查詢
    book_name = request.args.get('book', '')
    try:    
        sql = "select chapter_title from book8 where book = %s GROUP BY chapter_title"
        result = db.execute_query(sql, (book_name,))
    except Exception as e:
        print(f"An error occurred: {e}")
    #書籍詳情查詢   
    try:
        sql = "SELECT book, author, img, COUNT(*) as book_count, MAX(post_date) as last_updated FROM book8 where book = %s;"   
        book_result = db.execute_query(sql, (book_name,))
        book_name = book_result[0][0]
        book_author = book_result[0][1]
        book_img = book_result[0][2]
        book_count = book_result[0][3]
        post_date = book_result[0][4]
    except Exception as e:
        print(f"An error occurred: {e}")
    back_link = url_for('home')
    return render_template('book.html',back_link=back_link, result = result, book_name=book_name, book_author=book_author,book_img=book_img,book_count=book_count ,post_date=post_date)

@app.route('/text')
def text():    
    """   
    章節頁面   
    """
    chapter_title = request.args.get('book', '')
    chapter_title = chapter_title.replace('+', ' ')
    try:
        sql = "select text from book8 where chapter_title = %s"
        db.cursor.execute(sql, (f'{chapter_title}',))
        result = db.cursor.fetchone()
        if result:
            result_content = result[0]
            formatted_content = result_content.replace('。', '。\n\n')
            html_content = f'<p>{formatted_content}</p>'
            #print("Result from database:", html_content)
        else:
            return render_template('text.html', result="章節未找到", chapter_title=chapter_title)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('text.html', result="發生錯誤", chapter_title=chapter_title)
    #返回目錄邏輯取得當前id與book
    try:
       book_sql = "SELECT id, book FROM book8 WHERE chapter_title = %s"
       db.cursor.execute(book_sql, (f'{chapter_title}',))
       book_result = db.cursor.fetchone()
       if book_result:
           book_id = book_result[0]
           book_name = book_result[1]
       else:
            # 處理找不到書籍信息的情況
            return render_template('text.html', result="無法回到目錄", chapter_title=chapter_title)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('text.html', result="發生錯誤", chapter_title=chapter_title) 

    
    #下一頁邏輯使用id+1來取得下一章的章節名
    try:
       book_sql = "SELECT chapter_title FROM book8 WHERE book = %s and id = %s + 1"
       db.cursor.execute(book_sql, (f'{book_name}', f'{book_id}',))
       next_chapter_result = db.cursor.fetchone()
       if next_chapter_result:
           next_chapter_title = next_chapter_result[0]
           next_link = url_for('text', book =f"{next_chapter_title}")         
       else:
           next_link = None
           
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('text.html', result="發生錯誤", chapter_title=chapter_title)
    #返回目錄url
    back_link = url_for('book', book=f'{book_name}')
    
    return render_template('text.html', result=html_content, chapter_title=f'{chapter_title}', back_link=back_link, next_link=next_link)

def get_title_list():
    """
    從 session 中取得爬蟲資料中的書籍標題列表
    """
    return session.get('reptile_data', {}).get('title_list', [])

def update_title_list(title_list):
    """
    更新爬蟲資料中session的書籍標題列表
    """
    session['reptile_data'] = {'title_list': title_list}

def select_and_scrape_novel_data(novel_scraper, title_list, user_input):
    """
    選擇並爬取小說資訊
    
    Parameters:
    - novel_scraper (NovelScraper): 小說爬蟲實例
    - title_list (list): 全部的小說標題列表
    - user_input (str): 使用者選擇的小說編號
    """
    url2, selected_link, selected_book = novel_scraper.select_novel(title_list, user_input)
    
    if selected_book and selected_link:
        return novel_scraper.scrape_and_store_novel_info(url2, selected_link, selected_book)
    else:
        return None, None, None, None

@app.route('/reptile', methods=['GET', 'POST'])
def reptile():
    """
    爬蟲頁面的路由函數
    """
    back_link = url_for('home')

    title_list = get_title_list()
    
    novel_scraper = NovelScraper()
    
    
    if request.method == 'POST':
        data = request.form.get('novel_name')
        
        title_list = novel_scraper.search(data)
        
        update_title_list(title_list)
        
        return render_template('reptile.html', back_link=back_link, title_list=title_list)

    if request.method == 'GET':
        user_input = request.args.get('selected_index')

        if user_input:
            
            
            try:
                selected_book, img_url, author, currentTime = select_and_scrape_novel_data(novel_scraper, title_list, user_input)
            except:
                return redirect(url_for('reptile'))
            
            if selected_book is not None:
                # 成功爬取資料，移除session資料中的書籍資訊
                session.pop('reptile_data', None)
                return render_template('reptile.html', back_link=back_link, selected_book=selected_book, img_url=img_url, author=author, currentTime=currentTime)
                      
            
    return render_template('reptile.html', back_link=back_link)


    
if __name__ == '__main__':
    app.run(debug=True)
    
    