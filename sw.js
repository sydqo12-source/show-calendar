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

// 3. 백그라운드 메시지 처리기
const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  console.log('[firebase-messaging-sw.js] 백그라운드 메시지 수신 ', payload);
  const data = payload.data || payload.notification;

  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: 'https://showkok.com/icon-192.png', // ★중요: 이 경로에 실제 이미지 파일이 없으면 알림이 안 뜰 수 있습니다. 확인하세요!
    badge: 'https://showkok.com/icon.png',
    data: {
      url: data.url 
    }
    // data: payload.data // 클릭 시 이동할 URL 등을 담을 수 있습니다.
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// ★★★ [추가된 부분] 알림 클릭 이벤트 처리 ★★★
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  // 알림에 심어둔 URL 꺼내기 (없으면 메인으로)
  const targetUrl = event.notification.data && event.notification.data.url 
                    ? event.notification.data.url 
                    : 'https://showkok.com';
  // 2. 앱(창) 열기 또는 포커스 잡기
  event.waitUntil(
    clients.matchAll({type: 'window'}).then(function(clientList) {
      // 이미 열려있는 창이 있으면 그 창을 앞으로 띄움
      for (var i = 0; i < clientList.length; i++) {
        var client = clientList[i];
        if (client.url.includes('showkok.com') && 'focus' in client) {
          return client.focus().then(c => c.navigate(targetUrl)); // 열려있으면 거기로 이동
        }
      }
      // 열려있는 창이 없으면 새로 셤
      if (clients.openWindow) {
        return clients.openWindow('https://showkok.com'); 
      }
    })
  );
});