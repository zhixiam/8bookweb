# 8bookweb
這是作品網站
https://s93114604.pythonanywhere.com/

使用方式

pythonanywhere 虛擬環境建立

virtualenv --python=python3.10 bookweb建立虛擬環境

source bookweb/bin/activate進入虛擬環境

--------------------------------------------------------------------------

需安裝插件

pip install mysqlclient 資料庫

pip install flask

pip install bs4

pip install urljoin 

pip install datetime

pip install load-dotenv 搜索.env文件

pip install requests

pip install PyJWT 切記!!!不要和jwt裝在一起(解決方式兩個一起刪再重裝)

pip freeze > requirements.txt匯出虛擬環境所安裝的套件

pip install -r (當前所在的路徑)/requirements.txt 安裝清單中的套件

---------------------------------------------------------------------------

pythonanywhere 資料庫匯入方式

1.將檔案上傳到file的資料夾(如:/home/s93114604/mysite)

2.去database建立資料庫名稱(如:輸入bookdb就會出現 使用者名稱$bookdb)

3.use 你的資料庫;

4.source /home/使用者名稱/創建的資料夾/你匯出的資料庫名稱.sql;

5.若還是抓不到資料庫請去查詢db.py將db.env的資料輸入進去

若資料庫已有資料須先刪除

drop database 你的資料庫;

---------------------------------------------------------------------------

sql 資料庫格式

create database bookdb default character set utf8 collate utf8_general_ci;

table格式(四個)

書籍訊息

CREATE TABLE IF NOT EXISTS books (

book_id INT AUTO_INCREMENT PRIMARY KEY,

book VARCHAR(100),

author VARCHAR(100),

image VARCHAR(255)

);

書籍章節內容

CREATE TABLE IF NOT EXISTS `chapters` (

  `chapter_id` int NOT NULL AUTO_INCREMENT,
  
  `book_id` int NOT NULL,
  
  `chapter_title` varchar(255) NOT NULL,
  
  `character_count` varchar(20) DEFAULT NULL,
  
  `text` longtext,
  
  `update_date` datetime NOT NULL,
  
  PRIMARY KEY (`chapter_id`),
  
  KEY `book_id` (`book_id`),
  
  CONSTRAINT `fk_chapters_books` FOREIGN KEY (`book_id`) REFERENCES `books` (`book_id`)
  
);

使用者訊息

CREATE TABLE `users` (

  `user_id` int NOT NULL AUTO_INCREMENT,
  
  `username` varchar(255) NOT NULL,
  
  `password_hash` varchar(255) NOT NULL,
  
  `email` varchar(255) NOT NULL,
  
  `creation_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  
  `account_status` enum('Active','Inactive') DEFAULT 'Active',
  
  `permission_level` enum('admin','moderator','user') DEFAULT 'user',
  
  `reset_token` varchar(255) DEFAULT NULL,
  
  PRIMARY KEY (`user_id`)
  
);

最愛書籍

CREATE TABLE `user_favorite_books` (

  `user_id` int NOT NULL,
  
  `book_id` int NOT NULL,
  
  PRIMARY KEY (`user_id`,`book_id`),
  
  KEY `book_id` (`book_id`),
  
  CONSTRAINT `user_favorite_books_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  
  CONSTRAINT `user_favorite_books_ibfk_2` FOREIGN KEY (`book_id`) REFERENCES `books` (`book_id`)
  
);
