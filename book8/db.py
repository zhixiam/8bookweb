# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import os
import MySQLdb
from dotenv import load_dotenv

load_dotenv(dotenv_path='db.env')

class Database:
    def __init__(self):
        host = os.getenv('DB_HOST', 'localhost')
        user = os.getenv('DB_USER', 'root')
        password = os.getenv('DB_PASSWORD', '')
        dbname = os.getenv('DB_NAME', 'your_database_name')
        port = int(os.getenv('DB_PORT', 3306))  

        self.conn = MySQLdb.connect(
            host=host,
            user=user,
            passwd=password,
            db=dbname,
            port=port,
            charset='utf8mb4'
        )
        self.cursor = self.conn.cursor()

    def execute_query(self, sql, params=None):
        try:
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error executing query: {e}")
            return None

    def execute_update(self, sql, params=None):
        try:
            self.cursor.execute(sql, params)
            self.conn.commit()
        except Exception as e:
            print(f"Error executing update: {e}")
            self.conn.rollback()

    def close(self):
        self.conn.close()