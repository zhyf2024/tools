# Joom产品爬虫插件

## 功能描述
本插件用于从Joom网站抓取男装产品信息，包括产品名称、产品描述、产品图片、产品参数、产品价格等信息，并将抓取的数据存储到本地数据库中。

## 依赖安装

在使用本插件前，请确保已安装Scrapling库：

```bash
pip install scrapling
```

## 目录结构

```
module_joom_scraper/
├── __init__.py
├── joom/
│   ├── __init__.py
│   ├── controller.py    # API控制器
│   ├── crud.py          # 数据访问层
│   ├── model.py         # 数据库模型
│   ├── schema.py        # Pydantic模式
│   └── service.py       # 业务逻辑（包含爬虫功能）
├── plugin.toml          # 插件元数据
└── README.md            # 本文件
```

## API接口

所有接口均需要相应的权限才能访问：

### 1. 抓取Joom产品
**POST** `/joom/scrape`

请求体：
```json
{
  "category_url": "https://www.joom.com/en/category/mens-fashion/c.1597236266669222893-190-2-2-2152716438",
  "max_products": 20
}
```

响应：返回抓取到的产品列表

### 2. 获取产品详情
**GET** `/joom/detail/{id}`

### 3. 分页查询产品列表
**GET** `/joom/list`

查询参数：
- `page_no`: 页码（默认1）
- `page_size`: 每页数量（默认10）
- `product_name`: 产品名称模糊搜索
- `min_price`: 最小价格
- `max_price`: 最大价格
- `status`: 产品状态（0:正常 1:停用）

### 4. 修改产品
**PUT** `/joom/update/{id}`

请求体：与创建产品相同的字段

### 5. 删除产品
**DELETE** `/joom/delete`

请求体：`{"ids": [1, 2, 3]}`

### 6. 批量修改产品状态
**PATCH** `/joom/status/batch`

请求体：`{"ids": [1, 2, 3], "status": 0}`

## 数据模型

Joom产品模型包含以下字段：
- `product_name`: 产品名称
- `product_description`: 产品描述
- `product_url`: 产品原始URL
- `price`: 产品价格
- `currency`: 货币单位（默认USD）
- `main_image_url`: 主图片URL
- `image_local_path`: 本地图片保存路径
- `status`: 状态(0:启动 1:停用)

## 注意事项

1. 图片会自动下载并保存到 `static/uploads/joom_images` 目录
2. 插件会自动检查产品URL是否已存在，避免重复抓取
3. 请确保网络可以访问Joom网站
4. 抓取频率请合理控制，避免对目标网站造成压力