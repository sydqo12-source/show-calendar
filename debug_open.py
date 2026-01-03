from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# 1. 설정 및 접속
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://nol.interpark.com/ticket")

print("====== ⏳ 사이트 접속 및 탭 이동 중... ======")
time.sleep(3)

try:
    # 2. '티켓오픈' 탭 클릭
    open_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '티켓오픈')]"))
    )
    open_tab.click()
    time.sleep(5) # 충분히 기다림

    # 3. HTML 분석
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    print("\n====== 🕵️‍♂️ 화면 분석 결과 ======")
    
    # 전략: "오픈" 또는 ":" (시간 표시)가 들어있는 태그를 찾아서 부모를 추적함
    # 보통 날짜/시간은 '09:00' 처럼 나오므로 ':'를 찾아봅니다.
    samples = soup.find_all(string=lambda text: text and ":" in text and ("09" in text or "10" in text or "11" in text or "14" in text))
    
    if len(samples) > 0:
        print(f"✅ 시간으로 추정되는 텍스트 {len(samples)}개를 찾았습니다!")
        
        # 첫 번째 단서 분석
        target_text = samples[0]
        parent = target_text.parent
        grandparent = parent.parent
        
        print(f"\n1. 발견된 텍스트: '{target_text.strip()}'")
        print(f"2. 감싸고 있는 태그(Parent): <{parent.name} class='{parent.get('class')}' ...>")
        print(f"3. 그 위의 상자(Grandparent): <{grandparent.name} class='{grandparent.get('class')}' ...>")
        
        # 상위 리스트 아이템 추적
        list_item = parent.find_parent('li')
        if list_item:
            print(f"4. 전체 리스트 아이템(LI): <li class='{list_item.get('class')}'>")
        else:
            div_item = parent.find_parent('div', class_=lambda x: x and 'Item' in x)
            if div_item:
                print(f"4. 전체 리스트 아이템(DIV): <div class='{div_item.get('class')}'>")
            else:
                print("4. 리스트 아이템(li/div)을 못 찾음. 구조가 특이함.")

    else:
        print("😢 '시간(:)' 텍스트를 못 찾았습니다. 페이지가 로딩되지 않았거나 텍스트가 그림일 수 있습니다.")
        print("Body 태그 앞부분 500자:", soup.body.text[:500].strip())

except Exception as e:
    print(f"❌ 오류 발생: {e}")

driver.quit()