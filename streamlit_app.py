import streamlit as st
import pandas as pd
from database import DatabaseManager

# 初始化数据库连接
# 使用 st.cache_resource 确保数据库连接在刷新时不会重复创建，但要注意线程安全
# 这里简单处理，每次页面加载实例化一个，Manager内部自管理
# 或者更好的方式是把 Manager 放在 session_state

def get_db():
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()
    return st.session_state.db

def main():
    st.set_page_config(page_title="简易电商平台", layout="wide")
    
    # 侧边栏导航
    st.sidebar.title("导航")
    
    if 'user' not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        user_menu()
    else:
        login_register_menu()

def login_register_menu():
    menu = st.sidebar.radio("请选择", ["登录", "注册"])
    
    if menu == "登录":
        st.title("用户登录")
        with st.form("login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            submit = st.form_submit_button("登录")
            
            if submit:
                db = get_db()
                sql = "SELECT * FROM Users WHERE username=%s"
                users = db.execute_query(sql, (username,))
                
                if users:
                    user = users[0]
                    if user['password_hash'] == password:
                        st.session_state.user = user
                        st.success(f"登录成功，欢迎: {user['username']}")
                        st.rerun()
                    else:
                        st.error("登录失败：密码错误")
                else:
                    st.error("登录失败：用户不存在")
                    
    elif menu == "注册":
        st.title("用户注册")
        with st.form("register_form"):
            new_user = st.text_input("用户名")
            new_pass = st.text_input("密码", type="password")
            new_pass_confirm = st.text_input("确认密码", type="password")
            submit = st.form_submit_button("注册")
            
            if submit:
                if new_pass != new_pass_confirm:
                    st.error("两次密码输入不一致")
                else:
                    db = get_db()
                    try:
                        with db.connection.cursor() as cursor:
                            # 使用直接 CALL 语法，更稳定
                            # 传入参数: u, p, role, @msg
                            cursor.execute("CALL sp_register_user(%s, %s, %s, @msg)", (new_user, new_pass, 'customer'))
                            cursor.execute("SELECT @msg")
                            result = cursor.fetchone()
                            msg = result['@msg']
                            
                            if '成功' in msg:
                                db.connection.commit()
                                st.success(msg + "，请前往登录页面")
                            else:
                                st.error(msg)
                    except Exception as e:
                        st.error(f"注册发生错误: {e}")

def user_menu():
    user = st.session_state.user
    st.sidebar.write(f"当前用户: **{user['username']}**")
    st.sidebar.write(f"角色: **{user['role']}**")
    
    if st.sidebar.button("注销"):
        st.session_state.user = None
        st.rerun()
        
    st.sidebar.markdown("---")
    
    options = ["商品列表", "我的订单"]
    if user['role'] == 'admin':
        options.extend(["[管理员] 上架商品", "[管理员] 销售报表"])
        
    choice = st.sidebar.radio("功能菜单", options)
    
    if choice == "商品列表":
        show_products(user)
    elif choice == "我的订单":
        show_orders(user)
    elif choice == "[管理员] 上架商品":
        add_product_page()
    elif choice == "[管理员] 销售报表":
        show_report()

def show_products(user):
    st.header("商品列表")
    db = get_db()
    products = db.execute_query("SELECT * FROM Products ORDER BY product_id")
    
    if not products:
        st.info("暂无商品")
        return
        
    # 转换为DataFrame展示更美观
    df = pd.DataFrame(products)
    df = df[['product_id', 'name', 'description', 'price', 'stock_quantity']]
    df.columns = ['ID', '名称', '描述', '价格', '库存']
    st.dataframe(df, use_container_width=True)
    
    st.markdown("### 购买商品")
    with st.form("buy_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_id = st.number_input("请输入商品ID", min_value=1, step=1)
        with col2:
            qty = st.number_input("购买数量", min_value=1, step=1)
        
        buy_btn = st.form_submit_button("立即下单")
        
        if buy_btn:
            try:
                with db.connection.cursor() as cursor:
                    # 使用显式 CALL，自动处理 OUT 参数通过变量 @oid, @msg
                    cursor.execute("CALL sp_place_order(%s, %s, %s, @oid, @msg)", 
                                   (user['user_id'], p_id, qty))
                    cursor.execute("SELECT @oid, @msg")
                    res = cursor.fetchone()
                    msg = res['@msg']
                    
                    if '成功' in msg:
                        db.connection.commit()
                        st.success(f"{msg} (订单号: {res['@oid']})")
                    else:
                        st.error(msg)
            except Exception as e:
                st.error(f"系统错误: {e}")

def show_orders(user):
    st.header("我的订单")
    db = get_db()
    sql = """
        SELECT o.order_id, p.name AS product_name, o.total_amount, o.status, o.created_at
        FROM Orders o
        JOIN OrderDetails od ON o.order_id = od.order_id
        JOIN Products p ON od.product_id = p.product_id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
    """
    orders = db.execute_query(sql, (user['user_id'],))
    
    if orders:
        df = pd.DataFrame(orders)
        df.columns = ['订单号', '商品名称', '总金额', '状态', '下单时间']
        st.dataframe(df, use_container_width=True)
    else:
        st.info("您还没有订单记录")

def add_product_page():
    st.header("上架新商品 (管理员)")
    
    with st.form("add_product"):
        name = st.text_input("商品名称")
        desc = st.text_area("商品描述")
        price = st.number_input("价格", min_value=0.01, step=0.01)
        stock = st.number_input("初始库存", min_value=1, step=1)
        
        submit = st.form_submit_button("上架")
        
        if submit:
            if not name:
                st.warning("请输入商品名称")
                return
                
            db = get_db()
            try:
                with db.connection.cursor() as cursor:
                    cursor.execute("CALL sp_add_product(%s, %s, %s, %s, @msg)", 
                                   (name, desc, price, stock))
                    cursor.execute("SELECT @msg")
                    res = cursor.fetchone()
                    st.success(res['@msg'])
                    db.connection.commit()
            except Exception as e:
                st.error(f"操作失败: {e}")

def show_report():
    st.header("销售报表 (管理员)")
    db = get_db()
    report = db.execute_query("SELECT * FROM v_sales_report")
    
    if report:
        df = pd.DataFrame(report)
        df.columns = ['商品ID', '商品名称', '当前单价', '总销量', '总销售额']
        st.dataframe(df, use_container_width=True)
        
        # 简单的图表展示
        st.markdown("#### 销售额概览")
        st.bar_chart(df.set_index('商品名称')['总销售额'])
    else:
        st.info("暂无销售数据")

if __name__ == "__main__":
    main()
