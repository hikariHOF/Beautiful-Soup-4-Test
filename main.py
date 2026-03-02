import requests # 导入网页请求库
from bs4 import BeautifulSoup # 导入网页解析库

# 传入URL
r = requests.get('https://www.csdn.net/')

# 解析URL
soup = BeautifulSoup(r.text, 'html.parser')
content_list = soup.find_all('div', attrs = {'class': 'title'})

for content in content_list:
    print(content.h2.a.text)