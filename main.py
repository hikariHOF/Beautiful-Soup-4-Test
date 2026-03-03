from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random


def get_toutiao_home_titles():
    """
    使用Playwright爬取今日头条首页标题（绕过Selenium网络限制）
    """
    titles = []
    # Playwright配置
    with sync_playwright() as p:
        # 启动Edge浏览器（非无头模式，方便调试）
        browser = p.chromium.launch(
            channel="msedge",  # 使用系统安装的Edge
            headless=True,  # 显示浏览器窗口
            slow_mo=1000,  # 放慢操作速度，模拟真人
        )

        # 创建上下文，模拟真实浏览器环境
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
            locale="zh-CN",
            geolocation={"longitude": 116.403963, "latitude": 39.915119},  # 北京坐标
            permissions=["geolocation"],
        )

        # 创建页面
        page = context.new_page()

        # 禁用自动化检测（Playwright自带更强的反检测）
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            delete window.navigator.languages;
            window.navigator.languages = ['zh-CN', 'zh'];
        """)

        try:
            # 访问今日头条首页
            print("正在访问今日头条首页...")
            page.goto("https://www.toutiao.com/", timeout=60000)  # 延长超时到60秒

            # 检查是否需要登录
            if "login" in page.url or "verify" in page.url:
                print("⚠️ 跳转到登录页，请手动完成登录后按Enter继续...")
                input("登录完成后按Enter键：")  # 暂停程序，等待手动登录
                page.reload()  # 重新加载页面

            # 模拟滚动加载更多内容
            print("正在加载更多文章...")
            for _ in range(3):
                # 平滑滚动到底部
                page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
                # 随机等待
                time.sleep(random.uniform(1.5, 3))

            # 获取页面完整源码
            page_source = page.content()
            soup = BeautifulSoup(page_source, 'html.parser')

            # 多维度提取标题
            # 1. 提取带title属性的a标签
            title_links = soup.find_all('a', title=True)
            for link in title_links:
                title = link.get('title').strip()
                if title and len(title) > 5 and title not in titles:
                    titles.append(title)

            # 2. 提取h3标签的标题
            h3_tags = soup.find_all('h3')
            for tag in h3_tags:
                title = tag.get_text(strip=True)
                if title and len(title) > 5 and title not in titles:
                    titles.append(title)

            # 3. 提取class含title的元素
            class_title_tags = soup.find_all('a', class_=lambda x: x and 'title' in x)
            for tag in class_title_tags:
                title = tag.get_text(strip=True)
                if title and len(title) > 5 and title not in titles:
                    titles.append(title)

            # 过滤广告标题
            filter_keywords = ['广告', '下载', '安装', '推广', '关注', '充值']
            valid_titles = [t for t in titles if not any(k in t for k in filter_keywords)]

            return valid_titles

        except Exception as e:
            print(f"爬取失败：{str(e)}")
            # 保存页面截图，方便调试
            page.screenshot(path="error_screenshot.png")
            print("已保存错误截图到 error_screenshot.png")
            return []
        finally:
            # 关闭浏览器
            browser.close()


# 主程序
if __name__ == "__main__":
    print("=" * 60)
    print("使用Playwright爬取今日头条首页标题")
    print("=" * 60)

    # 爬取标题
    all_titles = get_toutiao_home_titles()

    # 输出结果
    if all_titles:
        print(f"\n 成功爬取到 {len(all_titles)} 个有效标题：")
        print("-" * 50)
        for idx, title in enumerate(all_titles[:20], 1):
            print(f"{idx}. {title}")
        if len(all_titles) > 20:
            print(f"... 共 {len(all_titles)} 个标题，仅显示前20个")
    else:
        print("\n 仍未爬取到标题，请尝试：")
        print("  1. 关闭防火墙/杀毒软件后重试")
        print("  2. 使用手机热点替换当前网络")
        print("  3. 以管理员身份运行Python程序")