import re
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation 
from openpyxl.utils.dataframe import dataframe_to_rows

# ======================================================
# 0. 날짜 정제 함수
# ======================================================
def clean_date_text(raw_text):
    if not raw_text:
        return ""
    # 1. 연도 제거 (숫자 4개 + 점) 예: 2025. -> 삭제
    text = re.sub(r'\d{4}\.', '', raw_text)
    # 2. 오전/오후 제거
    text = text.replace('오전', '').replace('오후', '')
    # 3. 앞뒤 공백 및 이중 공백 제거
    text = " ".join(text.split())
    return text

# ======================================================
# 1. 지역 분류 로직
# ======================================================
def parse_region(text):
    if not text: return "(기타)"
    clean_text = text.replace(" ", "").lower()
    
    if "국립정동극장" in clean_text: return "(서울)"
    if "코델아트홀" in clean_text: return "(서울)"
    if "yes24" in clean_text or "예스24" in clean_text: return "(서울)"
    if "당진" in clean_text: return "(충남)"
    
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

# ======================================================
# 2. 크롤링 실행
# ======================================================
save_dir = r"C:\Users\ddobi\Desktop\show"
file_name = "공연목록_오픈예정.xlsx"
full_path = os.path.join(save_dir, file_name)

if not os.path.exists(save_dir):
    os.makedirs(save_dir)

options = uc.ChromeOptions()
# options.add_argument('--headless') 

print(">> 브라우저를 실행합니다...")
driver = uc.Chrome(options=options)
final_results = [] 

base_url = "https://ticket.yes24.com/New/Notice/NoticeMain.aspx?Gcode=009_208_002"
page = 1 

try:
    while True:
        # [핵심 변경] 페이지 번호를 URL에 직접 포함시켜 이동
        target_url = f"{base_url}#page={page}"
        print(f"\n>> [Page {page}] 접속 중: {target_url}")
        
        driver.get(target_url)
        
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "tr")))
            time.sleep(2) 
        except:
            print(">> [경고] 페이지 로딩이 원활하지 않습니다.")

        if page == 1:
            try:
                print(">> [정렬] '오픈일순' 버튼 클릭 시도...")
                sort_button = driver.find_element(By.XPATH, "//*[contains(text(), '오픈일순')]")
                sort_button.click()
                print(">> [클릭] 완료. 목록 갱신 대기 (4초)...")
                time.sleep(4) 
            except:
                print(">> [Pass] 정렬 버튼을 못 찾았거나 이미 정렬됨.")

        print(f">> [Page {page}] 목록 스캔 중...")
        items_to_crawl = [] 
        
        # 목록 로딩 안정성 확보
        for _ in range(3):
            rows = driver.find_elements(By.TAG_NAME, "tr")
            if len(rows) > 5: break
            time.sleep(1)

        for row in rows:
            try:
                link_element = row.find_element(By.TAG_NAME, "a")
                link_url = link_element.get_attribute("href")
                
                if not link_url or "javascript" in link_url:
                    continue
                
                row_text = row.text.strip()
                is_exclusive = "" 
                
                if "단독" in row_text:
                    is_exclusive = "★"
                else:
                    try:
                        imgs = row.find_elements(By.TAG_NAME, "img")
                        for img in imgs:
                            if "단독" in img.get_attribute("alt"):
                                is_exclusive = "★"
                                break
                    except:
                        pass
                
                if not any(item['url'] == link_url for item in items_to_crawl):
                    items_to_crawl.append({
                        'url': link_url,
                        'is_exclusive': is_exclusive
                    })
            except:
                continue
        
        count = len(items_to_crawl)
        print(f">> [Page {page}] 수집 대상: {count}개")

        if count == 0:
            print(">> [종료] 게시물이 없습니다.")
            break

        print(f">> [Page {page}] 상세 데이터 추출 시작...")

        for idx, item in enumerate(items_to_crawl):
            url = item['url']
            is_exclusive = item['is_exclusive']

            print(f"   [{idx+1}/{count}] 분석 중...", end="\r")
            
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(random.uniform(0.5, 1.2)) 

                full_text = driver.find_element(By.TAG_NAME, "body").text
                
                # 변수 초기화
                title = ""
                open_date = ""
                place = ""
                region = ""
                genre = "" 
                poster_url = ""

                tokens = full_text.split("티켓오픈")
                
                # 1. 제목 
                if len(tokens) >= 2:
                    raw_title = tokens[1].strip().split('\n')[0].strip()
                    title = raw_title.replace("티켓 오픈 안내", "").replace("티켓오픈 안내", "").strip()

                # 2. 오픈일시
                for token in tokens[1:]:
                    cleaned_line = token.strip().split('\n')[0].strip()
                    if re.search(r'\d{4}\.\d{2}\.\d{2}', cleaned_line):
                        open_date = clean_date_text(cleaned_line) 
                        break 

                # 3. 장소
                if "공연 장소" in full_text:
                    place = full_text.split("공연 장소")[1].strip().split('\n')[0].replace(":", "").strip()
                elif "공연장소" in full_text:
                    place = full_text.split("공연장소")[1].strip().split('\n')[0].replace(":", "").strip()

                # 4. 지역
                combined_text = f"{place} {title}"
                region = parse_region(combined_text)

                # 5. 포스터
                try:
                    poster_img = driver.find_element(By.CSS_SELECTOR, ".view_con img")
                    poster_url = poster_img.get_attribute("src")
                except:
                    poster_url = ""

                final_results.append({
                    "단독": is_exclusive,
                    "오픈일시": open_date,
                    "지역": region, 
                    "제목": title,
                    "장소": place,
                    "장르": genre,
                    "링크": url,
                    "포스터": poster_url
                })

            except Exception as e:
                print(f"      -> [오류] {e}")
                continue
        
        print(f"\n   -> [완료] {count}개 데이터 확보함.")

        # [핵심 로직] 20개 미만이면 종료, 20개면 페이지 번호 증가
        if count < 20:
            print(f"\n>> [조건 달성] 게시물 {count}개(20개 미만) -> 마지막 페이지입니다.")
            break
        else:
            print(f"\n>> [진행] 게시물이 20개이므로 다음 페이지({page+1})로 넘어갑니다.")
            page += 1 
            time.sleep(2)

