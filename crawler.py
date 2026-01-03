from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import re

# ======================================================
# 1. 지역/도시 매핑 로직
# ======================================================
def parse_region(text):
    if not text: return "(기타)"
    clean_text = text.replace(" ", "").lower()
    
    if "서울" in clean_text or "seoul" in clean_text: return "(서울)"
    if "부산" in clean_text or "busan" in clean_text: return "(부산)"
    if "대구" in clean_text or "daegu" in clean_text: return "(대구)"
    if "인천" in clean_text or "incheon" in clean_text: return "(인천)"
    if "대전" in clean_text or "daejeon" in clean_text: return "(대전)"
    if "울산" in clean_text or "ulsan" in clean_text: return "(울산)"
    if "세종" in clean_text or "sejong" in clean_text: return "(세종)"
    if "제주" in clean_text or "jeju" in clean_text: return "(제주)"
    
    if "광주" in clean_text:
        if "경기" in clean_text: return "(경기)"
        return "(광주)"

    gyeonggi_cities = [
        "수원", "성남", "의정부", "안양", "부천", "광명", "평택", "안산", "고양", "일산", 
        "과천", "구리", "남양주", "오산", "시흥", "군포", "의왕", "하남", "용인", "파주", 
        "이천", "김포", "화성", "광주", "양주", "포천", "여주", "연천", "가평", "양평", 
        "킨텍스", "kintex", "아람누리", "어울림"
    ]
    if any(c in clean_text for c in gyeonggi_cities): return "(경기)"

    if any(c in clean_text for c in ["춘천", "원주", "강릉", "속초", "동해", "태백", "삼척"]): return "(강원)"
    if any(c in clean_text for c in ["청주", "충주", "제천"]): return "(충북)"
    if any(c in clean_text for c in ["천안", "공주", "보령", "아산", "당진", "서산", "논산"]): return "(충남)"
    if any(c in clean_text for c in ["전주", "군산", "익산", "정읍", "남원"]): return "(전북)"
    if any(c in clean_text for c in ["목포", "여수", "순천", "광양", "나주"]): return "(전남)"
    if any(c in clean_text for c in ["포항", "경주", "김천", "안동", "구미", "영주", "영천", "상주", "문경", "경산"]): return "(경북)"
    if any(c in clean_text for c in ["창원", "진주", "통영", "사천", "김해", "밀양", "거제", "양산", "벡스코", "bexco"]): return "(경남)"

    seoul_venues = [
        "링크아트센터", "드림아트센터", "대학로", "혜화", "예술의전당", "세종문화", 
        "롯데콘서트", "블루스퀘어", "잠실", "올림픽공원", "코엑스", "디큐브", "샤롯데", 
        "lg아트", "충무아트", "국립극장", "한전아트", "마포", "유니플렉스", "예스24", 
        "kt&g", "홍대", "성수", "강남", "명화라이브", "tom", "플러스씨어터", "아트원", "자유극장"
    ]
    if any(v in clean_text for v in seoul_venues): return "(서울)"

    if "경기" in clean_text: return "(경기)"
    if "강원" in clean_text: return "(강원)"
    if "충북" in clean_text: return "(충북)"
    if "충남" in clean_text: return "(충남)"
    if "전북" in clean_text: return "(전북)"
    if "전남" in clean_text: return "(전남)"
    if "경북" in clean_text: return "(경북)"
    if "경남" in clean_text: return "(경남)"

    return "(기타)"

def get_address_from_map(driver, place_name):
    # (지도 검색 기능 유지)
    try:
        url = f"https://map.naver.com/p/search/{place_name}"
        driver.get(url)
        time.sleep(1.5)
        try:
            driver.switch_to.default_content()
            iframe = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "searchIframe")))
            driver.switch_to.frame(iframe)
            return driver.find_element(By.TAG_NAME, "body").text
        except: return ""
    except: return ""
    finally: driver.switch_to.default_content()

# ======================================================
# 2. 크롤링 실행
# ======================================================
options = webdriver.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://tickets.interpark.com/contents/notice"
driver.get(url)

print("====== ⏳ 데이터 수집 및 분류 중... ======")
time.sleep(5)

ticket_list = []

