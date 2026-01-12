# 简易电商平台管理系统

一个基于 MySQL 8.0 和 Python 的简易电商平台后端系统，展示数据库原理的实际应用，包括关系模型设计、完整性约束、存储过程和触发器的高级应用。

## 📋 项目特性

- **数据库设计**：遵循第三范式 (3NF)，确保数据一致性和完整性
- **存储过程**：封装核心业务逻辑，提高安全性和性能
- **触发器**：自动化数据维护，防止超卖等业务问题
- **视图**：简化复杂查询，提供便捷的报表功能
- **双界面支持**：提供命令行版本和 Streamlit Web 界面

## 🏗️ 系统架构

### 核心实体

1. **用户 (Users)**: 系统的参与者，分为管理员和普通用户
2. **商品 (Products)**: 平台售卖的货物
3. **订单 (Orders)**: 用户的一次购买行为记录（订单头）
4. **订单明细 (OrderDetails)**: 订单中具体的商品项

### 数据库特性

- **第三范式设计**：消除数据冗余，保证数据一致性
- **外键约束**：维护数据完整性
- **索引优化**：提高查询性能
- **事务控制**：确保操作的原子性
- **触发器自动化**：自动扣减库存、更新订单金额

## 🚀 快速开始

### 环境要求

- Python 3.7+
- MySQL 8.0+
- pip (Python 包管理器)

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone <your-repo-url>
   cd SimpleEcommerceDB
   ```

2. **安装 Python 依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **初始化数据库**
   - 打开 MySQL 客户端或Navicat（直接运行脚本代码）
   - 运行 `init_ecommerce_db.sql` 脚本：
   ```bash
   mysql -u root -p < init_ecommerce_db.sql
   ```
   或者在 MySQL 客户端中执行：
   ```sql
   source init_ecommerce_db.sql
   ```

4. **配置数据库连接**
   - 编辑 `database.py` 文件，修改数据库配置：
   ```python
   DB_CONFIG = {
       'host': 'localhost',
       'user': 'root',
       'password': 'your_password',  # 修改为你的 MySQL 密码
       'database': 'ecommerce_db',
       'charset': 'utf8mb4',
       'cursorclass': pymysql.cursors.DictCursor
   }
   ```

## 💻 使用方法

### 命令行版本

运行命令行界面：
```bash
python main.py
```

功能菜单：
- 用户登录/注册
- 浏览商品列表
- 购买商品（下单）
- 查看我的订单
- [管理员] 上架新商品
- [管理员] 查看销售报表

### Web 界面版本

运行 Streamlit Web 应用：
```bash
streamlit run streamlit_app.py
```

浏览器会自动打开 `http://localhost:8501`

## 🔑 测试账号

系统初始化后会自动创建以下测试账号：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| alice | pass123 | 普通用户 |
| bob | pass456 | 普通用户 |

## 📁 项目结构

```
SimpleEcommerceDB/
├── README.md                 # 项目说明文档
├── requirements.txt          # Python 依赖列表
├── design_doc.md            # 数据库设计文档
├── init_ecommerce_db.sql    # 数据库初始化脚本
├── database.py              # 数据库管理类
├── main.py                  # 命令行版本主程序
└── streamlit_app.py         # Streamlit Web 界面
```

## 🗄️ 数据库设计

### 表结构

- **Users**: 用户信息表
- **Products**: 商品信息表
- **Orders**: 订单主表
- **OrderDetails**: 订单明细表

### 存储过程

- `sp_register_user`: 用户注册
- `sp_place_order`: 下单（包含事务控制）
- `sp_add_product`: 管理员上架商品

### 触发器

- `trg_after_order_detail_insert`: 自动扣减库存
- `trg_update_order_amount`: 自动更新订单总金额

### 视图

- `v_sales_report`: 销售报表视图

详细设计说明请参考 [design_doc.md](design_doc.md)

## 🔧 技术栈

- **后端语言**: Python 3.7+
- **数据库**: MySQL 8.0+
- **数据库驱动**: PyMySQL
- **命令行界面**: PrettyTable
- **Web 框架**: Streamlit
- **数据处理**: Pandas

## 📝 主要功能

### 普通用户功能
- ✅ 用户注册和登录
- ✅ 浏览商品列表
- ✅ 购买商品（下单）
- ✅ 查看个人订单历史

### 管理员功能
- ✅ 上架新商品
- ✅ 查看销售报表
- ✅ 管理商品库存

## 🛡️ 安全特性

- 使用存储过程防止 SQL 注入
- 事务控制确保数据一致性
- 触发器自动维护数据完整性
- 外键约束保证数据关联正确性

## 📊 数据库原理应用

本项目展示了以下数据库原理的实际应用：

1. **范式化设计**：遵循第三范式，消除数据冗余
2. **完整性约束**：主键、外键、CHECK 约束
3. **存储过程**：封装业务逻辑，提高安全性
4. **触发器**：自动化数据维护
5. **视图**：简化复杂查询
6. **索引优化**：提高查询性能
7. **事务控制**：保证 ACID 特性

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目仅供学习和演示使用。


## 📚 参考资料

- MySQL 8.0 官方文档
- Python PyMySQL 文档
- Streamlit 官方文档

---

**注意**：本项目为教学演示项目，密码以明文存储，实际生产环境应使用密码哈希（如 bcrypt）进行加密存储。
