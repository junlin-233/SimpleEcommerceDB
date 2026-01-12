/*
============================================================
项目名称：简易电商平台管理系统数据库
文件名称：init_ecommerce_db.sql
作者：AI Assistant
描述：
    本脚本用于初始化电商平台的数据库环境。包含以下内容：
    1. 数据库和表的创建 (DDL) - 满足第三范式 (3NF)
    2. 索引创建 - 优化查询性能
    3. 存储过程 (Stored Procedures) - 封装核心业务逻辑
    4. 触发器 (Triggers) - 保证数据一致性和自动化处理
    5. 视图 (Views) - 简化报表查询
    6. 模拟测试数据

使用方法：
    在 MySQL 8.0+ 环境中运行此脚本。建议使用 root 或具有足够权限的用户。
============================================================
*/

-- 1. 创建数据库
-- 如果数据库存在则删除，确保环境纯净
DROP DATABASE IF EXISTS ecommerce_db;
CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ecommerce_db;

-- =========================================================
-- 2. 表结构设计 (DDL)
-- =========================================================

/*
表名：Users (用户表)
描述：存储系统用户信息，区分普通用户和管理员。
设计理由：
    - user_id: 主键，自增。
    - username: 唯一约束，便于登录查询。
    - role: 枚举类型，限制权限范围。
*/
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希(实际项目中应加密存储)',
    role ENUM('admin', 'customer') NOT NULL DEFAULT 'customer' COMMENT '角色：管理员/普通用户',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间'
) ENGINE=InnoDB COMMENT='用户信息表';

/*
表名：Products (商品表)
描述：存储商品基本信息。
设计理由：
    - price: 使用DECIMAL保证金额精度，避免浮点数误差。
    - stock_quantity: 这里的库存是当前实际可售库存。
*/
CREATE TABLE Products (
    product_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '商品ID',
    name VARCHAR(100) NOT NULL COMMENT '商品名称',
    description TEXT COMMENT '商品描述',
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0) COMMENT '单价',
    stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0) COMMENT '库存数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上架时间',
    INDEX idx_product_name (name) -- 索引：按名称搜索商品是高频操作
) ENGINE=InnoDB COMMENT='商品信息表';

/*
表名：Orders (订单表)
描述：存储订单头信息。
设计理由：
    - total_amount: 订单总金额，虽然可以通过明细计算，但冗余存储可以提高查询效率（反范式化的一种折中，或者通过触发器维护）。
    - status: 订单状态流转。
*/
CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '订单ID',
    user_id INT NOT NULL COMMENT '下单用户ID',
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00 COMMENT '订单总金额',
    status ENUM('pending', 'paid', 'shipped', 'completed', 'cancelled') DEFAULT 'pending' COMMENT '订单状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE, -- 外键：关联用户
    INDEX idx_order_user (user_id) -- 索引：查询某用户的历史订单
) ENGINE=InnoDB COMMENT='订单主表';

/*
表名：OrderDetails (订单明细表)
描述：存储订单中包含的具体商品和数量。
设计理由：
    - 联合主键 (order_id, product_id) 确保一个订单中同一个商品只出现一次记录。
    - unit_price: 记录下单时的单价，防止商品后续改价影响历史订单金额。
*/
CREATE TABLE OrderDetails (
    detail_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    order_id INT NOT NULL COMMENT '所属订单ID',
    product_id INT NOT NULL COMMENT '商品ID',
    quantity INT NOT NULL CHECK (quantity > 0) COMMENT '购买数量',
    unit_price DECIMAL(10, 2) NOT NULL COMMENT '下单时单价',
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id), -- 这里不级联删除，保留历史数据完整性
    UNIQUE KEY uk_order_product (order_id, product_id) -- 唯一约束：防止重复添加同一商品
) ENGINE=InnoDB COMMENT='订单明细表';

-- =========================================================
-- 3. 触发器 (Triggers)
-- =========================================================

DELIMITER //

/*
触发器：trg_after_order_detail_insert
功能：每当往订单明细表插入一条记录时，自动扣减对应商品的库存。
业务价值：
    1. 保证原子性：插入明细和扣减库存绑定在一起。
    2. 数据一致性：防止超卖。如果库存不足（违反 CHECK 约束 stock>=0），数据库会抛出错误，导致整个事务回滚。
*/
CREATE TRIGGER trg_after_order_detail_insert
AFTER INSERT ON OrderDetails
FOR EACH ROW
BEGIN
    -- 减少对应商品的库存
    UPDATE Products
    SET stock_quantity = stock_quantity - NEW.quantity
    WHERE product_id = NEW.product_id;
    
    -- 注意：如果减完后 stock_quantity < 0，由于 Products 表上有 CHECK (stock_quantity >= 0) 约束，
    -- update 语句会失败，从而触发错误，整个事务（如果是事务内）会回滚。
END //

/*
触发器：trg_update_order_amount
功能：插入订单明细后，自动更新订单主表的总金额。
业务价值：简化业务层逻辑，无需手动计算总价回写。
*/
CREATE TRIGGER trg_update_order_amount
AFTER INSERT ON OrderDetails
FOR EACH ROW
BEGIN
    UPDATE Orders
    SET total_amount = total_amount + (NEW.quantity * NEW.unit_price)
    WHERE order_id = NEW.order_id;
