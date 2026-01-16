// 파일명: sw.js
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging-compat.js');

// 1. Firebase 설정 (HTML에 있던 것과 똑같아야 함)
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

// 앱이 꺼져있을 때 알림이 오면 이 함수가 실행됩니다.
messaging.onBackgroundMessage(function(payload) {
  console.log('[firebase-messaging-sw.js] 백그라운드 메시지 수신 ', payload);
  
  // 알림 제목과 내용 설정
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/icon-192.png', // 아이콘 경로 (없으면 지워도 됨)
    badge: '/icon-192.png' // 상단 바 뱃지 (없으면 지워도 됨)
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});