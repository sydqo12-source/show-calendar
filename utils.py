import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

def request_indexing(url):
     """
     구글 Indexing API에 URL 업데이트(수집) 요청을 보냅니다.
     :param url: 색인 요청할 전체 URL (예: https://showkok.com/?id=999)
     """
     # 서비스 계정 키 파일 경로 (같은 폴더에 있다고 가정)
     KEY_FILE = 'service_account.json'
     
     # Indexing API 스코프
     SCOPES = ["https://www.googleapis.com/auth/indexing"]

     try:
          # 1. 인증 정보 로드
          credentials = service_account.Credentials.from_service_account_file(
               KEY_FILE, scopes=SCOPES
          )

          # 2. 서비스 객체 빌드
          service = build('indexing', 'v3', credentials=credentials)

          # 3. 요청 바디 생성 (URL_UPDATED: 새 페이지 생성 또는 수정 시)
          body = {
               "url": url,
               "type": "URL_UPDATED"
          }

          # 4. API 호출
          response = service.urlNotifications().publish(body=body).execute()

          # 5. 결과 출력 (성공 시 확인용)
          print(f"✅ 구글 색인 요청 성공: {url}")
          print(f"   응답: {response}")

     except Exception as e:
          print(f"❌ 구글 색인 요청 실패: {e}")

# --- 사용 예시 ---
if __name__ == "__main__":
     # 아이유 콘서트 ID가 999라고 가정할 때
     new_concert_url = "https://showkok.com/?id=999"
     request_indexing(new_concert_url)