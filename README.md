# 8bookweb

這是一個基於 Python Flask 的網路小說網站，提供用戶瀏覽和閱讀小說的功能。  
您可以在此處查看線上版本：[8bookweb 線上版](https://s93114604.pythonanywhere.com/)

---

## 功能特性

- **小說列表**：展示可供閱讀的小說清單，包括書名、作者和封面圖片。  
- **章節閱讀**：點擊小說進入章節列表，選擇章節進行閱讀。  
- **用戶認證**：提供用戶註冊、登入和密碼找回功能，確保用戶資料安全。  
- **資料擷取與更新**：使用網路爬蟲定期更新小說內容，保持資料的時效性。  

---

## 技術棧

- **前端**：  
  - HTML5  
  - CSS3  
  - JavaScript  
- **後端**：  
  - Python Flask  
- **資料庫**：  
  - MySQL  
- **網路爬蟲**：  
  - BeautifulSoup  
  - Selenium  
- **部署**：  
  - PythonAnywhere  

---

## 環境設置與安裝

1. **建立虛擬環境**：  
   ```bash
   virtualenv --python=python3.10 bookweb
   source bookweb/bin/activate
   
2. **安裝必要套件**：  
   ```bash
   pip install -r requirements.txt
   
## 資料庫設置與初始化  

1. **建立資料庫**

   在 MySQL 中執行以下指令，建立資料庫 `bookdb` 並設定字符集：  
   ```sql
   CREATE DATABASE bookdb DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;

2. **匯入資料庫結構和初始資料**

   將現有的資料庫結構及初始資料匯入到新建的資料庫中，執行以下指令：
   ```sql
   USE bookdb;
   SOURCE /path/to/your/database_dump.sql;

   請將 /path/to/your/database_dump.sql 替換為實際檔案存放路徑。

3. **驗證資料庫設置**

   執行以下指令，確認資料庫結構和內容已正確匯入：
   ```sql
   USE bookdb;
   SOURCE /path/to/your/database_dump.sql;

   請將 your_table_name 替換為您的資料表名稱。

## 環境變數設置

   在專案根目錄中建立 .env 檔案，並填入以下內容：
   ```env
   DATABASE_URI=mysql://username:password@localhost/bookdb
   SECRET_KEY=your_secret_key
  
   username：MySQL 用戶名
   password：MySQL 密碼
   your_secret_key：應用程式的隨機密鑰，用於加密和驗證功能
