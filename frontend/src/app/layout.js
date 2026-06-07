import "./globals.css";

export const metadata = {
  title: "SpotSync | 모두가 공평한 모임 장소",
  description: "여러 출발지에서 가장 공평하고 최적화된 모임 장소를 AI로 찾아보세요.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" />
        <script src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.2/kakao.min.js" crossOrigin="anonymous"></script>
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