try:
    wait = WebDriverWait(driver, 20)
    
    # 1. 오픈순 필터 클릭
    try:
        filter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '오픈순')]")))
        driver.execute_script("arguments[0].scrollIntoView();", filter_el)
        filter_el.click()
        time.sleep(3)
    except:
        pass

    collected_titles = set()

    # 2. 스크롤 10번 (데이터 로딩)
    for _ in range(10): 
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(1)
    
    # 3. [핵심 변경] 텍스트 전체 스캔 대신 개별 아이템(li) 추출 방식 사용
    # 이렇게 해야 날짜 형식이 다른 '내일' 데이터도 놓치지 않음
    items = driver.find_elements(By.CSS_SELECTOR, "div.boardList ul li")
    
    print(f"====== 📌 총 {len(items)}개의 공지사항 발견. 분석 시작... ======")

    for item in items:
        try:
            raw_text = item.text
            if not raw_text: continue

            # --- 데이터 파싱 로직 ---
            lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
            
            # 조건 1: 날짜 패턴(00.00)이 있는 경우
            date_match = re.search(r'(\d{2}\.\d{2}\(.\)\s\d{2}:\d{2})', raw_text)
            
            # 조건 2: '내일'이라는 글자가 있는 경우
            has_tomorrow = '내일' in raw_text

            if not date_match and not has_tomorrow:
                continue # 둘 다 아니면 패스 (광고 등)

            open_date = ""
            if date_match:
                open_date = date_match.group(1)
            elif has_tomorrow:
                open_date = "" # '내일'이면 빈칸으로 둠

            # 제목 찾기 (보통 첫 번째 줄)
            title = lines[0]
            
            # 장소 찾기
            location = "장소 미정"
            for line in lines:
                # 제목 아니고, 날짜(있다면) 아니고, '조회'/'내일' 아닌 줄이 장소
                if line != title and "조회" not in line and "내일" not in line:
                    if open_date and open_date in line: continue
                    if len(line) > 1:
                        location = line
                        break
            
            # 필터링
            if location.strip() in ["다음", "이전", "맨처음", "맨끝", "TOP", "목록"]: continue
            if "추후공지" in title or "추후공지" in location: continue
            if "티켓" in title and "안내" in title: continue 
            
            if title not in collected_titles:
                ticket_list.append({
                    '오픈일시': open_date,
                    '지역': '', 
                    '제목': title,
                    '장소': location,
                    '장르': '선택',
                    '링크': '',    # 빈칸
                    '포스터': ''   # 빈칸
                })
                collected_titles.add(title)
                # print(f"✅ 추가됨: {title[:10]}...")

        except Exception as e:
            continue

    print(f"====== ✅ 1단계 완료! 총 {len(ticket_list)}건. 지역 검증 시작... ======")

    place_cache = {} 
    for idx, item in enumerate(ticket_list):
        place = item['장소']
        title = item['제목']
        region = "(기타)"
        
        if place in place_cache:
            region = place_cache[place]
        else:
            full_text = place + " " + title
            temp_region = parse_region(full_text)
            
            if temp_region != "(기타)":
                region = temp_region
                if "의정부" in place or "안산" in place:
                    print(f"⚡ [확인] {place} -> {region}")
            else:
                region = temp_region
            place_cache[place] = region
        
        item['지역'] = region

    # ======================================================
    # 3. 엑셀 저장
    # ======================================================
    if ticket_list:
        df = pd.DataFrame(ticket_list)
        # 오픈일시 기준 정렬 (빈칸은 맨 위나 아래로 갈 수 있음)
        df = df.sort_values(by='오픈일시', ascending=True)
        
        # [요청하신 열 순서]
        df = df[['오픈일시', '지역', '제목', '장소', '장르', '링크', '포스터']]
        
        output_file = '공연목록_오픈예정.xlsx'
        
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sheet1')

        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        genre_options = ['콘서트', '뮤지컬', '연극', '클래식', '행사(전시)', '가족']
        last_row = len(df) + 1
        
        worksheet.data_validation(f'E2:E{last_row}', {
            'validate': 'list',
            'source': genre_options,
            'input_title': '장르 선택',
            'input_message': '목록에서 장르를 선택해주세요.'
        })

        # 열 너비 조정
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 8)
        worksheet.set_column('C:C', 45)
        worksheet.set_column('D:D', 30)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 15) # 링크
        worksheet.set_column('G:G', 15) # 포스터

        writer.close()
        print(f"\n🎉 저장 완료! '{output_file}'")
        print(f"   - '내일' 포함 데이터 수집 완료 (오픈일시 빈칸)")
        print(f"   - '링크', '포스터' 열 추가됨 (빈칸)")
    else:
        print("\n😢 데이터를 찾지 못했습니다.")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
finally:
    driver.quit()