import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import configparser
import customtkinter as ctk
from tkinter import messagebox, filedialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

log_callback = None

def log(message):
    print(message)
    if log_callback:
        log_callback(message)

class WebLinkCrawler:
    def __init__(self, config_file='config.ini'):
        self.config = self.load_config(config_file)
        self.timeout = int(self.config.get('General', 'timeout', fallback='10'))
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def load_config(self, config_file):
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file, encoding='utf-8')
        return config
    
    def get_page_content(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except Exception as e:
            log(f"获取网页失败: {e}")
            return None
    
    def extract_links(self, html_content, base_url):
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        target_element = soup.find('div', class_='gt200')
        
        if not target_element:
            log("未找到class为gt200的div元素")
            return []
        
        log("找到class为gt200的div元素")
        
        for a_element in target_element.find_all('a'):
            href = a_element.get('href', '')
            if href:
                full_url = urljoin(base_url, href)
                link_info = {
                    'href': full_url,
                    'text': a_element.get_text(strip=True)
                }
                links.append(link_info)
        
        log(f"找到 {len(links)} 个链接")
        return links
    
    def extract_title(self, html_content, title_type='translated'):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if title_type == 'translated':
            title_element = soup.find('h1', id='gn')
            if title_element:
                title = title_element.get_text(strip=True)
                log(f"获取到翻译后标题: {title}")
                return title
            else:
                log("标题获取失败将为你更换成原标题")
                title_element = soup.find('h1', id='gj')
                if title_element:
                    title = title_element.get_text(strip=True)
                    log(f"获取到原标题: {title}")
                    return title
                else:
                    log("未找到任何标题")
                    return None
        else:
            title_element = soup.find('h1', id='gj')
            if title_element:
                title = title_element.get_text(strip=True)
                log(f"获取到原标题: {title}")
                return title
            else:
                log("未找到原标题")
                return None
    
    def display_links(self, all_links):
        result_text = "链接信息:\n"
        result_text += "=" * 50 + "\n\n"
        
        for i, link in enumerate(all_links, 1):
            result_text += f"链接 {i}:\n"
            result_text += f"  URL: {link['href']}\n"
            if link['text']:
                text_preview = link['text'][:50] + "..." if len(link['text']) > 50 else link['text']
                result_text += f"  文本: {text_preview}\n"
            result_text += "-" * 30 + "\n\n"
        
        result_text += "=" * 50 + "\n"
        result_text += f"总计: {len(all_links)} 个链接\n"
        
        return result_text
    
    def extract_images_from_page(self, url):
        html_content = self.get_page_content(url)
        if not html_content:
            log(f"获取页面失败: {url}")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        images = []
        
        target_element = soup.find('div', id='i3')
        
        if not target_element:
            log(f"未找到id为i3的div元素: {url}")
            return []
        
        log(f"找到id为i3的div元素: {url}")
        
        for img_element in target_element.find_all('img'):
            src = img_element.get('src', '')
            if src:
                full_url = urljoin(url, src)
                images.append(full_url)
        
        log(f"找到 {len(images)} 张图片")
        return images

class ProgressWindow:
    def __init__(self, parent):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("执行进度")
        self.window.geometry("750x550")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.lift()
        self.window.focus_force()
        self.execute_callback = None
        self.url_var = ctk.StringVar()
        
        self.url_frame = ctk.CTkFrame(self.window)
        self.url_frame.pack(fill="x", padx=15, pady=15)
        
        url_label = ctk.CTkLabel(self.url_frame, text="URL:", font=("Microsoft YaHei", 12))
        url_label.pack(side="left", padx=10)
        
        self.url_entry = ctk.CTkEntry(self.url_frame, textvariable=self.url_var, width=450, height=35, font=("Microsoft YaHei", 11))
        self.url_entry.pack(side="left", padx=10, fill="x", expand=True)
        
        self.execute_btn = ctk.CTkButton(self.url_frame, text="执行", command=self._on_execute, width=80, height=35, fg_color="#2ecc71", hover_color="#27ae60", font=("Microsoft YaHei", 12, "bold"))
        self.execute_btn.pack(side="left", padx=10)
        
        self.step_label = ctk.CTkLabel(self.window, text="当前步骤: 无", font=("Microsoft YaHei", 13, "bold"))
        self.step_label.pack(pady=10)
        
        self.text_area = ctk.CTkTextbox(self.window, wrap="word", font=("Consolas", 11))
        self.text_area.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.close_btn = ctk.CTkButton(self.window, text="关闭", command=self.window.destroy, width=120, height=35, font=("Microsoft YaHei", 12))
        self.close_btn.pack(pady=10)
    
    def hide_url_input(self):
        self.url_frame.pack_forget()
    
    def set_execute_callback(self, callback):
        self.execute_callback = callback
    
    def _on_execute(self):
        if self.execute_callback:
            url = self.url_var.get().strip()
            self.execute_callback(url)
    
    def get_url(self):
        return self.url_var.get().strip()
    
    def update_step(self, step_text):
        self.step_label.configure(text=f"当前步骤: {step_text}")
        self.window.update()
    
    def log(self, message):
        self.text_area.insert("end", message + "\n")
        self.text_area.see("end")
        self.window.update()

class StepSelectionDialog:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("神秘e站工具")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        self.result = {'step': -1, 'custom_file': None, 'progress_window': None, 'executed': False}
        
        self.setup_ui()
    
    def setup_ui(self):
        title_label = ctk.CTkLabel(self.root, text="神秘e站工具", font=("Microsoft YaHei", 22, "bold"))
        title_label.pack(pady=15)
        
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        left_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        left_title = ctk.CTkLabel(left_frame, text="手动挡", font=("Microsoft YaHei", 16, "bold"), text_color="#3498db")
        left_title.pack(pady=10)
        
        btn1 = ctk.CTkButton(left_frame, text="步骤1: 爬取链接", 
                             command=lambda: self.on_select(1), width=220, height=40, font=("Microsoft YaHei", 12))
        btn1.pack(pady=8)
        
        frame2 = ctk.CTkFrame(left_frame, fg_color="transparent")
        frame2.pack(pady=8)
        btn2 = ctk.CTkButton(frame2, text="步骤2: 提取图片URL", 
                             command=lambda: self.on_select(2), width=150, height=40, font=("Microsoft YaHei", 11))
        btn2.pack(side="left", padx=3)
        btn2_custom = ctk.CTkButton(frame2, text="选择文件", 
                                    command=self.select_file_for_step2, width=80, height=40, font=("Microsoft YaHei", 10))
        btn2_custom.pack(side="left", padx=3)
        
        frame3 = ctk.CTkFrame(left_frame, fg_color="transparent")
        frame3.pack(pady=8)
        btn3 = ctk.CTkButton(frame3, text="步骤3: 下载图片", 
                             command=lambda: self.on_select(3), width=150, height=40, font=("Microsoft YaHei", 11))
        btn3.pack(side="left", padx=3)
        btn3_custom = ctk.CTkButton(frame3, text="选择文件", 
                                    command=self.select_file_for_step3, width=80, height=40, font=("Microsoft YaHei", 10))
        btn3_custom.pack(side="left", padx=3)
        
        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True, padx=10)
        
        right_title = ctk.CTkLabel(right_frame, text="自动挡", font=("Microsoft YaHei", 16, "bold"), text_color="#e74c3c")
        right_title.pack(pady=10)
        
        btn_all = ctk.CTkButton(right_frame, text="执行所有步骤", 
                                command=lambda: self.on_select(0), width=220, height=60, 
                                fg_color="#e74c3c", hover_color="#c0392b", font=("Microsoft YaHei", 13, "bold"))
        btn_all.pack(pady=30)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_select(self, step, custom_file=None):
        self.result['step'] = step
        self.result['custom_file'] = custom_file
        self.result['progress_window'] = ProgressWindow(self.root)
        self.result['progress_window'].set_execute_callback(
            lambda url: self.on_execute(url, self.result['progress_window'], step, custom_file)
        )
        
        if step == 2 or step == 3:
            self.result['progress_window'].hide_url_input()
            self.on_execute(None, self.result['progress_window'], step, custom_file)
    
    def on_execute(self, url, progress_window, selected_step, custom_file):
        global log_callback
        log_callback = progress_window.log
        
        if selected_step == 0 or selected_step == 1:
            if not url:
                log("未输入URL，程序退出")
                return
        
        self.result['executed'] = True
        
        crawler = WebLinkCrawler()
        
        try:
            if selected_step == 0 or selected_step == 1:
                title_type = self.show_title_type_dialog()
                
                if title_type == -1:
                    log("用户取消操作，程序退出")
                    return
                
                progress_window.update_step("步骤1: 爬取链接")
                if not step1_crawl_links_with_url(crawler, url, title_type):
                    return
            
            if selected_step == 0 or selected_step == 2:
                if os.path.exists('title.txt'):
                    with open('title.txt', 'r', encoding='utf-8') as f:
                        title = f.read().strip()
                    if title:
                        images_file = f"{title}_images.txt"
                        if os.path.exists(images_file):
                            os.remove(images_file)
                            log(f"已清除 {images_file}")
                
                progress_window.update_step("步骤2: 提取图片URL")
                step2_extract_images(crawler, custom_file)
            
            if selected_step == 0 or selected_step == 3:
                progress_window.update_step("步骤3: 下载图片")
                step3_download_images(custom_file)
            
            log("\n程序执行完成！")
            
        except KeyboardInterrupt:
            log("\n用户中断爬取")
        except Exception as e:
            log(f"程序出错: {e}")
            messagebox.showerror("错误", f"程序出错: {e}")
    
    def show_title_type_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("选择标题类型")
        dialog.geometry("360x220")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        selected_type = ctk.IntVar(value=-1)
        
        def on_select(title_type):
            selected_type.set(title_type)
            dialog.destroy()
        
        def on_close():
            selected_type.set(-1)
            dialog.destroy()
        
        dialog.protocol("WM_DELETE_WINDOW", on_close)
        
        label = ctk.CTkLabel(dialog, text="请选择标题类型:", font=("Microsoft YaHei", 14))
        label.pack(pady=20)
        
        btn1 = ctk.CTkButton(dialog, text="获取翻译后标题", 
                             command=lambda: on_select(1), width=250, height=40, font=("Microsoft YaHei", 12))
        btn1.pack(pady=10)
        
        btn2 = ctk.CTkButton(dialog, text="获取原标题", 
                             command=lambda: on_select(2), width=250, height=40, font=("Microsoft YaHei", 12))
        btn2.pack(pady=10)
        
        dialog.wait_window()
        return selected_type.get()
    
    def select_file_for_step2(self):
        file_path = filedialog.askopenfilename(
            title="选择链接文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.on_select(2, file_path)
    
    def select_file_for_step3(self):
        file_path = filedialog.askopenfilename(
            title="选择图片URL文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.on_select(3, file_path)
    
    def on_close(self):
        self.result['step'] = -1
        self.root.destroy()
    
    def show(self):
        self.root.mainloop()
        return self.result['step'], self.result['custom_file'], self.result['progress_window']

def save_links_to_file(links, filename='links.txt'):
    with open(filename, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(link['href'] + '\n')
    log(f"已将 {len(links)} 个链接保存到 {filename}")

def save_images_to_file(images, filename='images.txt'):
    with open(filename, 'w', encoding='utf-8') as f:
        for image in images:
            f.write(image + '\n')
    log(f"已将 {len(images)} 个图片URL保存到 {filename}")

def crawl_images_from_links(crawler, links_filename='links.txt', images_filename='images.txt'):
    if not os.path.exists(links_filename):
        log(f"未找到 {links_filename} 文件")
        return []
    
    with open(links_filename, 'r', encoding='utf-8') as f:
        links = [line.strip() for line in f if line.strip()]
    
    log(f"从 {links_filename} 中读取到 {len(links)} 个链接")
    
    all_images = []
    
    for i, link in enumerate(links, 1):
        log(f"\n处理第 {i}/{len(links)} 个链接: {link}")
        images = crawler.extract_images_from_page(link)
        all_images.extend(images)
    
    if all_images:
        save_images_to_file(all_images, images_filename)
        log(f"\n总共提取 {len(all_images)} 个图片URL")
    
    return all_images

def download_with_retry(image_urls, download_dir, headers, max_retries=6):
    downloaded_count = 0
    failed_count = 0
    downloaded_urls = set()
    
    for i, image_url in enumerate(image_urls, 1):
        if image_url in downloaded_urls:
            log(f"\n跳过重复URL: {image_url}")
            continue
        
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                log(f"\n下载第 {i}/{len(image_urls)} 张图片 (尝试 {retry_count + 1}/{max_retries}): {image_url}")
                
                from urllib.parse import urlparse as url_parse
                parsed_url = url_parse(image_url)
                referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"
                
                download_headers = headers.copy()
                download_headers['Referer'] = referer
                
                response = requests.get(image_url, headers=download_headers, timeout=30, proxies={'http': None, 'https': None})
                response.raise_for_status()
                
                filename = os.path.basename(urlparse(image_url).path)
                if not filename:
                    filename = f"image_{i}.jpg"
                
                filepath = os.path.join(download_dir, filename)
                counter = 1
                while os.path.exists(filepath):
                    name, ext = os.path.splitext(filename)
                    filepath = os.path.join(download_dir, f"{name}_{counter}{ext}")
                    counter += 1
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                log(f"已保存: {filepath}")
                downloaded_count += 1
                downloaded_urls.add(image_url)
                success = True
                
            except Exception as e:
                log(f"下载失败: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    log(f"将在 {retry_count} 秒后重试...")
                    import time
                    time.sleep(retry_count)
        
        if not success:
            failed_count += 1
    
    return downloaded_count, failed_count

def download_images_from_file(images_filename='images.txt', download_dir='images'):
    if not os.path.exists(images_filename):
        log(f"未找到 {images_filename} 文件")
        return
    
    with open(images_filename, 'r', encoding='utf-8') as f:
        image_urls = [line.strip() for line in f if line.strip()]
    
    log(f"从 {images_filename} 中读取到 {len(image_urls)} 个图片URL")
    
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        log(f"创建下载目录: {download_dir}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-site',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    log(f"\n开始下载图片...")
    
    downloaded_count, failed_count = download_with_retry(image_urls, download_dir, headers)
    
    log(f"\n下载完成: 成功 {downloaded_count} 张, 失败 {failed_count} 张")
    log(f"图片保存在: {os.path.abspath(download_dir)}")

def step1_crawl_links_with_url(crawler, url, title_type):
    try:
        all_links = []
        page_count = 0
        current_url = url
        previous_links = []
        title = None
        
        while True:
            log(f"\n开始爬取第 {page_count + 1} 页: {current_url}")
            
            html_content = crawler.get_page_content(current_url)
            if not html_content:
                log("获取网页内容失败")
                break
            
            if page_count == 0 and title is None:
                if title_type == 1:
                    title = crawler.extract_title(html_content, 'translated')
                else:
                    title = crawler.extract_title(html_content, 'original')
            
            links = crawler.extract_links(html_content, current_url)
            if not links:
                log(f"第 {page_count + 1} 页没有找到符合条件的链接，停止爬取")
                break
            
            all_links.extend(links)
            log(f"第 {page_count + 1} 页找到 {len(links)} 个链接")
            
            page_count += 1
            
            if page_count == 1:
                if '?' in current_url:
                    next_url = current_url + '&p=1'
                else:
                    next_url = current_url + '?p=1'
            else:
                if '?p=' in current_url:
                    next_url = current_url.replace(f'?p={page_count-1}', f'?p={page_count}')
                else:
                    next_url = current_url + f'?p={page_count}'
            
            current_url = next_url
            
            if previous_links:
                current_links_set = set(link['href'] for link in links)
                previous_links_set = set(link['href'] for link in previous_links)
                if current_links_set == previous_links_set:
                    log("连续两次获取到的链接相同，停止爬取")
                    break
            
            previous_links = links
        
        if all_links:
            log(f"\n总共爬取 {len(all_links)} 个链接，来自 {page_count} 个页面")
            
            if title:
                invalid_chars = '<>:"/\\|?*'
                for char in invalid_chars:
                    title = title.replace(char, '_')
                
                with open('title.txt', 'w', encoding='utf-8') as f:
                    f.write(title)
                log(f"标题已保存: {title}")
                
                links_filename = f"{title}_links.txt"
                
                if os.path.exists(links_filename):
                    os.remove(links_filename)
                    log(f"已删除旧文件: {links_filename}")
                
                save_links_to_file(all_links, links_filename)
            else:
                save_links_to_file(all_links)
            
            return True
        else:
            log("没有找到任何链接")
            return False
            
    except Exception as e:
        log(f"步骤1出错: {e}")
        messagebox.showerror("错误", f"步骤1出错: {e}")
        return False

def step2_extract_images(crawler, custom_file=None):
    try:
        log("\n开始从链接中提取图片URL...")
        
        if custom_file:
            log(f"使用自定义文件: {custom_file}")
            links_filename = custom_file
        else:
            if os.path.exists('title.txt'):
                with open('title.txt', 'r', encoding='utf-8') as f:
                    title = f.read().strip()
                if title:
                    links_filename = f"{title}_links.txt"
                else:
                    links_filename = "links.txt"
            else:
                links_filename = "links.txt"
        
        if os.path.exists('title.txt'):
            with open('title.txt', 'r', encoding='utf-8') as f:
                title = f.read().strip()
            if title:
                images_filename = f"{title}_images.txt"
                if os.path.exists(images_filename):
                    os.remove(images_filename)
                    log(f"已删除旧文件: {images_filename}")
            else:
                images_filename = "images.txt"
        else:
            images_filename = "images.txt"
        
        crawl_images_from_links(crawler, links_filename=links_filename, images_filename=images_filename)
        return True
    except Exception as e:
        log(f"步骤2出错: {e}")
        messagebox.showerror("错误", f"步骤2出错: {e}")
        return False

def step3_download_images(custom_file=None):
    try:
        log("\n开始下载图片...")
        
        if custom_file:
            log(f"使用自定义文件: {custom_file}")
            images_filename = custom_file
        else:
            if os.path.exists('title.txt'):
                with open('title.txt', 'r', encoding='utf-8') as f:
                    title = f.read().strip()
                if title:
                    images_filename = f"{title}_images.txt"
                else:
                    images_filename = "images.txt"
            else:
                images_filename = "images.txt"
        
        download_images_from_file(images_filename=images_filename)
        
        if os.path.exists('title.txt'):
            with open('title.txt', 'r', encoding='utf-8') as f:
                title = f.read().strip()
            
            if title and os.path.exists('images'):
                new_folder_name = title
                counter = 1
                while os.path.exists(new_folder_name):
                    new_folder_name = f"{title}_{counter}"
                    counter += 1
                
                os.rename('images', new_folder_name)
                log(f"\n文件夹已重命名为: {new_folder_name}")
        
        return True
    except Exception as e:
        log(f"步骤3出错: {e}")
        messagebox.showerror("错误", f"步骤3出错: {e}")
        return False

def main():
    global log_callback
    
    dialog = StepSelectionDialog()
    selected_step, custom_file, progress_window = dialog.show()
    
    if selected_step == -1 or progress_window is None:
        print("用户取消操作，程序退出")
        return
    
    log_callback = progress_window.log
    
    if selected_step == 1:
        progress_window.update_step("步骤1: 爬取链接 - 请在上方输入URL并点击执行")
        log("请在上方输入URL并点击执行按钮")
    
    elif selected_step == 0:
        progress_window.update_step("执行所有步骤 - 请在上方输入URL并点击执行")
        log("请在上方输入URL并点击执行按钮")

if __name__ == "__main__":
    main()
