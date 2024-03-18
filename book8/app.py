# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 05:23:44 2023

@author: mot66
"""

from flask import Flask, render_template, request, url_for, session, redirect, jsonify, flash
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from db import Database
from reptile import NovelScraper 
import os
import hashlib
import datetime
import jwt
import secrets
import string
import logging


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
db = Database()

#日誌設定
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
log_directory = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
log_filename = os.path.join(log_directory, f'{current_date}.log')
logging.basicConfig(filename=log_filename, level=logging.INFO)


def get_user_info():
    """
    將用戶資訊從session取出做哈希解碼
    """
    token = session.get('token')
    if token:
        try:
            decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            return decoded_token
        except jwt.ExpiredSignatureError:

            session.pop('token', None)
    return None

@app.context_processor
def inject_user_info():
    """
    全局訪問用於存儲用戶資訊
    """  
    return {'user': get_user_info()}

@app.route('/')
def home():
    """
    首頁
    """   
    db = Database()  # 建立資料庫連線
    
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 寫入日誌
    logging.info(f'{current_time} - P Address: {ip_address}, User-Agent: {user_agent}')
    
    prev_link = None
    next_link = None    
    
    page = request.args.get('page', 1, type=int)
    per_page = 8  # 每頁顯示的書籍數量
    
    try:
        sql ="""
                SELECT
                    books.*,
                    COUNT(chapters.chapter_id) AS total_chapters,
                    MAX(chapters.update_date) AS latest_update_date
                FROM books
                LEFT JOIN chapters ON books.book_id = chapters.book_id
                GROUP BY books.book_id, book, image
                ORDER BY latest_update_date DESC
            """
        results = db.execute_query(sql)
        
        #分頁製作
        total_books = len(results)
        total_pages = (total_books // per_page) + (1 if total_books % per_page > 0 else 0)
        offset = (page - 1) * per_page
        results = results[offset : offset + per_page]
        
    except Exception as e:
        print(f"An error occurred: {e}")
        total_pages = 0
        results = []
        
    books_info = []
    for result in results:
        book_id = result[0]
        book_name = result[1]
        img_data = result[3]


        # 將每本書籍的資訊放入字典
      
        book_info = {
            'book_id': book_id,
            'book_name': book_name,
            'image': img_data,
        }
 
        # 將字典加入列表
        books_info.append(book_info)
        
        prev_link = url_for('home', page=page - 1) if page > 1 else None
        next_link = url_for('home', page=page + 1) if page < total_pages else None
    
    #從session中取得用戶資訊
    user_info = get_user_info()
    if user_info:
        favorite_books = []

        user_id = user_info.get('user_id')
        try:
            favorite_book = db.execute_query("SELECT book_id FROM user_favorite_books WHERE user_id=%s", (user_id,))
            
            for book_id in favorite_book:
                book_id = book_id[0]  # 提取 book_id
                book_info = db.execute_query("SELECT book, image FROM books WHERE book_id=%s", (book_id,))
                if book_info:
                    book_name = book_info[0][0]
                    image_data = book_info[0][1] 
                    
                    favorite_books.append({'book_id': book_id, 'book_name': book_name, 'image': image_data})

        except Exception as e:
            print(f"An error occurred: {e}")
        db.close()
        return render_template('home.html', books_info=books_info, total_pages=total_pages, current_page=page, prev_link=prev_link, next_link=next_link, favorite_books=favorite_books)
    db.close()
    return render_template('home.html', books_info=books_info, total_pages=total_pages, current_page=page, prev_link=prev_link, next_link=next_link)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """   
    註冊邏輯  
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        
        if password != confirm_password:
            flash('密碼和確認密碼不一致')
        
        # 檢查用戶名是否已經存在
        existing_user = db.execute_query("SELECT * FROM users WHERE username=%s", (username,))
        if existing_user:         
            flash('已有重複名稱')
        
        # 密碼加密
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # 將用戶的資料存入
        db.execute_update("INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)", (username, hashed_password, email,))
        
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """   
    登入邏輯   
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 使用元組的方式查詢以防sql注入
        user = db.execute_query("SELECT * FROM users WHERE username=%s", (username,))
        if user:
            
            #獲取哈希密碼
            user_info = user[0]
            
            stored_password_hash = user_info[2]
            
            permission_level = user_info[6]
            # 將用戶輸入的密碼做哈希處理
            input_password_hash = hashlib.sha256(password.encode()).hexdigest()

            # 比較哈希碼
            if input_password_hash == stored_password_hash:
                
                # 生成 JWT Token
                token_payload = {
                    'user_id': user_info[0],
                    'username': user_info[1],
                    'usermail': user_info[3],
                    'permission_level':user_info[6],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
                }

                token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
                session['token'] = token
                
                if permission_level == 'admin':
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('home'))
                
            else:
                flash('用戶名或密碼不對，請重新嘗試。')
        else:
            flash('用戶名不存在，請重新嘗試。')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """   
    從session中刪除token   
    """
    session.pop('token', None)
    return redirect(url_for('home'))

def generate_reset_token():
    """
    自動生成長度20的token
    """
    token_length = 20  # 設置 token 的長度
    token_characters = string.ascii_letters + string.digits  # 包含在 token 中的字符集
    reset_token = ''.join(secrets.choice(token_characters) for _ in range(token_length))
    return reset_token

def send_reset_password_email(email, reset_token):
    """
    用於與gmail串接並發送郵件
    """
    gmail_user = 'mot666888@gmail.com'  
    gmail_password = 'nyvx dgxx akvp hxjb'#由google生成16位元密碼登入並非本身google密碼  
    
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = email
    msg['Subject'] = 'Reset Your Password'
    domin = '127.0.0.1:5000'#根據domin修改
    reset_password_link = f"{domin}/reset_password/{reset_token}"
    message = f"Click the following link to reset your password: {reset_password_link}"
    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, email, msg.as_string())
        server.close()
        print('Email發送成功')
    except Exception as e:
        print('Email發送失敗')
        print(e)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """
    忘記密碼邏輯
    使用smtplib向google發送簡易信件
    """
    if request.method == 'POST':
        email = request.form.get('email')
        
        reset_token = generate_reset_token()
        
        db.execute_update("UPDATE users SET reset_token = %s WHERE email = %s", (reset_token, email))

        users = db.execute_query("SELECT * FROM users WHERE email = %s and reset_token = %s ", (email, reset_token))
        if users:
            send_reset_password_email(email, reset_token)
            flash("已發送驗證碼，請到信箱點擊驗證網址。", "success")
            return redirect(url_for('login'))
        else:
            flash("該信箱並無被註冊，請重新輸入。", "error")
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

@app.route('/reset_password/<reset_token>', methods=['GET', 'POST'])
def reset_password(reset_token):
    """
    忘記密碼邏輯
    驗證是否包含token
    """
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        
        user = db.execute_query("SELECT email FROM users WHERE reset_token = %s", (reset_token,))
        if user:
            if new_password == confirm_password:
                hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
            
                db.execute_update("UPDATE users SET password_hash=%s WHERE reset_token=%s", (hashed_password, reset_token))
                
                flash("你的密碼已被更改請重新登入。", "success")
                
                db.execute_update("UPDATE users SET reset_token = NULL WHERE email = %s", (user[0],))
                return redirect(url_for('login'))
            else:
                flash("密碼與確認密碼不相同，請重新輸入。", "error")
                return redirect(url_for('reset_password', reset_token = reset_token))
        else:
            flash("token驗證失敗，請再輸入一次", "error")
            return redirect(url_for('forgot_password'))

    return render_template('reset_password.html', reset_token = reset_token)

@app.route('/search', methods=['GET'])
def search_books():
    """   
    搜尋頁面   
    """
    query = request.args.get('query')
    try:
        sql = """
                SELECT
                    books.*,
                    COUNT(chapters.chapter_id) AS total_chapters,
                    MAX(chapters.update_date) AS latest_update_date
                FROM books
                LEFT JOIN chapters ON books.book_id = chapters.book_id
                where book like %s or author like %s
                GROUP BY books.book_id, book, author, image;
            """   
        results = db.execute_query(sql, ('%' + query + '%', '%' + query +'%'))
    except Exception as e:
        print(f"An error occurred: {e}")
    
    books_info = []
    for result in results:
        book_id = result[0]
        book_name = result[1]
        book_author = result[2]
        img_data = result[3]
        total_chapters = result[4]
        latest_update_date = result[5]
        # 將每本書籍的資訊放入字典
        book_info = {
            'book_id': book_id,
            'book_name': book_name,
            'book_author': book_author,
            'image': img_data,
            'total_chapters': total_chapters,
            'latest_update_date': latest_update_date
        }
 
        # 將字典加入列表
        books_info.append(book_info)
        
    back_link = url_for('home')

    return render_template('search_results.html',query=query, books_info = books_info, back_link = back_link)

def is_book_in_favorites(user_id, book_id):
    try:
        result = db.execute_query("SELECT * FROM user_favorite_books WHERE user_id = %s AND book_id = %s", (user_id, book_id))
        return bool(result) 
    except Exception as e:
        print(f"An error occurred while checking if book is in favorites: {e}")
        return False 
  
@app.route('/book')
def book():
    """   
    書籍目錄  
    """
    back_link = url_for('home')
    #章節查詢
    book_id = request.args.get('book', '')
    try:    
        sql = "select chapter_title, book_id, chapter_id from chapters where book_id = %s"
        chapter_result = db.execute_query(sql, (book_id,))
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    #書籍詳情查詢       
    try:
        sql = """
                SELECT
                    books.*,
                    COUNT(chapters.chapter_id) AS total_chapters,
                    MAX(chapters.update_date) AS latest_update_date
                FROM books
                LEFT JOIN chapters ON books.book_id = chapters.book_id
                where books.book_id = %s
                GROUP BY books.book_id, book, author, image;
            """    
        book_result = db.execute_query(sql, (book_id,))
    except Exception as e:
        print(f"An error occurred: {e}")
    
    
    for result in book_result:
        book_name = result[1]
        book_author = result[2]
        img_data = result[3]
        total_chapters = result[4]
        latest_update_date = result[5]
        # 將每本書籍的資訊放入字典
      
    user_info = get_user_info()   
    if user_info:
        user_id = user_info['user_id']
        favorite = is_book_in_favorites(user_id, book_id)
        return render_template('book.html',favorite=favorite, back_link=back_link, book_id=book_id, chapter_result=chapter_result , book_name=book_name, book_author=book_author, img_data=img_data,total_chapters=total_chapters, latest_update_date=latest_update_date)
    else:
        return render_template('book.html',back_link=back_link, book_id=book_id, chapter_result=chapter_result , book_name=book_name, book_author=book_author, img_data=img_data,total_chapters=total_chapters, latest_update_date=latest_update_date)

@app.route('/add_to_favorites', methods=['POST'])
def add_to_favorites():
    """   
    添加到使用者最愛列表
    """
    if request.method == 'POST':

        book_id = request.form.get('book_id')
        
        try:
            user_info = get_user_info() 
            if user_info and 'user_id' in user_info:
                user_id = user_info.get('user_id')  
                existing_entry = db.execute_query("SELECT * FROM user_favorite_books WHERE user_id = %s AND book_id = %s", (user_id, book_id))
                if existing_entry:
                    return jsonify({'success': False, 'message': '書籍已在收藏夾中。'})
                else:
                    db.execute_update("INSERT INTO user_favorite_books (user_id, book_id) VALUES (%s, %s)", (user_id, book_id))
                    return jsonify({'success': True, 'message': '書籍已成功添加到我的最愛'})
            else:
                return jsonify({'success': False, 'message': '用戶未登入，請先登入。'})
        except Exception as e:
            return jsonify({'success': False, 'message': '添加書籍失敗，請稍後。', 'error': str(e)})


@app.route('/remove_from_favorites', methods=['POST'])
def remove_from_favorites():
    if request.method == 'POST':
        
        book_id = request.form.get('book_id')

        try:
            user_info = get_user_info() 
            if user_info and 'user_id' in user_info:
                user_id = user_info.get('user_id')  

                existing_entry = db.execute_query("SELECT * FROM user_favorite_books WHERE user_id = %s AND book_id = %s", (user_id, book_id))

                if existing_entry:
                    db.execute_update("DELETE FROM user_favorite_books WHERE user_id=%s AND book_id=%s", (user_id, book_id))
                    return jsonify({'success': True, 'message': '書籍已從我的最愛刪除。'})
                else:
                    return jsonify({'success': False, 'message': '書籍未添加到我的最愛中'})
            else:
                return jsonify({'success': False, 'message': '用戶未登入，請先登入。'})
        except Exception as e:
            return jsonify({'success': False, 'message': '刪除書籍失敗，請稍後。', 'error': str(e)})

        
def custom_split(text):
    """   
    根據要求進行斷行   
    """
    paragraphs = []
    paragraph = ''
    in_quotes = False
    left_quotes = ['“', '「', '（', '【', '『', '《']
    right_quotes = ['”', '」', '）', '】', '』', '》']

    for i, char in enumerate(text):
        paragraph += char

        if char in left_quotes:
            in_quotes = True
        elif char in right_quotes:
            in_quotes = False

            # 檢查右引號的下一個，是否是左引號
            if i < len(text) - 1 and text[i + 1] in left_quotes:
                paragraphs.append(paragraph.strip() + '\n\n')
                paragraph = ''#初始化文字
                
        if not in_quotes:  # 檢查是否在引號內
            if char in '。':
                paragraphs.append(paragraph.strip() + '\n\n')
                paragraph = ''
    

    if paragraph:
        paragraphs.append(paragraph.strip())

    return paragraphs

@app.route('/text')
def text():    
    """   
    內文頁面   
    """
    chapter_title = request.args.get('book',)
    chapter_title = chapter_title.replace('+', ' ')#將書名的+替換成空格
    book_id = request.args.get('book_id')
    chapter_id = request.args.get('chapter_id')
    
    try:
        sql = "select text from chapters where chapter_title = %s and book_id = %s"
        db.cursor.execute(sql, (f'{chapter_title}', book_id,))
        result = db.cursor.fetchone()
        if result:
            result_content = result[0]
            formatted_sentences = custom_split(result_content)
            html_content = ''.join([f'<p>{sentence}</p>' for sentence in formatted_sentences])

        else:
            return render_template('text.html', result="章節未找到", chapter_title=chapter_title)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('text.html', result="發生錯誤", chapter_title=chapter_title)

    
    #下一頁邏輯找尋chapter_id比它還大的來取得下一章的章節名
    try:
       book_sql = "SELECT chapter_title, book_id, chapter_id FROM chapters WHERE book_id = %s and chapter_id > %s ORDER BY chapter_id ASC LIMIT 1"
       db.cursor.execute(book_sql, (book_id, chapter_id,))
       next_chapter_result = db.cursor.fetchone()
       if next_chapter_result:
           next_chapter_title = next_chapter_result[0]
           book_id = next_chapter_result[1]
           chapter_id = next_chapter_result[2]
           next_link = url_for('text', book =f"{next_chapter_title}", book_id = book_id, chapter_id = chapter_id)         
       else:
           next_link = None
           
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('text.html', result="發生錯誤", chapter_title=chapter_title)
    #返回目錄url
    back_link = url_for('book', book = book_id)

    return render_template('text.html', html_content=html_content, chapter_title=f'{chapter_title}', back_link=back_link, next_link=next_link)

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
    back_link = url_for('admin')

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
                
                selected_book, images, author, update_date = select_and_scrape_novel_data(novel_scraper, title_list, user_input)


            except:
                return redirect(url_for('reptile'))
            
            if selected_book is not None:
                # 成功爬取資料，移除session資料中的書籍資訊
                session.pop('reptile_data', None)
                return render_template('reptile.html', back_link=back_link, selected_book=selected_book, images=images, author=author, update_date=update_date)
                      
            
    return render_template('reptile.html', back_link=back_link)

@app.route('/admin')
def admin():
    if 'token' in session:
        user_info = get_user_info()
        if user_info and user_info['permission_level'] == 'admin':
            # 如果是管理員，則傳遞用戶資訊到模板中
            return redirect(url_for('user_management'))
        else:
            # 如果不是管理員，則重定向到登入頁面
            flash('您無權訪問此頁面')
            return redirect(url_for('login'))
    else:
       # 如果沒有登入 token，則重定向到登入頁面
       flash('請先登入')
       return redirect(url_for('login'))
   

@app.route('/user_management')
def user_management():
    db = Database()
    if 'token' in session:
        user_info = get_user_info()
        if user_info and user_info['permission_level'] == 'admin':          
            try:
                users = db.execute_query("SELECT * FROM users")
            except Exception as e:
                flash('用戶資訊獲取失敗')
                print(f"An error occurred: {e}")
        else:
            # 如果不是管理員，則重定向到登入頁面
            flash('您無權訪問此頁面')
            return redirect(url_for('login'))
    else:
       # 如果沒有登入 token，則重定向到登入頁面
       flash('請先登入')
       return redirect(url_for('login'))
   
    return render_template('user_management.html', users=users)

@app.route('/user_management/edit/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    db = Database()
    try:
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            account_status = request.form['account_status']
            permission = request.form['permission']
          
            db.execute_query("UPDATE users SET username = %s, email = %s, account_status = %s, permission_level = %s WHERE user_id = %s", (username, email, account_status, permission, user_id))
            flash('用戶信息更新成功')
        else:
            flash('請使用POST方法提交表單')
    except Exception as e:
        flash('用戶信息更新失敗')
        print(f"An error occurred: {e}")
    db.close()

    return redirect(url_for('user_management'))

@app.route('/user_management/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    
    db = Database()
    try:
        db.execute_query("DELETE FROM users WHERE user_id = %s", (user_id,))
        flash('用戶刪除成功')
    except Exception as e:
        flash('用戶刪除失敗')
        print(f"An error occurred: {e}")
    db.close()

    return redirect(url_for('user_management'))    
    
@app.route('/admin_book')
def admin_book():
    db = Database()
    if 'token' in session:
        user_info = get_user_info()
        if user_info and user_info['permission_level'] == 'admin':
            prev_link = None
            next_link = None    
            page = request.args.get('page', 1, type=int)
            per_page = 10  # 每頁顯示的書籍數量
            try:
                books = db.execute_query("SELECT * FROM books")
                total_books = len(books)
                total_pages = (total_books // per_page) + (1 if total_books % per_page > 0 else 0)
                offset = (page - 1) * per_page
                books = books[offset : offset + per_page]
            except Exception as e:
                flash('書籍資訊獲取失敗')
                print(f"An error occurred: {e}")
            if page > 1:    
                prev_link = url_for('admin_book', page=page - 1) 
            if page < total_pages:
                next_link = url_for('admin_book', page=page + 1)
        else:
            # 如果不是管理員，則重定向到登入頁面
            flash('您無權訪問此頁面')
            return redirect(url_for('login'))
    else:
       # 如果沒有登入 token，則重定向到登入頁面
       flash('請先登入')
       return redirect(url_for('login'))
    return render_template('admin_book.html', books=books, total_pages=total_pages, current_page=page, prev_link=prev_link, next_link=next_link)

@app.route('/admin_book/edit/<int:book_id>', methods=['POST'])
def edit_book(book_id):
    db = Database()

    try:
        if request.method == 'POST':
            book = request.form['book']
            author = request.form['author']
            image = request.form['image']
            
            db.execute_query("UPDATE books SET book = %s, author = %s, image = %s WHERE book_id = %s", (book, author, image, book_id))
            flash('書籍信息更新成功')
        else:
            flash('請使用POST方法提交表單')
    except Exception as e:
        flash('書籍信息更新失敗')
        print(f"An error occurred: {e}")
    db.close()

    return redirect(url_for('admin_book'))

@app.route('/admin_book/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    
    db = Database()
    try:
        db.execute_query("DELETE FROM books WHERE book_id = %s", (book_id,))
        db.execute_query("DELETE FROM chapters WHERE book_id = %s", (book_id,))
        flash('書籍刪除成功')
    except Exception as e:
        flash('書籍刪除失敗')
        print(f"An error occurred: {e}")
    db.close()

@app.route('/chapters/<int:book_id>', methods=['GET', 'POST'])
def chapters(book_id):
    db = Database()
    prev_link = None
    next_link = None   
    if 'token' in session:
        user_info = get_user_info()
        if user_info and user_info['permission_level'] == 'admin':
            page = request.args.get('page', 1, type=int)
            per_page = 4  # 每頁顯示的書籍數量
            try:
                
                chapters = db.execute_query("SELECT * FROM chapters where book_id = %s", (book_id,))
                #分頁製作
                total_chapters = len(chapters)
                total_pages = (total_chapters // per_page) + (1 if total_chapters % per_page > 0 else 0)
                offset = (page - 1) * per_page
                chapters = chapters[offset : offset + per_page]
            except Exception as e:
                flash('書籍資訊獲取失敗')
                print(f"An error occurred: {e}")
            if page > 1:    
                prev_link = url_for('chapters', book_id=book_id, page=page - 1) 
            if page < total_pages:
                next_link = url_for('chapters', book_id=book_id, page=page + 1)
        else:
            # 如果不是管理員，則重定向到登入頁面
            flash('您無權訪問此頁面')
            return redirect(url_for('login'))
    else:
       # 如果沒有登入 token，則重定向到登入頁面
       flash('請先登入')
       return redirect(url_for('login'))
    return render_template('admin_chapters.html', book_id=book_id, chapters=chapters, total_pages=total_pages, current_page=page, prev_link=prev_link, next_link=next_link )


@app.route('/chapters/save_chapter/<int:chapter_id>', methods=['POST'])
def save_chapter(chapter_id):
    db = Database()
    
    try:
        if request.method == 'POST':
            book_id = request.form['book_id']
            chapter_title = request.form['chapter_title']
            character_count = request.form['character_count']
            chapterText = request.form['chapterText']
            
            db.execute_query("UPDATE chapters SET book_id = %s, chapter_title = %s, character_count = %s, text = %s WHERE chapter_id = %s", (book_id, chapter_title, character_count, chapterText, chapter_id))
            flash('書籍信息更新成功')
        else:
            flash('請使用POST方法提交表單')
    except Exception as e:
        flash('書籍信息更新失敗')
        print(f"An error occurred: {e}")
    db.close()

    return redirect(url_for('chapters', book_id=book_id))

@app.route('/chapters/delete/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    
    db = Database()
    try:
        db.execute_query("DELETE FROM chapters WHERE chapter_id = %s", (chapter_id,))
        flash('書籍刪除成功')
    except Exception as e:
        flash('書籍刪除失敗')
        print(f"An error occurred: {e}")
    db.close()

@app.route('/log')
def show_logs():
    if 'token' in session:
        user_info = get_user_info()
        if user_info and user_info['permission_level'] == 'admin':
            log_files = []
            for filename in os.listdir(log_directory):
                if filename.endswith('.log'):
                    log_files.append(filename)
        else:
            # 如果不是管理員，則重定向到登入頁面
            flash('您無權訪問此頁面')
            return redirect(url_for('login'))
    else:
       # 如果沒有登入 token，則重定向到登入頁面
       flash('請先登入')
       return redirect(url_for('login'))
    return render_template('log.html', log_files=log_files)


@app.route('/log/<filename>')
def show_log(filename):
    log_directory = os.path.join(os.path.dirname(__file__), 'logs')
    log_contents = read_log_file(log_directory, filename)
    return render_template('log.html', log_contents=log_contents)

def read_log_file(log_directory, filename):
    log_content = []
    log_filename = os.path.join(log_directory, filename)
    if os.path.exists(log_filename):
        with open(log_filename, 'r') as f:
            log_content = f.readlines()
    return log_content
    
if __name__ == '__main__':
    app.run()
    
    
