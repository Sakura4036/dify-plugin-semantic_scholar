# Semantic Scholar Dify插件

## 简介
这是一个基于Semantic Scholar API的Dify插件，提供学术论文搜索和检索功能。通过此插件，您可以在Dify平台上轻松搜索和获取学术论文的详细信息。

## 功能
该插件提供以下工具：

1. **相关性搜索 (Relevance Search)** - 根据查询内容按相关性搜索学术论文
2. **批量搜索 (Bulk Search)** - 一次执行多个查询搜索
3. **论文详情 (Paper Detail)** - 获取特定论文的详细信息
4. **多篇论文详情 (Multiple Papers Detail)** - 同时获取多篇论文的详细信息
5. **标题搜索 (Title Search)** - 根据标题搜索论文

## 安装

### 方法1：远程调试安装
1. 复制`.env.example`文件并重命名为`.env`
2. 在Dify平台的插件管理页面获取远程调试信息并填入`.env`文件
3. 运行以下命令启动插件：
   ```
   python -m main
   ```

### 方法2：打包安装
1. 使用Dify插件工具打包插件：
   ```
   dify plugin package ./
   ```
2. 在Dify平台的插件管理页面上传生成的`.difypkg`文件

## 配置
插件支持以下配置：

- **API密钥** (可选) - Semantic Scholar API密钥，可增加API请求限制

## 工具用法

### 相关性搜索
根据查询内容搜索相关论文。

参数：
- `query`：搜索查询文本（必填）
- `limit`：返回结果数量，默认10，最大100
- `fields`：指定返回的字段，逗号分隔

### 批量搜索
一次执行多个查询搜索。

参数：
- `queries`：搜索查询列表，可以是JSON数组或逗号分隔的值（必填）
- `fields`：指定返回的字段，逗号分隔

### 论文详情
获取特定论文的详细信息。

参数：
- `paper_id`：论文标识符，可以是Semantic Scholar Paper ID、DOI、arXiv ID等（必填）
- `fields`：指定返回的字段，逗号分隔

### 多篇论文详情
同时获取多篇论文的详细信息。

参数：
- `paper_ids`：论文标识符列表，可以是JSON数组或逗号分隔的值（必填）
- `fields`：指定返回的字段，逗号分隔

### 标题搜索
根据标题搜索论文。

参数：
- `title`：论文标题（必填）
- `year`：出版年份（可选）
- `fields`：指定返回的字段，逗号分隔

## 注意事项
- Semantic Scholar API有请求频率限制。使用API密钥可提高限制。
- 有关API的完整文档，请参考[Semantic Scholar API文档](https://api.semanticscholar.org/api-docs/)



