import pandas as pd
import os
import webbrowser
import subprocess
import calendar
import json
import re 

# ==========================================
# [설정]
# ==========================================
# 엑셀에 연도가 없을 경우 사용할 기본 연도
DEFAULT_YEAR = 2026 

GENRE_ORDER = ["콘서트", "뮤지컬", "연극", "클래식", "행사(전시)", "가족"]

COLOR_SEOUL = "#e03131"
COLOR_GYEONGGI = "#e03131"
COLOR_OTHERS = "#1971c2"

FONT_SIZE = 11
# ==========================================

def get_content_html(row_data):
    region = str(row_data['지역'])
    title = str(row_data['제목'])
    place = str(row_data['장소'])
    genre = str(row_data['장르'])
    
    raw_time = str(row_data['오픈일시'])
    time_txt = raw_time.split(' ')[-1] if ' ' in raw_time else ''

    if "(서울)" in region: color = COLOR_SEOUL
    elif "(경기)" in region or "(인천)" in region: color = COLOR_GYEONGGI
    else: color = COLOR_OTHERS

    html_left = f'<span style="color:#212529; font-weight:800;">{time_txt}</span>'
    html_right = f'<span style="color:{color}; font-weight:800;">{region}</span>'
    html_bottom = f'<span style="color:#495057; font-weight:500;">{title}</span>'

    r_group = "others"
    if "(서울)" in region: r_group = "seoul"
    elif "(경기)" in region or "(인천)" in region: r_group = "gyeonggi"

    tooltip = f"[{region}] {title}\n장소: {place}\n장르: {genre}\n시간: {raw_time}"

    return f"""
    <div class="event-box" data-region="{r_group}" data-genre="{genre}" title="{tooltip}">
        <div class="event-header">
            <div>{html_left}</div>
            <div>{html_right}</div>
        </div>
        <span class="box-line2">{html_bottom}</span>
    </div>
    """

