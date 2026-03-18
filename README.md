# 米奇妙妙工具

一个基于界外神兵打造的法宝，通过ai打包出来的
可以用来针对e站一些图片多但是没有上传种的漫画，由于我只有前端基础，网络方面一窍不通，目前程序运行流畅程度纯看你的梯子强度
本地测试多次没出什么问题，如果遇到问题感谢提出

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
