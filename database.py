import pymysql
import sys

# =========================================================
# 数据库配置
# =========================================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'ljb051109', # 请在此处填入你的MySQL root密码
    'database': 'ecommerce_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

class DatabaseManager:
    """数据库管理类：负责连接数据库和执行存储过程"""
    
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
        except pymysql.MySQLError as e:
            # Streamlit 环境下可能需要不同的错误处理，这里先简单的 print
            print(f"数据库连接失败: {e}") 
            # 如果是在 Streamlit 中运行，可以在外部捕获处理

    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()

    def check_connection(self):
        """检查连接是否存活，断开则重连"""
        if self.connection is None:
            self.connect()
            return

        try:
            self.connection.ping(reconnect=True)
        except (pymysql.MySQLError, AttributeError):
            self.connect()

    def call_proc(self, proc_name, args=()):
        """通用存储过程调用方法"""
        self.check_connection()
        if self.connection is None:
            return None, None
            
        try:
            with self.connection.cursor() as cursor:
                cursor.callproc(proc_name, args)
                result = cursor.fetchall()
                self.connection.commit()
                return result, cursor 
        except pymysql.MySQLError as e:
            print(f"数据库操作错误: {e}")
            return None, None

    def execute_query(self, sql, args=()):
        """执行普通查询"""
        self.check_connection()
        if self.connection is None:
            return []
            
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, args)
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"查询错误: {e}")
            return []
