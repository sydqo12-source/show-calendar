// 파일명: sw.js
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging-compat.js');

// 1. Firebase 설정
const firebaseConfig = {
    apiKey: "AIzaSyCc1GvgMaWHZtAa_zTRqL0fj3l5B4zzg50",
    authDomain: "showkok.firebaseapp.com",
    projectId: "showkok",
    storageBucket: "showkok.firebasestorage.app",
    messagingSenderId: "42586284108",
    appId: "1:42586284108:web:f2020d0452b02fa23554e9",
    measurementId: "G-HXGN9LHRJT"
};

// 2. 앱 초기화
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// ❌ [삭제됨] messaging.onBackgroundMessage(...) 
// 이유: 이제 서버가 보낸 'webpush' 설정 덕분에 안드로이드가 알아서 알림을 띄워줍니다.
// 여기서 또 띄우면 알림이 2개가 오기 때문에 지웠습니다.

// 3. [유지] 알림 클릭 이벤트 처리 (앱 열기 & 포커스)
self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  // 서버에서 보낸 data.url이 있으면 쓰고, 없으면 메인으로
  const targetUrl = event.notification.data && event.notification.data.url 
                    ? event.notification.data.url 
                    : 'https://showkok.com';

  // 앱(창) 열기 로직
  event.waitUntil(
    clients.matchAll({type: 'window'}).then(function(clientList) {
      // 이미 열려있는 창이 있으면 그 창을 앞으로 띄움
      for (var i = 0; i < clientList.length; i++) {
        var client = clientList[i];
        if (client.url.includes('showkok.com') && 'focus' in client) {
          return client.focus().then(c => c.navigate(targetUrl)); 
        }
      }
      // 열려있는 창이 없으면 새로 열기
      if (clients.openWindow) {
        return clients.openWindow(targetUrl); 
      }
    })
  );
});