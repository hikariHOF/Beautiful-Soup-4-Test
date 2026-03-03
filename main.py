from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import time
import random
import csv
import threading
import sys
import os


# 解决打包后Playwright找不到浏览器的问题
def get_playwright_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "playwright")
    else:
        return None


# 全局变量存储爬取结果
crawled_titles = []


class ToutiaoCrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("今日头条标题爬取工具 v1.0")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # 设置字体
        self.font_normal = ("微软雅黑", 10)
        self.font_bold = ("微软雅黑", 12, "bold")

        # 🔧 修复核心问题：为ttk组件配置样式（替代直接传font参数）
        self.style = ttk.Style()
        # 配置LabelFrame样式（标题字体）
        self.style.configure("Bold.TLabelframe.Label", font=self.font_bold)
        # 配置普通按钮样式
        self.style.configure("Accent.TButton", font=self.font_bold)
        # 配置普通标签/输入框样式
        self.style.configure("Normal.TLabel", font=self.font_normal)
        self.style.configure("Normal.TSpinbox", font=self.font_normal)
        self.style.configure("Normal.TCheckbutton", font=self.font_normal)

        # 1. 顶部配置区域（修复font参数问题）
        frame_config = ttk.LabelFrame(root, text="爬取配置", style="Bold.TLabelframe")
        frame_config.pack(padx=10, pady=10, fill=tk.X)

        # 滚动次数选择（指定样式）
        lbl_scroll = ttk.Label(frame_config, text="滚动加载次数：", style="Normal.TLabel")
        lbl_scroll.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.scroll_var = tk.StringVar(value="5")
        scroll_spin = ttk.Spinbox(frame_config, textvariable=self.scroll_var, width=10, style="Normal.TSpinbox")
        scroll_spin.grid(row=0, column=1, padx=5, pady=5)

        # 无头模式选择（指定样式）
        self.headless_var = tk.BooleanVar(value=True)
        chk_headless = ttk.Checkbutton(frame_config, text="后台运行（不显示浏览器）",
                                       variable=self.headless_var, style="Normal.TCheckbutton")
        chk_headless.grid(row=0, column=2, padx=10, pady=5)

        # 2. 按钮区域
        frame_buttons = ttk.Frame(root)
        frame_buttons.pack(padx=10, pady=5, fill=tk.X)

        self.btn_crawl = ttk.Button(frame_buttons, text="开始爬取",
                                    command=self.start_crawl_thread, style="Accent.TButton")
        self.btn_crawl.pack(side=tk.LEFT, padx=5)

        self.btn_export = ttk.Button(frame_buttons, text="导出结果到CSV",
                                     command=self.export_titles, state=tk.DISABLED, style="Accent.TButton")
        self.btn_export.pack(side=tk.LEFT, padx=5)

        self.btn_clear = ttk.Button(frame_buttons, text="清空日志",
                                    command=self.clear_log, style="Accent.TButton")
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        # 3. 日志显示区域（修复font参数）
        frame_log = ttk.LabelFrame(root, text="爬取日志", style="Bold.TLabelframe")
        frame_log.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(frame_log, font=self.font_normal, wrap=tk.WORD)
        self.log_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # 4. 底部状态栏
        self.status_var = tk.StringVar(value="就绪 - 等待开始爬取")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, style="Normal.TLabel")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def log(self, msg, level="info"):
        """日志输出"""
        color = {"info": "black", "success": "green", "error": "red", "warning": "orange"}
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.tag_add(level, self.log_text.index(tk.END + "-2l"), self.log_text.index(tk.END + "-1l"))
        self.log_text.tag_config(level, foreground=color.get(level, "black"))
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log("日志已清空", "info")

    def start_crawl_thread(self):
        """启动爬取线程"""
        self.btn_crawl.config(state=tk.DISABLED)
        self.btn_export.config(state=tk.DISABLED)
        self.status_var.set("运行中 - 正在初始化...")
        crawl_thread = threading.Thread(target=self.crawl_toutiao, daemon=True)
        crawl_thread.start()

    def crawl_toutiao(self):
        """核心爬取逻辑"""
        global crawled_titles
        crawled_titles = []
        scroll_times = int(self.scroll_var.get())
        headless = self.headless_var.get()

        try:
            self.log("开始初始化Playwright...", "info")
            with sync_playwright() as p:
                # 直接指定系统Edge的绝对路径（关键！）
                edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
                browser_kwargs = {
                    "executable_path": edge_path,  # 强制用系统Edge
                    "headless": headless,
                    "slow_mo": 800,
                }

                # 启动浏览器（去掉channel参数，避免冲突）
                browser = p.chromium.launch(**browser_kwargs)
                self.log("浏览器启动成功", "success")

                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
                    locale="zh-CN",
                    geolocation={"longitude": 116.403963, "latitude": 39.915119},
                    permissions=["geolocation"],
                    extra_http_headers={
                        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                        "Referer": "https://www.baidu.com/"
                    }
                )

                page = context.new_page()
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4] });
                    Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh'] });
                    delete window.navigator.webdriver;
                    window.chrome = { runtime: {} };
                """)

                self.log("正在访问今日头条首页...", "info")
                page.goto("https://www.toutiao.com/", timeout=60000, wait_until="networkidle")

                if "login" in page.url or "verify" in page.url:
                    self.log("检测到登录页面，请手动完成登录后继续...", "warning")
                    self.root.after(0, lambda: messagebox.showwarning("需要登录",
                                                                      "请在弹出的浏览器中完成登录，登录后点击确定继续！"))
                    time.sleep(15)
                    page.reload(wait_until="networkidle")
                    self.log("登录完成，继续爬取...", "success")

                self.log(f"开始滚动加载（共{scroll_times}次）...", "info")
                last_height = 0
                for i in range(scroll_times):
                    current_height = page.evaluate("document.body.scrollHeight")
                    if current_height == last_height:
                        self.log(f"第{i + 1}次滚动未加载新内容，停止滚动", "warning")
                        break
                    page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
                    wait_time = random.uniform(1.5, 3)
                    self.log(f"第{i + 1}次滚动，等待{wait_time:.1f}秒...", "info")
                    time.sleep(wait_time)
                    page.wait_for_selector("a[title]", timeout=5000)
                    last_height = current_height

                self.log("开始提取标题...", "info")
                page_source = page.content()
                soup = BeautifulSoup(page_source, 'html.parser')

                titles = []
                # 提取title属性
                title_links = soup.find_all('a', title=True)
                for link in title_links:
                    title = link.get('title', '').strip()
                    if title and len(title) > 5 and title not in titles:
                        titles.append(title)
                # 提取h3标签
                h3_tags = soup.find_all('h3')
                for tag in h3_tags:
                    title = tag.get_text(strip=True)
                    if title and len(title) > 5 and title not in titles:
                        titles.append(title)
                # 提取class含title
                class_title_tags = soup.find_all('a', class_=lambda x: x and 'title' in x)
                for tag in class_title_tags:
                    title = tag.get_text(strip=True)
                    if title and len(title) > 5 and title not in titles:
                        titles.append(title)

                # 过滤广告
                filter_keywords = ['广告', '下载', '安装', '推广', '关注', '充值', '秒杀', '特惠', '扫码', '点击']
                crawled_titles = [t for t in titles if not any(k in t for k in filter_keywords)]
                crawled_titles = list(set(crawled_titles))

                browser.close()
                self.log(f"爬取完成！共获取{len(crawled_titles)}个有效标题", "success")

                self.root.after(0, lambda: self.btn_crawl.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.btn_export.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.status_var.set(f"完成 - 共爬取{len(crawled_titles)}个标题"))

        except Exception as e:
            error_msg = f"爬取失败：{str(e)}"
            self.log(error_msg, "error")
            if 'page' in locals() and page:
                screenshot_path = os.path.join(os.getcwd(), "error_screenshot.png")
                page.screenshot(path=screenshot_path)
                self.log(f"错误截图已保存到：{screenshot_path}", "error")
            self.root.after(0, lambda: self.btn_crawl.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set("错误 - 爬取失败"))
            self.root.after(0, lambda: messagebox.showerror("爬取失败", error_msg))

    def export_titles(self):
        """导出标题到CSV"""
        if not crawled_titles:
            messagebox.showwarning("提示", "暂无爬取结果可导出！")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="保存标题结果",
            initialfile=f"今日头条标题_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["序号", "文章标题"])
                for idx, title in enumerate(crawled_titles, 1):
                    writer.writerow([idx, title])
            self.log(f"结果已成功导出到：{file_path}", "success")
            messagebox.showinfo("导出成功", f"共导出{len(crawled_titles)}个标题到：\n{file_path}")
        except Exception as e:
            self.log(f"导出失败：{str(e)}", "error")
            messagebox.showerror("导出失败", f"保存文件时出错：{str(e)}")


if __name__ == "__main__":
    # 高清适配
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    root = tk.Tk()
    app = ToutiaoCrawlerGUI(root)
    app.log("软件已启动，准备就绪！", "info")
    root.mainloop()