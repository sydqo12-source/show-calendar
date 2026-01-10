// sw.js

// ==========================================
// 1. Firebase 알림 설정 (맨 위에 추가됨)
// ==========================================
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging-compat.js');

const firebaseConfig = {
  apiKey: "AIzaSyCc1GvgMaWHZtAa_zTRqL0fj3l5B4zzg50",
  authDomain: "showkok.firebaseapp.com",
  projectId: "showkok",
  storageBucket: "showkok.firebasestorage.app",
  messagingSenderId: "42586284108",
  appId: "1:42586284108:web:f2020d0452b02fa23554e9",
  measurementId: "G-HXGN9LHRJT"
};

firebase.initializeApp(firebaseConfig);

const messaging = firebase.messaging();

// 앱이 꺼져있을 때(백그라운드) 알림 처리
messaging.onBackgroundMessage(function(payload) {
  console.log('백그라운드 메시지 수신:', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/icon-192.png' // 알림에 뜰 아이콘
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// ==========================================
// 2. 기존 캐싱 로직 (원래 있던 코드 유지)
// ==========================================
const CACHE_NAME = 'showkok-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
  // 여기에 필요한 이미지나 CSS 파일이 더 있으면 추가하면 됩니다.
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});