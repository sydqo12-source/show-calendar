import os
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from supabase import create_client, Client

# --- [설정 1] 구글 색인 API 설정 ---
KEY_FILE = 'service_account.json'
SCOPES = ["https://www.googleapis.com/auth/indexing"]

# --- [설정 2] Supabase 설정 (index.html에 있던 정보) ---
SUPABASE_URL = 'https://btvwssnlrwvzgqdbcuti.supabase.co'
# 주의: 이 키는 공개되어도 되는 Anon 키입니다. (읽기 전용이라 안전)
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ0dndzc25scnd2emdxZGJjdXRpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc1MjczMDIsImV4cCI6MjA4MzEwMzMwMn0.NF-nG9Dtwe__p5Xmzz4dmFT56B4XN77oBJlJxnPnDdM'

def request_indexing(url):
    """구글에 해당 URL 색인 요청을 보냅니다."""
    try:
        credentials = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
        service = build('indexing', 'v3', credentials=credentials)
        body = {"url": url, "type": "URL_UPDATED"}
        service.urlNotifications().publish(body=body).execute()
        print(f"✅ [성공] 구글에 신고 완료: {url}")
    except Exception as e:
        print(f"❌ [실패] {e}")

def get_latest_event_id():
    """Supabase에서 가장 최근에 등록된 공연 ID 하나를 가져옵니다."""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 'events' 테이블에서, 'created_at' 기준으로 내림차순 정렬해서 1개만 가져옴
        # (만약 created_at 컬럼이 없다면 id 기준으로 정렬합니다)
        response = supabase.table('events').select('id').order('id', desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        else:
            return None
    except Exception as e:
        print(f"❌ Supabase 조회 실패: {e}")
        return None

# --- 실행 부분 ---
if __name__ == "__main__":
    print("\n🔎 최신 공연 정보를 조회합니다...")
    
    # 1. 알아서 최신 ID를 가져옴
    latest_id = get_latest_event_id()
    
    if latest_id:
        print(f"👉 발견된 최신 공연 ID: {latest_id}")
        target_url = f"https://showkok.com/?id={latest_id}"
        
        # 2. 바로 색인 요청 날림
        request_indexing(target_url)
    else:
        print("🤔 DB에 데이터가 없거나 연결할 수 없습니다.")