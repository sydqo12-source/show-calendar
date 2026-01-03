import pandas as pd
import calendar
import os
import webbrowser
import subprocess

# ==========================================
# [설정]
# ==========================================
YEAR = 2026
MONTH = 1

GENRE_ORDER = ["콘서트", "뮤지컬", "연극", "클래식", "행사(전시)", "가족"]

COLOR_SEOUL = "#e03131"
COLOR_GYEONGGI = "#e03131"
COLOR_OTHERS = "#1971c2"

LAYOUT_TOP_LEFT = "시간"
LAYOUT_TOP_RIGHT = "지역"
LAYOUT_BOTTOM = "제목"

FONT_SIZE = 11
# ==========================================

def get_day(x):
    try: return int(str(x).split('(')[0].split('.')[1])
    except: return 0

def get_content_html(selection_type, row_data):
    region = str(row_data['지역'])
    title = str(row_data['제목'])
    place = str(row_data['장소'])
    genre = str(row_data['장르'])
    time_txt = str(row_data['오픈일시']).split(' ')[-1] if ' ' in str(row_data['오픈일시']) else ''

    if "(서울)" in region: color = COLOR_SEOUL
    elif "(경기)" in region or "(인천)" in region: color = COLOR_GYEONGGI
    else: color = COLOR_OTHERS

    if "시간" in selection_type:
        return f'<span style="color:#212529; font-weight:800;">{time_txt}</span>'
    elif "지역" in selection_type:
        return f'<span style="color:{color}; font-weight:800;">{region}</span>'
    elif "제목" in selection_type:
        return f'<span style="color:#495057; font-weight:500;">{title}</span>'
    elif "장소" in selection_type:
        return f'<span style="color:#868e96; font-weight:400;">{place}</span>'
    elif "장르" in selection_type:
        return f'<span style="color:#868e96; font-weight:400;">{genre}</span>'
    else:
        return ""

