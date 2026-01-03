import pandas as pd
import os
import webbrowser
import subprocess
import json

# ==========================================
# [설정]
# ==========================================
# 엑셀 데이터에 있는 날짜를 기준으로 자동 설정되므로 연도/월 설정 삭제

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

def push_to_github():
    print("🚀 깃허브로 업로드를 시작합니다...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        try:
            subprocess.run(["git", "commit", "-m", "Update calendar (Single Page)"], check=True)
        except subprocess.CalledProcessError:
            print("⚠️ 변경된 내용이 없습니다.")
            return
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ 깃허브 업로드 성공! 잠시 후 사이트에서 확인하세요.")
    except Exception as e:
        print(f"❌ 업로드 실패: {e}")

def main():
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

        # 2. 날짜 파싱 (년, 월, 일 추출)
        def parse_date(x):
            try:
                # 2026.01.20(화) 형식 가정
                date_part = str(x).split('(')[0]
                parts = date_part.split('.')
                return int(parts[0]), int(parts[1]), int(parts[2])
            except:
                return None, None, None

        df['Year'], df['Month'], df['Day'] = zip(*df['오픈일시'].apply(parse_date))
        df = df.dropna(subset=['Year', 'Month', 'Day'])
        df['Year'] = df['Year'].astype(int)
        df['Month'] = df['Month'].astype(int)
        df['Day'] = df['Day'].astype(int)

        # 3. 데이터 가공 (JavaScript로 넘길 데이터 리스트 생성)
        # DataFrame을 dict list로 변환
        events_list = df.to_dict('records')
        
        # JS 변수로 넣기 위해 JSON 문자열로 변환 (ensure_ascii=False로 한글 깨짐 방지)
        events_json = json.dumps(events_list, ensure_ascii=False)

        # 4. 장르 목록
        raw_genres = set(df['장르'].astype(str).unique())
        if '선택' in raw_genres: raw_genres.remove('선택')
        
        unique_genres = []
        for g in GENRE_ORDER:
            if g in raw_genres:
                unique_genres.append(g)
                raw_genres.remove(g)
        unique_genres.extend(sorted(list(raw_genres)))

        # 시작 연월 계산 (데이터 중 가장 빠른 날짜 or 현재 날짜)
        min_year = df['Year'].min()
        min_month = df[df['Year'] == min_year]['Month'].min()

        # HTML 생성
        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>공연 예매일정 캘린더</title>
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        
        body {{ font-family: 'Pretendard', sans-serif; background-color: #ffffff; padding: 20px 40px; user-select: none; }}
        
        /* 네비게이션 헤더 */
        .header-container {{ 
            display: flex; justify-content: center; align-items: center; gap: 20px;
            margin-bottom: 20px;
        }}
        .nav-btn {{
            cursor: pointer; color: #868e96; font-size: 30px; font-weight: 800;
            padding: 10px; border-radius: 50%; transition: all 0.2s; line-height: 1; user-select: none;
        }}
        .nav-btn:hover {{ background-color: #f1f3f5; color: #343a40; }}

        .title-wrap {{ text-align: center; }}
        .emoji-font {{ font-family: "Segoe UI Emoji", "Segoe UI Symbol", "Apple Color Emoji", "Noto Color Emoji", sans-serif; }}
        .main-title {{ font-size: 30px; font-weight: 800; color: #343a40; margin-bottom: 5px; }}
        .sub-title {{ font-size: 29px; font-weight: 700; color: #495057; }}

        /* 컨트롤 바 */
        .control-bar {{ 
            margin-bottom: 20px; display: flex; flex-direction: column; align-items: flex-start; gap: 2px; 
            padding-left: 12px; font-size: 13px;
        }}
        .filter-group {{ display: flex; align-items: baseline; gap: 0px; width: 100%; }}
        .group-title {{ font-weight: 800; color: #212529; margin-right: 2px; white-space: nowrap; margin-top: 3px; }}
        .chk-wrap {{ display: flex; flex-wrap: wrap; align-items: center; gap: 0px; flex: 1; }}
        
        label {{ cursor: pointer; display: flex; align-items: center; gap: 4px; margin-right: 8px; transition: opacity 0.2s; }}
        label:hover {{ opacity: 0.7; }}
        input[type="checkbox"] {{ accent-color: #343a40; width: 14px; height: 14px; cursor: pointer; }}
        
        .btn-reset {{
            margin-left: 4px; background-color: transparent; border: 1px solid #ced4da;
            border-radius: 4px; padding: 2px 8px; font-size: 12px; font-weight: 600; 
            color: #495057; cursor: pointer; transition: all 0.2s; height: 24px; display: flex; align-items: center;
        }}
        .btn-reset:hover {{ background-color: #e9ecef; color: #212529; }}

        /* 캘린더 테이블 */
        table {{ width: 100%; table-layout: fixed; border-collapse: collapse; background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border-radius: 10px; overflow: hidden; }}
        th {{ background-color: #495057; color: white; padding: 10px; font-size: 14px; font-weight: 600; }}
        th:first-child {{ background-color: #fa5252; }}
        th:last-child {{ background-color: #228be6; }}
        td {{ vertical-align: top; height: 150px; border: 1px solid #dee2e6; padding: 5px; }}
        td:hover {{ background-color: #fcfcfc; }}
        
        .date-num {{ font-weight: 800; font-size: 14px; color: #adb5bd; margin-bottom: 5px; display: block; }}
        .sun .date-num {{ color: #ff8787; }}
        .sat .date-num {{ color: #74c0fc; }}

        /* 이벤트 박스 */
        .event-box {{ 
            display: none; margin-bottom: 4px; padding: 4px 6px; border-radius: 4px; 
            background-color: #fff; border: 1px solid #e9ecef; box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
            cursor: pointer; font-size: {FONT_SIZE}px; overflow: hidden; 
        }}
        .event-box:hover {{ transform: translateY(-1px); border-color: #adb5bd; z-index: 5; position: relative; }}
        
        .event-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }}
        .box-line2 {{ 
            display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
            overflow: hidden; text-overflow: ellipsis; line-height: 1.3; word-break: break-all; margin-top: 1px; 
        }}

        .txt-red {{ color: {COLOR_SEOUL}; font-weight: 700; }}
        .txt-green {{ color: {COLOR_GYEONGGI}; font-weight: 700; }}
        .txt-blue {{ color: {COLOR_OTHERS}; font-weight: 700; }}
        .txt-black {{ color: #495057; font-weight: 500; }}

        /* 📱 모바일 최적화 */
        @media screen and (max-width: 768px) {{
            body {{ padding: 15px; }} 

            .header-container {{ gap: 10px; margin-bottom: 25px; }}
            .nav-btn {{ font-size: 36px; padding: 5px 15px; }}
            .main-title {{ font-size: 16px; margin-bottom: 2px; font-weight: 700; }}
            .sub-title {{ font-size: 32px; font-weight: 800; }}
            
            .control-bar {{ padding-left: 0; gap: 15px; }}
            .filter-group {{ align-items: baseline; }}
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
            .date-num::after {{
                content: "(" attr(data-dayname) ")";
                font-size: inherit; color: inherit; font-weight: inherit; margin-left: 0;
            }}
            
            .sun .date-num {{ color: #ffc9c9; }}
            .sat .date-num {{ color: #a5d8ff; }}

            /* 활성 상태 */
            td.day-active .date-num {{
                font-size: 24px; margin-bottom: 12px; border-bottom: none; padding-bottom: 5px;
                color: #212529; font-weight: 800;
            }}
            td.day-active .date-num::after {{ font-size: inherit; color: inherit; font-weight: inherit; }}
            td.day-active.sun .date-num {{ color: #ff8787 !important; }}
            td.day-active.sat .date-num {{ color: #74c0fc !important; }}

            /* 비활성 상태 */
            td.day-inactive .date-num {{
                font-size: 15px; margin-bottom: 0; border-bottom: none; color: #ced4da; 
            }}
            td.day-inactive.sun .date-num {{ color: #ffc9c9 !important; }}
            td.day-inactive.sat .date-num {{ color: #a5d8ff !important; }}

            .event-box {{ font-size: 16px !important; padding: 12px; margin-bottom: 10px; border: 1px solid #ced4da; }}
            .box-line2 {{ -webkit-line-clamp: 10; line-height: 1.5; }}

            /* 초기 모드 */
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
            <div class="main-title"><span class="emoji-font">📅</span> 공연 예매일정</div>
            <div class="sub-title" id="calendar-title">YEAR년 MONTH월</div>
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
        <table>
            <thead><tr><th>일</th><th>월</th><th>화</th><th>수</th><th>목</th><th>금</th><th>토</th></tr></thead>
            <tbody id="calendar-body">
                </tbody>
        </table>
    </div>

    <script>
        // 1. 파이썬에서 넘겨준 전체 데이터
        const allEvents = {events_json};
        
        // 2. 현재 상태 (초기값)
        let currYear = {min_year};
        let currMonth = {min_month};

        // 색상 상수
        const COLOR_SEOUL = "{COLOR_SEOUL}";
        const COLOR_GYEONGGI = "{COLOR_GYEONGGI}";
        const COLOR_OTHERS = "{COLOR_OTHERS}";

        // DOM 요소
        const titleEl = document.getElementById('calendar-title');
        const tbodyEl = document.getElementById('calendar-body');
        const regionChks = document.querySelectorAll('.region-chk');
        const genreChks = document.querySelectorAll('.genre-chk');
        const btnReset = document.getElementById('btn-reset');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');

        // --- 기능 함수들 ---

        function getDayName(dayIndex) {{ // 0:일, 1:월 ...
            const names = ["일", "월", "화", "수", "목", "금", "토"];
            return names[dayIndex];
        }}

        function getEventHtml(row) {{
            const region = row['지역'];
            const title = row['제목'];
            const place = row['장소'];
            const genre = row['장르'];
            const timeTxt = row['오픈일시'].split(' ').pop();
            
            let color = COLOR_OTHERS;
            if (region.includes("서울")) color = COLOR_SEOUL;
            else if (region.includes("경기") || region.includes("인천")) color = COLOR_GYEONGGI;

            // HTML 생성 (파이썬 로직을 JS로 이식)
            // LAYOUT 설정이 파이썬 변수로 되어있지만, 여기선 JS에서 조립해야 함.
            // 요청하신 배치: TL:시간, TR:지역, B:제목
            const htmlLeft = `<span style="color:#212529; font-weight:800;">${{timeTxt}}</span>`;
            const htmlRight = `<span style="color:${{color}}; font-weight:800;">${{region}}</span>`;
            const htmlBottom = `<span style="color:#495057; font-weight:500;">${{title}}</span>`;

            let rGroup = "others";
            if(region.includes("서울")) rGroup = "seoul";
            else if(region.includes("경기") || region.includes("인천")) rGroup = "gyeonggi";

            return `
            <div class="event-box" data-region="${{rGroup}}" data-genre="${{genre}}" 
                 title="[${{region}}] ${{title}}\\n장소: ${{place}}\\n장르: ${{genre}}\\n시간: ${{row['오픈일시']}}">
                <div class="event-header">
                    <div>${{htmlLeft}}</div>
                    <div>${{htmlRight}}</div>
                </div>
                <span class="box-line2">${{htmlBottom}}</span>
            </div>`;
        }}

        function renderCalendar(year, month) {{
            // 제목 업데이트
            titleEl.textContent = `${{year}}년 ${{month}}월`;
            
            // 달력 계산
            const firstDay = new Date(year, month - 1, 1);
            const lastDay = new Date(year, month, 0);
            
            const startDayIdx = firstDay.getDay(); // 0(일) ~ 6(토)
            const totalDays = lastDay.getDate();

            let html = "";
            let dayCount = 1;
            let rowHtml = "<tr>";

            // 첫 주 빈칸 채우기
            for (let i = 0; i < startDayIdx; i++) {{
                rowHtml += "<td></td>";
            }}

            // 날짜 채우기
            for (let i = startDayIdx; i < 7; i++) {{
                rowHtml += createTd(year, month, dayCount, i);
                dayCount++;
            }}
            rowHtml += "</tr>";
            html += rowHtml;

            // 나머지 주 채우기
            while (dayCount <= totalDays) {{
                rowHtml = "<tr>";
                for (let i = 0; i < 7; i++) {{
                    if (dayCount > totalDays) {{
                        rowHtml += "<td></td>";
                    }} else {{
                        rowHtml += createTd(year, month, dayCount, i);
                        dayCount++;
                    }}
                }}
                rowHtml += "</tr>";
                html += rowHtml;
            }}

            tbodyEl.innerHTML = html;
            
            // 렌더링 후 필터 적용
            applyFilter();
        }}

        function createTd(year, month, day, weekIdx) {{
            // 주말 클래스
            let tdClass = "";
            if (weekIdx === 0) tdClass = "sun";
            else if (weekIdx === 6) tdClass = "sat";

            // 해당 날짜의 이벤트 찾기
            const dayEvents = allEvents.filter(e => e.Year === year && e.Month === month && e.Day === day);
            
            // has-event / no-event (초기 로딩용 힌트)
            const eventClass = dayEvents.length > 0 ? "has-event" : "no-event";
            const dayName = getDayName(weekIdx);

            let content = `<span class="date-num" data-dayname="${{dayName}}">${{day}}</span>`;
            
            dayEvents.forEach(evt => {{
                content += getEventHtml(evt);
            }});

            return `<td class="${{tdClass}} ${{eventClass}}">${{content}}</td>`;
        }}

        // 설정 저장/로드
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

        // 필터링 로직 (모바일 스타일 적용 포함)
        function applyFilter() {{
            const selectedRegions = Array.from(regionChks).filter(c => c.checked).map(c => c.value);
            const selectedGenres = Array.from(genreChks).filter(c => c.checked).map(c => c.value);
            
            saveSettings();

            const allTds = tbodyEl.querySelectorAll('td');

            // 1. 초기 모드 (지역 미선택)
            if (selectedRegions.length === 0) {{
                document.body.classList.add('initial-mode');
                document.querySelectorAll('.event-box').forEach(el => el.style.display = 'none');
                allTds.forEach(td => {{
                    td.classList.remove('day-active');
                    td.classList.add('day-inactive');
                }});
                return;
            }} else {{
                document.body.classList.remove('initial-mode');
            }}

            // 2. 일반 모드
            allTds.forEach(td => {{
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

        // 이벤트 리스너
        prevBtn.addEventListener('click', () => {{
            currMonth--;
            if (currMonth < 1) {{ currMonth = 12; currYear--; }}
            renderCalendar(currYear, currMonth);
        }});

        nextBtn.addEventListener('click', () => {{
            currMonth++;
            if (currMonth > 12) {{ currMonth = 1; currYear++; }}
            renderCalendar(currYear, currMonth);
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

        // 초기 실행
        loadSettings();
        renderCalendar(currYear, currMonth);
        
    </script>
</body>
</html>
        """
        
        filename = "index.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"생성 완료: {filename}")
        push_to_github()

    except Exception as e:
        print(f"작업 중 오류 발생: {e}")

if __name__ == "__main__":
    main()