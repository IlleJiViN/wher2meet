import { NextResponse } from 'next/server';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q');
  
  if (!q) return NextResponse.json({ error: "Missing query" }, { status: 400 });

  try {
    // 백엔드에서 우회하여 Nominatim API 호출 (모바일 브라우저의 엄격한 CORS/User-Agent 차단 회피)
    const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=1&countrycodes=kr`, {
      headers: {
        'User-Agent': 'SpotSync/1.0 (local-test)',
        'Accept-Language': 'ko-KR,ko;q=0.9'
      }
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Geocode error" }, { status: 500 });
  }
}
