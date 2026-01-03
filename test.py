# [1] 윈도우 버그 해결 코드 (이 2줄을 가장 위에 쓰세요)
import mimetypes
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

import streamlit as st
st.write("메롱")