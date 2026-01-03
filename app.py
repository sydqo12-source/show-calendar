import streamlit as st
import pandas as pd

st.set_page_config(page_title="티켓 오픈 비서", layout="wide")

st.title("📅 티켓 오픈 일정 목록")
st.write("인터파크 공지사항에서 추출한 실시간 예매 일정입니다.")

try:
    df = pd.read_csv('공연목록_오픈예정.csv')
    
    # 표 형태로 깔끔하게 출력
    # 인덱스(0, 1, 2...)를 숨기고 순위, 오픈일시, 제목만 보여줌
    st.table(df[['오픈일시', '제목', '링크']])

except FileNotFoundError:
    st.error("데이터 파일이 없습니다. crawler.py를 먼저 실행하세요.")