END //

DELIMITER ;

-- =========================================================
-- 4. 存储过程 (Stored Procedures)
-- =========================================================

DELIMITER //

/*
存储过程：sp_register_user
功能：用户注册
输入：p_username, p_password
输出：p_message (返回结果消息)
*/
CREATE PROCEDURE sp_register_user(
    IN p_username VARCHAR(50), 
    IN p_password VARCHAR(255),
    IN p_role VARCHAR(10),
    OUT p_message VARCHAR(100)
)
BEGIN
    DECLARE EXIT HANDLER FOR 1062 -- 处理唯一键冲突 (Duplicate entry)
    BEGIN
        SET p_message = '错误：用户名已存在';
    END;

    INSERT INTO Users (username, password_hash, role) 
    VALUES (p_username, p_password, p_role);
    
    SET p_message = '注册成功';
END //

/*
存储过程：sp_place_order
功能：下订单（核心事务处理）
描述：
    创建一个新订单，并添加商品明细。
    这是一个简化版本，假设一次下单只买一种商品（为了演示参数传递）。
    实际场景通常是传入JSON或在应用层循环插入。
输入：p_user_id, p_product_id, p_quantity
输出：p_order_id, p_message
*/
CREATE PROCEDURE sp_place_order(
    IN p_user_id INT,
    IN p_product_id INT,
    IN p_quantity INT,
    OUT p_order_id INT,
    OUT p_message VARCHAR(100)
)
BEGIN
    DECLARE v_price DECIMAL(10,2);
    DECLARE v_stock INT;
    
    -- 开启事务
    START TRANSACTION;
    
    -- 1. 检查商品是否存在及当前价格
    SELECT price, stock_quantity INTO v_price, v_stock
    FROM Products WHERE product_id = p_product_id FOR UPDATE; -- 加锁防止并发修改
    
    IF v_price IS NULL THEN
        ROLLBACK;
        SET p_message = '错误：商品不存在';
    ELSEIF v_stock < p_quantity THEN
        ROLLBACK;
        SET p_message = CONCAT('错误：库存不足 (剩余: ', v_stock, ')');
    ELSE
        -- 2. 创建订单头
        INSERT INTO Orders (user_id, status) VALUES (p_user_id, 'pending');
        SET p_order_id = LAST_INSERT_ID();
        
        -- 3. 插入订单明细
        -- 这一步会触发 Trigger自动扣减库存。如果库存扣减失败（校验失败），这里会报错回滚
        INSERT INTO OrderDetails (order_id, product_id, quantity, unit_price)
        VALUES (p_order_id, p_product_id, p_quantity, v_price);
        
        COMMIT;
        SET p_message = '下单成功';
    END IF;
END //

/*
存储过程：sp_add_product
功能：管理员上架商品
*/
CREATE PROCEDURE sp_add_product(
    IN p_name VARCHAR(100),
    IN p_desc TEXT,
    IN p_price DECIMAL(10,2),
    IN p_stock INT,
    OUT p_message VARCHAR(100)
)
BEGIN
    INSERT INTO Products (name, description, price, stock_quantity)
    VALUES (p_name, p_desc, p_price, p_stock);
    SET p_message = '商品上架成功';
END //

DELIMITER ;

-- =========================================================
-- 5. 视图 (Views)
-- =========================================================

/*
视图：v_sales_report
功能：统计每种商品的销售总额和总销量
*/
CREATE VIEW v_sales_report AS
SELECT 
    p.product_id,
    p.name AS product_name,
    p.price AS current_price,
    IFNULL(SUM(od.quantity), 0) AS total_sold_count,
    IFNULL(SUM(od.quantity * od.unit_price), 0.00) AS total_revenue
FROM Products p
LEFT JOIN OrderDetails od ON p.product_id = od.product_id
LEFT JOIN Orders o ON od.order_id = o.order_id
-- 这里可以加上 WHERE o.status = 'paid' 来只统计有效订单，演示起见统计所有
GROUP BY p.product_id, p.name, p.price;

-- =========================================================
-- 6. 初始化测试数据
-- =========================================================

-- 添加初始管理员
CALL sp_register_user('admin', 'admin123', 'admin', @msg);
-- 添加测试用户
CALL sp_register_user('alice', 'pass123', 'customer', @msg);
CALL sp_register_user('bob', 'pass456', 'customer', @msg);

-- 添加商品
CALL sp_add_product('高性能笔记本', '16核, 32GB RAM, 1TB SSD', 8999.00, 10, @msg);
CALL sp_add_product('机械键盘', 'Cherry红轴, RGB背光', 399.00, 50, @msg);
CALL sp_add_product('无线鼠标', '2.4G/蓝牙双模', 99.00, 100, @msg);
CALL sp_add_product('4K显示器', '27英寸 IPS面板', 2499.00, 5, @msg);
CALL sp_add_product('Type-C扩展坞', '9合1全功能', 199.00, 200, @msg);

-- 模拟下单
-- Alice 买了一个笔记本
CALL sp_place_order(2, 1, 1, @order_id, @msg);
-- Bob 买了两个机械键盘
CALL sp_place_order(3, 2, 2, @order_id, @msg);

SELECT '数据库初始化完成' AS Status;
