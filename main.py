import requests
from bs4 import BeautifulSoup

list_page_url = "https://cuiqingcai.com"
base_url = "https://cuiqingcai.com"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    # 1. 爬取列表页源码
    response = requests.get(list_page_url, headers=headers)
    response.raise_for_status()  # 捕获404、500等错误
    response.encoding = response.apparent_encoding  # 自动处理乱码
    soup = BeautifulSoup(response.text, "lxml")

    # 2. 批量定位所有标题标签（关键：用find_all替代find）
    all_title_tags = soup.find_all("a", class_="post-title-link")

    # 3. 遍历提取标题文本和完整链接
    if all_title_tags:
        print(f"共找到 {len(all_title_tags)} 篇文章的标题：\n")
        for idx, tag in enumerate(all_title_tags, 1):
            # 提取标题文本（去空格）
            title = tag.get_text().strip()
            # 提取并拼接完整链接（避免相对路径）
            full_link = requests.compat.urljoin(base_url, tag["href"])
            # 格式化输出
            print(f"{idx}. 标题：{title}")
            print(f"   链接：{full_link}\n")
    else:
        print("未找到任何文章标题，请检查标签特征或网页URL是否正确")

except Exception as e:
    print(f"爬取失败：{str(e)}")