except Exception as e:
    print(f"\n[시스템 오류] {e}")

finally:
    print("-" * 50)
    print(f">> 총 {len(final_results)}건 수집 완료.")
    
    # [WinError 6 방지 및 안전 종료]
    print(">> 브라우저 종료 및 메모리 정리 중...")
    try:
        if driver:
            driver.quit()
    except:
        pass
    
    try:
        os.system("taskkill /f /im chrome.exe")
    except:
        pass

    # [Step 6] 엑셀 저장
    if len(final_results) > 0:
        try:
            print(f">> 엑셀 저장 시작: {full_path}")
            
            df = pd.DataFrame(final_results)
            cols = ["단독", "오픈일시", "지역", "제목", "장소", "장르", "링크", "포스터"]
            for col in cols:
                if col not in df.columns:
                    df[col] = ""
            df = df[cols]

            if os.path.exists(full_path):
                wb = openpyxl.load_workbook(full_path)
            else:
                wb = openpyxl.Workbook()
                wb.remove(wb.active)
                wb.create_sheet("Sheet1")
            
            # 두번째 시트(인덱스 1) 확보 및 덮어쓰기
            if len(wb.sheetnames) >= 2:
                ws = wb.worksheets[1] 
                if ws.max_row > 0:
                    ws.delete_rows(1, ws.max_row)
            else:
                ws = wb.create_sheet("Sheet2")

            for r in dataframe_to_rows(df, index=False, header=True):
                ws.append(r)

            # 장르 콤보박스 추가
            last_row = ws.max_row
            if last_row > 1:
                dv = DataValidation(
                    type="list", 
                    formula1='"콘서트,뮤지컬,연극,클래식,행사(전시),가족"', 
                    allow_blank=True
                )
                dv.error = '목록에서 선택해주세요'
                dv.errorTitle = '선택 오류'
                dv.add(f'F2:F{last_row}')
                ws.add_data_validation(dv)

            wb.save(full_path)
            print(f">> [성공] 저장 완료. 경로: {full_path}")
            print(f">> 두 번째 시트({ws.title})에 데이터를 덮어씌웠습니다.")
            
        except Exception as e:
            print(f">> [저장 실패] 오류: {e}")
            print(">> 엑셀 파일을 닫고 다시 실행해 주세요.")