import pymysql
from prettytable import PrettyTable
from database import DatabaseManager

class EcommerceApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.current_user = None # 存储当前登录用户信息 {'id': 1, 'username': 'alice', 'role': 'customer'}

    def print_header(self, title):
        print("\n" + "="*40)
        print(f" {title}")
        print("="*40)

    def main_menu(self):
        while True:
            if not self.current_user:
                self.print_header("简易电商平台 - 欢迎")
                print("1. 用户登录")
                print("2. 用户注册")
                print("q. 退出程序")
                choice = input("请选择: ")
                
                if choice == '1': self.login()
                elif choice == '2': self.register()
                elif choice.lower() == 'q': break
                else: print("无效输入")
            else:
                self.user_menu()

    def user_menu(self):
        role_zh = "管理员" if self.current_user['role'] == 'admin' else "普通用户"
        print(f"\n当前用户: {self.current_user['username']} ({role_zh})")
        
        print("-" * 20)
        print("1. 浏览商品列表")
        print("2. 购买商品 (下单)")
        print("3. 查看我的订单")
        
        if self.current_user['role'] == 'admin':
            print("8. [管理员] 上架新商品")
            print("9. [管理员] 查看销售报表")
            
        print("0. 注销登录")
        print("-" * 20)
        
        choice = input("请选择功能: ")
        
        if choice == '1': self.view_products()
        elif choice == '2': self.place_order()
        elif choice == '3': self.view_my_orders()
        elif choice == '8' and self.current_user['role'] == 'admin': self.add_product()
        elif choice == '9' and self.current_user['role'] == 'admin': self.view_sales_report()
        elif choice == '0': 
            self.current_user = None
            print("已注销。")
        else:
            print("无效输入或权限不足")

    def login(self):
        print("\n[登录]")
        username = input("用户名: ")
        password = input("密码: ")
        
        # 使用裸SQL简单验证，实际应调用存储过程或更加安全的方式
        sql = "SELECT * FROM Users WHERE username=%s"
        users = self.db.execute_query(sql, (username,))
        
        if users:
            user = users[0]
            # 简化演示，直接比对明文密码 (实际应对比 Hash)
            if user['password_hash'] == password:
                self.current_user = user
                print(f"✅ 登录成功！欢迎回来, {user['username']}")
                return
        
        print("❌ 登录失败：用户名或密码错误")

    def register(self):
        print("\n[注册新用户]")
        username = input("请输入用户名: ")
        password = input("请输入密码: ")
        
        # 调用存储过程 sp_register_user (username, password, role, out_msg)
        # 这里使用与 Streamlit 前端一致的写法，直接使用 CALL + 用户变量 @msg
        try:
            with self.db.connection.cursor() as cursor:
                # 初始化 OUT 变量
                cursor.execute("SET @msg = ''")
                cursor.execute(
                    "CALL sp_register_user(%s, %s, %s, @msg)",
                    (username, password, 'customer')
                )
                cursor.execute("SELECT @msg")
                result = cursor.fetchone()
                msg = result['@msg']
                
                if '成功' in msg:
                    self.db.connection.commit()
                    print(f"✅ {msg}")
                else:
                    print(f"❌ {msg}")
        except Exception as e:
            print(f"❌ 系统错误: {e}")

    def view_products(self):
        print("\n[商品列表]")
        products = self.db.execute_query("SELECT * FROM Products ORDER BY product_id")
        
        if not products:
            print("暂无商品。")
            return

        table = PrettyTable()
        table.field_names = ["ID", "商品名称", "描述", "价格(元)", "库存"]
        for p in products:
            table.add_row([p['product_id'], p['name'], p['description'][:20]+"...", p['price'], p['stock_quantity']])
        print(table)

    def place_order(self):
        self.view_products()
        print("\n[下单]")
        try:
            p_id = int(input("请输入商品ID: "))
            qty = int(input("请输入购买数量: "))
            
            if qty <= 0:
                print("❌ 数量必须大于0")
                return

            # 调用存储过程 sp_place_order(user_id, product_id, quantity, out_order_id, out_msg)
            # 使用 CALL 语法 + 用户变量，避免多语句执行和 callproc OUT 参数处理的坑
            with self.db.connection.cursor() as cursor:
                cursor.execute("SET @oid = 0")
                cursor.execute("SET @msg = ''")
                cursor.execute(
                    "CALL sp_place_order(%s, %s, %s, @oid, @msg)",
                    (self.current_user['user_id'], p_id, qty)
                )
                cursor.execute("SELECT @oid, @msg")
                res = cursor.fetchone()
                msg = res['@msg']
                
                if '成功' in msg:
                    self.db.connection.commit()
                    print(f"✅ {msg} (订单号: {res['@oid']})")
                else:
                    # 存储过程内部已经处理了 ROLLBACK，这里只需提示信息
                    print(f"❌ {msg}")
                    
        except ValueError:
            print("❌ 输入格式错误，请输入数字")
        except Exception as e:
            print(f"❌ 系统错误: {e}")

    def view_my_orders(self):
        print("\n[我的订单]")
        sql = """
            SELECT o.order_id, o.total_amount, o.status, o.created_at, p.name 
            FROM Orders o
            JOIN OrderDetails od ON o.order_id = od.order_id
            JOIN Products p ON od.product_id = p.product_id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
        """
        orders = self.db.execute_query(sql, (self.current_user['user_id'],))
        
        if not orders:
            print("暂无订单记录。")
            return

        table = PrettyTable()
        table.field_names = ["订单号", "商品", "总金额", "状态", "时间"]
        for o in orders:
            table.add_row([o['order_id'], o['name'], o['total_amount'], o['status'], o['created_at']])
        print(table)

    def add_product(self):
        print("\n[管理员 - 上架商品]")
        name = input("商品名称: ")
        desc = input("商品描述: ")
        try:
            price = float(input("价格: "))
            stock = int(input("初始库存: "))
            
            with self.db.connection.cursor() as cursor:
                cursor.execute("SET @msg = ''")
                cursor.execute(
                    "CALL sp_add_product(%s, %s, %s, %s, @msg)",
                    (name, desc, price, stock)
                )
                cursor.execute("SELECT @msg")
                res = cursor.fetchone()
                print(f"✅ {res['@msg']}")
                self.db.connection.commit()
                
        except ValueError:
            print("❌ 价格或库存格式错误")

    def view_sales_report(self):
        print("\n[管理员 - 销售报表视图]")
        # 这里直接查询视图 v_sales_report
        report = self.db.execute_query("SELECT * FROM v_sales_report")
        
        table = PrettyTable()
        table.field_names = ["ID", "商品名称", "当前价格", "总销量", "总销售额"]
        for r in report:
            table.add_row([r['product_id'], r['product_name'], r['current_price'], r['total_sold_count'], r['total_revenue']])
        print(table)

if __name__ == "__main__":
    try:
        app = EcommerceApp()
        app.main_menu()
    except KeyboardInterrupt:
        print("\n程序已退出。")
    except Exception as e:
        print(f"发生未预期的错误: {e}")
