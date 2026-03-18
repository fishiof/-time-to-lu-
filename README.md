# 神秘e站工具

一个用于爬取网页链接和下载图片的工具。

## 功能

- **步骤1**: 爬取网页链接
- **步骤2**: 提取图片URL
- **步骤3**: 下载图片
- **自动挡**: 一键执行所有步骤

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python web_link_crawler_ctk.py
```

## 打包成 exe

```bash
python -m PyInstaller --onefile --windowed --name "神秘e站工具" web_link_crawler_ctk.py
```

## 技术栈

- Python 3.14
- CustomTkinter (GUI)
- BeautifulSoup (网页解析)
- Requests (HTTP请求)