def push_to_github(filename):
    print("🚀 깃허브로 업로드를 시작합니다...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        try:
            subprocess.run(["git", "commit", "-m", f"Update calendar: {YEAR}-{MONTH}"], check=True)
        except subprocess.CalledProcessError:
            print("⚠️ 변경된 내용이 없습니다.")
            return
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ 깃허브 업로드 성공! 잠시 후 사이트에서 확인하세요.")
    except Exception as e:
        print(f"❌ 업로드 실패: {e}")

def main():
    calendar.setfirstweekday(calendar.SUNDAY)

    filename = '공연목록_오픈예정.xlsx'
    if not os.path.exists(filename):
        print(f"오류: '{filename}' 파일이 없습니다.")
        return

    try:
        df = pd.read_excel(filename).fillna({'장르': '기타', '지역': '(기타)'})
        if '오픈일시' in df.columns:
            df['Day'] = df['오픈일시'].apply(get_day)
        else:
            print("오류: 엑셀에 '오픈일시' 컬럼이 없습니다.")
            return
    except Exception as e:
        print(f"엑셀 읽기 실패: {e}")
        return

    raw_genres = set(df['장르'].astype(str).unique())
    if '선택' in raw_genres: raw_genres.remove('선택')
    
    unique_genres = []
    for g in GENRE_ORDER:
        if g in raw_genres:
            unique_genres.append(g)
            raw_genres.remove(g)
    unique_genres.extend(sorted(list(raw_genres)))

    day_names_kr = ["일", "월", "화", "수", "목", "금", "토"]

    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{YEAR}년 {MONTH}월 공연 예매일정</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            
            body {{ font-family: 'Pretendard', sans-serif; background-color: #ffffff; padding: 20px 40px; user-select: none; }}
            
            .header-container {{ text-align: center; margin-bottom: 10px; }}
            
            .emoji-font {{
                font-family: "Segoe UI Emoji", "Segoe UI Symbol", "Apple Color Emoji", "Noto Color Emoji", sans-serif;
            }}

            .main-title {{ font-size: 30px; font-weight: 800; color: #343a40; margin-bottom: 30px; }}
            .sub-title {{ font-size: 29px; font-weight: 700; color: #495057; }}
            
            .control-bar {{ 
                margin-bottom: 20px; 
                display: flex; flex-direction: column; align-items: flex-start; gap: 2px; 
                padding-left: 12px; font-size: 13px;
            }}
            .filter-group {{ 
                display: flex; 
                align-items: baseline; 
                gap: 0px; 
                width: 100%; 
            }}
            
            .group-title {{ 
                font-weight: 800; color: #212529; margin-right: 2px; white-space: nowrap; 
                margin-top: 3px;
            }}
            
            .chk-wrap {{ 
                display: flex; flex-wrap: wrap; align-items: center; gap: 0px; flex: 1; 
            }}
            
            label {{ cursor: pointer; display: flex; align-items: center; gap: 4px; margin-right: 8px; transition: opacity 0.2s; }}
            label:hover {{ opacity: 0.7; }}
            input[type="checkbox"] {{ accent-color: #343a40; width: 14px; height: 14px; cursor: pointer; }}
            
            .btn-reset {{
                margin-left: 4px; background-color: transparent; border: 1px solid #ced4da;
                border-radius: 4px; padding: 2px 8px; font-size: 12px; font-weight: 600; 
                color: #495057; cursor: pointer; transition: all 0.2s; height: 24px; display: flex; align-items: center;
            }}
            .btn-reset:hover {{ background-color: #e9ecef; color: #212529; }}

            table {{ width: 100%; table-layout: fixed; border-collapse: collapse; background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border-radius: 10px; overflow: hidden; }}
            th {{ background-color: #495057; color: white; padding: 10px; font-size: 14px; font-weight: 600; }}
            th:first-child {{ background-color: #fa5252; }}
            th:last-child {{ background-color: #228be6; }}
            td {{ vertical-align: top; height: 150px; border: 1px solid #dee2e6; padding: 5px; }}
            td:hover {{ background-color: #fcfcfc; }}
            
            .date-num {{ font-weight: 800; font-size: 14px; color: #adb5bd; margin-bottom: 5px; display: block; }}
            .sun .date-num {{ color: #ff8787; }}
            .sat .date-num {{ color: #74c0fc; }}

            .event-box {{ 
                display: none; margin-bottom: 4px; padding: 4px 6px; border-radius: 4px; 
                background-color: #fff; border: 1px solid #e9ecef; box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
                cursor: pointer; font-size: {FONT_SIZE}px; overflow: hidden; 
            }}
            .event-box:hover {{ transform: translateY(-1px); border-color: #adb5bd; z-index: 5; position: relative; }}
            
            .event-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }}
            .box-line2 {{ 
                display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
                overflow: hidden; text-overflow: ellipsis; line-height: 1.3; 
                word-break: break-all; margin-top: 1px; 
            }}

            .txt-red {{ color: {COLOR_SEOUL}; font-weight: 700; }}
            .txt-green {{ color: {COLOR_GYEONGGI}; font-weight: 700; }}
            .txt-blue {{ color: {COLOR_OTHERS}; font-weight: 700; }}
            .txt-black {{ color: #495057; font-weight: 500; }}

            /* ========================================================= */
            /* 📱 모바일 최적화 (768px 이하) */
            /* ========================================================= */
            @media screen and (max-width: 768px) {{
                body {{ padding: 15px; }} 
                
                .main-title {{ font-size: 32px; margin-bottom: 30px; word-break: keep-all; }}
                .sub-title {{ font-size: 36px; margin-bottom: 25px; }}
                
                .control-bar {{ padding-left: 0; gap: 15px; }}
                
                .group-title {{ 
                    font-size: 17px; min-width: 50px; margin-top: 0; transform: translateY(2px);
                }}
                
                .chk-wrap {{ gap: 8px 12px; }} 
                label {{ font-size: 16px; margin: 0; line-height: 1.5; }} 
                input[type="checkbox"] {{ width: 18px; height: 18px; margin-top: 0; transform: translateY(1px); }}
                
                .btn-reset {{ 
                    font-size: 15px; padding: 4px 10px; border: 1px solid #adb5bd; margin-left: 0; 
                }}
                
                table, thead, tbody, th, td, tr {{ display: block; }}
                thead {{ display: none; }}
                tr {{ margin-bottom: 0; }}
                
                /* [핵심] 모바일 정렬: text-align left, 고정 패딩 */
                td {{ 
                    height: auto !important; border: none; border-bottom: 1px solid #eee; 
                    position: relative; 
                    text-align: left !important;  /* 무조건 왼쪽 정렬 */
                    padding: 12px 15px !important; /* 상하 12px, 좌우 15px (여백 통일) */
                }}
                td:empty {{ display: none; }}
                
                /* 날짜 숫자 */
                .date-num {{ 
                    display: inline-block; width: auto; /* auto로 변경하여 텍스트 길이에 맞춤 */
                }}
                
                .date-num::after {{
                    content: "(" attr(data-dayname) ")";
                    font-size: inherit; color: inherit; font-weight: inherit; margin-left: 0;
                }}
                
                /* 주말 색상 */
                .sun .date-num {{ color: #ff8787 !important; }}
                .sat .date-num {{ color: #74c0fc !important; }}
                
                /* ------------------------------------------------------------------
                   [상태 1] 공연(이벤트)이 나타났을 때 (지역 선택 후)
                   ------------------------------------------------------------------ */
                td.has-event .date-num {{
                    font-size: 24px; margin-bottom: 12px; 
                    border-bottom: 2px solid #343a40; padding-bottom: 5px;
                    color: #212529; 
                }}
                td.has-event .date-num::after {{ 
                    font-size: inherit; color: inherit; font-weight: inherit;
                }}

                /* 일정이 없는 날 (no-event) */
                td.no-event {{
                    border-bottom: 1px solid #f1f3f5;
                }}
                td.no-event .date-num {{
                    font-size: 15px; margin-bottom: 0; border-bottom: none; 
                    color: #ced4da; /* 흐리게 */
                }}
                td.no-event.sun .date-num {{ color: #ffc9c9 !important; }}
                td.no-event.sat .date-num {{ color: #a5d8ff !important; }}

                .event-box {{
                    font-size: 16px !important; padding: 12px; margin-bottom: 10px; border: 1px solid #ced4da;
                }}
                .box-line2 {{ -webkit-line-clamp: 10; line-height: 1.5; }}
            
                /* ------------------------------------------------------------------
                   [상태 2] 초기 상태 (지역 미선택) - 모두 흐리게 & 정렬
                   ------------------------------------------------------------------ */
                body.initial-mode td {{
                    border-bottom: 1px solid #f1f3f5;
                    /* padding은 위에서 정의한 15px가 적용됨 */
                }}

                body.initial-mode .date-num {{
                    font-size: 16px !important; 
                    margin-bottom: 0 !important;
                    border-bottom: none !important;
                    font-weight: 500 !important;
                    color: #ced4da !important; /* [수정] 다시 흐리게 변경 */
                }}
                
                body.initial-mode .date-num::after {{
                    font-size: inherit; color: inherit; font-weight: inherit;
                }}
                
                /* 초기상태 주말 (흐리게) */
                body.initial-mode .sun .date-num {{ color: #ffc9c9 !important; }}
                body.initial-mode .sat .date-num {{ color: #a5d8ff !important; }}
            }}
        </style>
    </head>
    <body class="initial-mode">
        <div class="header-container">
            <div class="main-title"><span class="emoji-font">📅</span> 공연 예매일정 캘린더</div>
            <div class="sub-title">{YEAR}년 {MONTH}월</div>
        </div>
        
        <div class="control-bar">
            <div class="filter-group">
                <span class="group-title">지역 :</span>
                <div class="chk-wrap">
                    <label><input type="checkbox" class="region-chk" value="seoul"> <span class="txt-red">서울</span></label>
                    <label><input type="checkbox" class="region-chk" value="gyeonggi"> <span class="txt-green">경기/인천</span></label>
                    <label><input type="checkbox" class="region-chk" value="others"> <span class="txt-blue">그 외 지역</span></label>
                </div>
            </div>
            
            <div class="filter-group">
                <span class="group-title">장르 :</span>
                <div class="chk-wrap">
                    {' '.join([f'<label><input type="checkbox" class="genre-chk" value="{g}" checked> <span class="txt-black">{g}</span></label>' for g in unique_genres])}
                    <button id="btn-reset" class="btn-reset">모두해제</button>
                </div>
            </div>
        </div>

        <div id="calendar-container">
            <table>
                <thead><tr><th>일</th><th>월</th><th>화</th><th>수</th><th>목</th><th>금</th><th>토</th></tr></thead>
                <tbody>
    """

    cal = calendar.monthcalendar(YEAR, MONTH)
    for week in cal:
        html += "<tr>"
        for idx, day in enumerate(week):
            td_class = ""
            if idx == 0: td_class = "sun"
            elif idx == 6: td_class = "sat"
            
            day_kor = day_names_kr[idx]
            
            day_events = df[df['Day'] == day]
            has_event_class = "has-event" if not day_events.empty else "no-event"

            html += f"<td class='{td_class} {has_event_class}'>"
            if day != 0:
                html += f"<span class='date-num' data-dayname='{day_kor}'>{day}</span>"
                
                for _, row in day_events.iterrows():
                    region_txt = str(row['지역'])
                    if "(서울)" in region_txt: r_group = "seoul"
                    elif "(경기)" in region_txt or "(인천)" in region_txt: r_group = "gyeonggi"
                    else: r_group = "others"
                    
                    genre = str(row['장르'])
                    tooltip = f"[{region_txt}] {row['제목']}\\n장소: {row['장소']}\\n장르: {genre}\\n시간: {row['오픈일시']}"
                    
                    html_left = get_content_html(LAYOUT_TOP_LEFT, row)
                    html_right = get_content_html(LAYOUT_TOP_RIGHT, row)
                    html_bottom = get_content_html(LAYOUT_BOTTOM, row)

                    html += f"""
                    <div class="event-box" data-region="{r_group}" data-genre="{genre}" title="{tooltip}">
                        <div class="event-header">
                            <div>{html_left}</div>
                            <div>{html_right}</div>
                        </div>
                        <span class="box-line2">{html_bottom}</span>
                    </div>
                    """
            html += "</td>"
        html += "</tr>"

    html += """
                </tbody>
            </table>
        </div>
        <script>
            const regionChks = document.querySelectorAll('.region-chk');
            const genreChks = document.querySelectorAll('.genre-chk');
            const events = document.querySelectorAll('.event-box');
            const table = document.querySelector('table');
            const btnReset = document.getElementById('btn-reset');

            function updateCalendar() {
                const selectedRegions = Array.from(regionChks).filter(c => c.checked).map(c => c.value);
                const selectedGenres = Array.from(genreChks).filter(c => c.checked).map(c => c.value);
                let visibleCount = 0;
                
                events.forEach(el => {
                    if (selectedRegions.includes(el.dataset.region) && selectedGenres.includes(el.dataset.genre)) {
                        el.style.display = 'block'; visibleCount++;
                    } else { el.style.display = 'none'; }
                });
                
                // [초기 상태 감지] 지역 선택이 하나도 없으면 'initial-mode'
                if (selectedRegions.length === 0) {
                    document.body.classList.add('initial-mode'); 
                } else {
                    document.body.classList.remove('initial-mode'); 
                }
            }

            let isAllChecked = true;
            btnReset.addEventListener('click', () => {
                if (isAllChecked) {
                    genreChks.forEach(chk => chk.checked = false);
                    btnReset.innerText = "모두선택";
                    isAllChecked = false;
                } else {
                    genreChks.forEach(chk => chk.checked = true);
                    btnReset.innerText = "모두해제";
                    isAllChecked = true;
                }
                updateCalendar();
            });

            regionChks.forEach(chk => chk.addEventListener('change', updateCalendar));
            genreChks.forEach(chk => chk.addEventListener('change', updateCalendar));
            
            updateCalendar();
        </script>
    </body>
    </html>
    """

    filename = "index.html" 
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"생성 완료: {filename}")
    push_to_github(filename)

if __name__ == "__main__":
    main()