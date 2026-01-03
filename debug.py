from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# 1. 사이트 접속
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://nol.interpark.com/ticket")

time.sleep(5)
soup = BeautifulSoup(driver.page_source, 'html.parser')

# 2. 첫 번째 공연 박스 가져오기
item = soup.select_one('.Ticket_Rank_Product')

if item:
    print("====== 🕵️‍♂️ 첫 번째 공연의 비밀 코드 분석 ======")
    print(f"1. 태그 이름: {item.name}")
    print(f"2. 가지고 있는 속성들(Attributes): {item.attrs}")
    print("\n3. 박스 안에 있는 내용물(HTML) 일부:")
    print(item.prettify()[:500]) # 앞부분 500글자만 출력
else:
    print("😢 공연 박스를 못 찾았어요.")

driver.quit()