def push_to_github():
    print("🚀 깃허브로 업로드를 시작합니다...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        try:
            subprocess.run(["git", "commit", "-m", "Fix date parsing logic"], check=True)
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
        # 1. 엑셀 로드
        df = pd.read_excel(filename).fillna({'장르': '기타', '지역': '(기타)'})
        if '오픈일시' not in df.columns:
            print("오류: 엑셀에 '오픈일시' 컬럼이 없습니다.")
            return

        print("엑셀 데이터 로드 성공. 날짜 변환 중...")

        # 2. [수정됨] 강력한 날짜 파싱 로직 (연도 없으면 DEFAULT_YEAR 사용)
        def smart_parse_date(x):
            s = str(x).strip()
            # 괄호 안 내용 제거 (예: (월))
            s = re.sub(r'\(.*?\)', '', s)
            
            # 패턴 1: 2026.01.05 (연도 있음)
            match_full = re.search(r'(\d{4})[\.\-/](\d{1,2})[\.\-/](\d{1,2})', s)
            if match_full:
                return int(match_full.group(1)), int(match_full.group(2)), int(match_full.group(3))
            
            # 패턴 2: 01.05 (연도 없음 -> DEFAULT_YEAR 사용)
            match_short = re.search(r'(\d{1,2})[\.\-/](\d{1,2})', s)
            if match_short:
                return DEFAULT_YEAR, int(match_short.group(1)), int(match_short.group(2))
            
            return None, None, None

        parsed_data = df['오픈일시'].apply(smart_parse_date)
        df['Year'], df['Month'], df['Day'] = zip(*parsed_data)

        # 파싱 실패 확인
        failed_count = df['Year'].isna().sum()
        if failed_count > 0:
            print(f"⚠️ 경고: {failed_count}개의 데이터는 날짜 형식을 인식하지 못해 제외되었습니다.")
        
        df = df.dropna(subset=['Year', 'Month', 'Day'])
        df['Year'] = df['Year'].astype(int)
        df['Month'] = df['Month'].astype(int)
        df['Day'] = df['Day'].astype(int)

        # 3. 장르 목록
        raw_genres = set(df['장르'].astype(str).unique())
        if '선택' in raw_genres: raw_genres.remove('선택')
        unique_genres = sorted(list(raw_genres))
        
        sorted_genres = []
        for g in GENRE_ORDER:
            if g in unique_genres:
                sorted_genres.append(g)
                unique_genres.remove(g)
        sorted_genres.extend(unique_genres)
        unique_genres = sorted_genres

        # 4. 존재하는 월 목록 확인
        all_yms = sorted(list(df[['Year', 'Month']].drop_duplicates().itertuples(index=False, name=None)))
        
        if not all_yms:
            print("❌ 오류: 유효한 날짜 데이터가 하나도 없습니다.")
            return

        print(f"📅 생성할 달력: {all_yms}")

        # 5. HTML 생성
        all_calendars_html = ""
        
        for idx, (year, month) in enumerate(all_yms):
            display_style = "block" if idx == 0 else "none"
            df_month = df[(df['Year'] == year) & (df['Month'] == month)]
            cal = calendar.monthcalendar(year, month)
            day_names_kr = ["일", "월", "화", "수", "목", "금", "토"]
            
            table_html = f"""
            <div id="page-{idx}" class="calendar-page" data-title="{year}년 {month}월" style="display: {display_style};">
                <table>
                    <thead><tr><th>일</th><th>월</th><th>화</th><th>수</th><th>목</th><th>금</th><th>토</th></tr></thead>
                    <tbody>
            """
            
            for week in cal:
                table_html += "<tr>"
                for w_idx, day in enumerate(week):
                    td_class = ""
                    if w_idx == 0: td_class = "sun"
                    elif w_idx == 6: td_class = "sat"
                    
                    day_kor = day_names_kr[w_idx]
                    day_events = df_month[df_month['Day'] == day]
                    has_event_class = "has-event" if not day_events.empty else "no-event"

                    table_html += f"<td class='{td_class} {has_event_class}'>"
                    if day != 0:
                        table_html += f"<span class='date-num' data-dayname='{day_kor}'>{day}</span>"
                        for _, row in day_events.iterrows():
                            table_html += get_content_html(row)
                    table_html += "</td>"
                table_html += "</tr>"
            
            table_html += """
                    </tbody>
                </table>
            </div>
            """
            all_calendars_html += table_html


        # 6. 최종 HTML 조립
        full_html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>공연 예매일정 캘린더</title>
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        
        body {{ font-family: 'Pretendard', sans-serif; background-color: #ffffff; padding: 20px 40px; user-select: none; }}
        
        .header-container {{ 
            display: flex; justify-content: center; align-items: center; gap: 20px;
            margin-bottom: 20px;
        }}
        .nav-btn {{
            cursor: pointer; color: #868e96; font-size: 30px; font-weight: 800;
            padding: 10px; border-radius: 50%; transition: all 0.2s; line-height: 1;
        }}
        .nav-btn:hover {{ background-color: #f1f3f5; color: #343a40; }}
        .nav-btn.disabled {{ opacity: 0.2; pointer-events: none; }}

        .title-wrap {{ text-align: center; }}
        .emoji-font {{ font-family: "Segoe UI Emoji", "Segoe UI Symbol", "Apple Color Emoji", "Noto Color Emoji", sans-serif; }}
        .main-title {{ font-size: 30px; font-weight: 800; color: #343a40; margin-bottom: 5px; }}
        .sub-title {{ font-size: 29px; font-weight: 700; color: #495057; }}
        
        .control-bar {{ 
            margin-bottom: 20px; display: flex; flex-direction: column; align-items: flex-start; gap: 2px; 
            padding-left: 12px; font-size: 13px;
        }}
        .filter-group {{ display: flex; align-items: baseline; gap: 0px; width: 100%; }}
        .group-title {{ font-weight: 800; color: #212529; margin-right: 2px; white-space: nowrap; margin-top: 3px; }}
        .chk-wrap {{ display: flex; flex-wrap: wrap; align-items: center; gap: 0px; flex: 1; }}
        
        label {{ 
            cursor: pointer; display: flex; align-items: center; gap: 4px; margin-right: 8px; 
            -webkit-tap-highlight-color: transparent; 
        }}
        
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

        @media screen and (max-width: 768px) {{
            body {{ padding: 15px; }} 
            
            .header-container {{ gap: 10px; margin-bottom: 25px; }}
            .nav-btn {{ font-size: 36px; padding: 5px 15px; }}
            .main-title {{ font-size: 16px; margin-bottom: 2px; font-weight: 700; }}
            .sub-title {{ font-size: 32px; font-weight: 800; }}
            
            .control-bar {{ padding-left: 0; gap: 15px; }}
            .group-title {{ font-size: 17px; min-width: 50px; margin-top: 0; transform: translateY(2px); }}
            .chk-wrap {{ gap: 8px 12px; }} 
            label {{ font-size: 16px; margin: 0; line-height: 1.5; }} 
            input[type="checkbox"] {{ width: 18px; height: 18px; margin-top: 0; transform: translateY(1px); }}
            .btn-reset {{ font-size: 15px; padding: 4px 10px; border: 1px solid #adb5bd; margin-left: 0; }}
            
            table, thead, tbody, th, td, tr {{ display: block; }}
            thead {{ display: none; }}
            tr {{ margin-bottom: 0; }}
            
            td {{ 
                height: auto !important; border: none; border-bottom: 1px solid #eee; 
                position: relative; text-align: left !important; padding: 12px 5px !important; 
            }}
            td:empty {{ display: none; }}
            
            .date-num {{ display: inline-block; width: auto; }}
            .date-num::after {{ content: "(" attr(data-dayname) ")"; font-size: inherit; color: inherit; font-weight: inherit; margin-left: 0; }}
            
            .sun .date-num {{ color: #ffc9c9; }}
            .sat .date-num {{ color: #a5d8ff; }}

            td.day-active .date-num {{
                font-size: 24px; margin-bottom: 12px; border-bottom: none; padding-bottom: 5px;
                color: #212529; font-weight: 800;
            }}
            td.day-active .date-num::after {{ font-size: inherit; color: inherit; font-weight: inherit; }}
            td.day-active.sun .date-num {{ color: #ff8787 !important; }}
            td.day-active.sat .date-num {{ color: #74c0fc !important; }}

            td.day-inactive .date-num {{ font-size: 15px; margin-bottom: 0; border-bottom: none; color: #ced4da; }}
            td.day-inactive.sun .date-num {{ color: #ffc9c9 !important; }}
            td.day-inactive.sat .date-num {{ color: #a5d8ff !important; }}

            .event-box {{ 
                font-size: 16px !important; padding: 12px; margin-bottom: 10px; border: 1px solid #ced4da;
                height: auto !important; min-height: 60px;
            }}
            .box-line2 {{ 
                display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
                overflow: hidden; text-overflow: ellipsis; line-height: 1.4; margin-top: 6px; 
                white-space: normal; word-break: break-all; 
            }}

            body.initial-mode td {{ border-bottom: 1px solid #f1f3f5; }}
            body.initial-mode .date-num {{
                font-size: 16px !important; margin-bottom: 0 !important; border-bottom: none !important;
                font-weight: 500 !important; color: #ced4da !important;
            }}
            body.initial-mode .sun .date-num {{ color: #ffc9c9 !important; }}
            body.initial-mode .sat .date-num {{ color: #a5d8ff !important; }}
        }}
    </style>
</head>
<body class="initial-mode">
    <div class="header-container">
        <div class="nav-btn" id="prev-btn">&lt;</div>
        <div class="title-wrap">
            <div class="main-title"><span class="emoji-font">📌</span> 공연 예매일정</div>
            <div class="sub-title" id="calendar-title">Loading...</div>
        </div>
        <div class="nav-btn" id="next-btn">&gt;</div>
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
        {all_calendars_html}
    </div>

    <script>
        const regionChks = document.querySelectorAll('.region-chk');
        const genreChks = document.querySelectorAll('.genre-chk');
        const btnReset = document.getElementById('btn-reset');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const titleEl = document.getElementById('calendar-title');
        
        const pages = document.querySelectorAll('.calendar-page');
        let currentIndex = 0;
        const totalPages = pages.length;

        function saveSettings() {{
            const settings = {{
                regions: Array.from(regionChks).filter(c => c.checked).map(c => c.value),
                genres: Array.from(genreChks).filter(c => c.checked).map(c => c.value)
            }};
            localStorage.setItem('calendarSettings', JSON.stringify(settings));
        }}

        function loadSettings() {{
            const saved = localStorage.getItem('calendarSettings');
            if (saved) {{
                const settings = JSON.parse(saved);
                regionChks.forEach(c => c.checked = settings.regions.includes(c.value));
                genreChks.forEach(c => c.checked = settings.genres.includes(c.value));
            }}
        }}

        function showPage(index) {{
            pages.forEach((page, idx) => {{
                if (idx === index) {{
                    page.style.display = 'block';
                    titleEl.innerText = page.dataset.title;
                }} else {{
                    page.style.display = 'none';
                }}
            }});
            
            if (index === 0) prevBtn.classList.add('disabled');
            else prevBtn.classList.remove('disabled');

            if (index === totalPages - 1) nextBtn.classList.add('disabled');
            else nextBtn.classList.remove('disabled');

            applyFilter();
        }}

        function applyFilter() {{
            const selectedRegions = Array.from(regionChks).filter(c => c.checked).map(c => c.value);
            const selectedGenres = Array.from(genreChks).filter(c => c.checked).map(c => c.value);
            
            saveSettings();

            const visiblePage = pages[currentIndex];
            const tds = visiblePage.querySelectorAll('td');

            if (selectedRegions.length === 0) {{
                document.body.classList.add('initial-mode');
                visiblePage.querySelectorAll('.event-box').forEach(el => el.style.display = 'none');
                tds.forEach(td => {{
                    td.classList.remove('day-active');
                    td.classList.add('day-inactive');
                }});
                return;
            }} else {{
                document.body.classList.remove('initial-mode');
            }}

            tds.forEach(td => {{
                const boxes = td.querySelectorAll('.event-box');
                let hasVisible = false;
                
                boxes.forEach(box => {{
                    if (selectedRegions.includes(box.dataset.region) && selectedGenres.includes(box.dataset.genre)) {{
                        box.style.display = 'block';
                        hasVisible = true;
                    }} else {{
                        box.style.display = 'none';
                    }}
                }});

                if (hasVisible) {{
                    td.classList.add('day-active');
                    td.classList.remove('day-inactive');
                }} else {{
                    td.classList.remove('day-active');
                    td.classList.add('day-inactive');
                }}
            }});
        }}

        prevBtn.addEventListener('click', () => {{
            if (currentIndex > 0) {{
                currentIndex--;
                showPage(currentIndex);
            }}
        }});

        nextBtn.addEventListener('click', () => {{
            if (currentIndex < totalPages - 1) {{
                currentIndex++;
                showPage(currentIndex);
            }}
        }});

        let isAllChecked = true;
        btnReset.addEventListener('click', () => {{
            if (isAllChecked) {{
                genreChks.forEach(chk => chk.checked = false);
                btnReset.innerText = "모두선택";
                isAllChecked = false;
            }} else {{
                genreChks.forEach(chk => chk.checked = true);
                btnReset.innerText = "모두해제";
                isAllChecked = true;
            }}
            applyFilter();
        }});

        regionChks.forEach(chk => chk.addEventListener('change', applyFilter));
        genreChks.forEach(chk => chk.addEventListener('change', applyFilter));

        loadSettings();
        if (totalPages > 0) {{
            showPage(0);
        }} else {{
            titleEl.innerText = "일정 없음";
        }}
        
    </script>
</body>
</html>
        """

        filename = "index.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_html)
        
        print(f"생성 완료: {filename}")
        push_to_github()

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()