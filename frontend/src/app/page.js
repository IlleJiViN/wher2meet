'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

const MapComponent = dynamic(() => import('./MapComponent'), { 
  ssr: false, 
  loading: () => <div className="w-full h-[320px] bg-gray-100 rounded-2xl flex items-center justify-center text-gray-400 font-medium">지도를 불러오는 중...</div> 
});

export default function Home() {
  const [origins, setOrigins] = useState([]);
  const [newOrigin, setNewOrigin] = useState('');
  const [keyword, setKeyword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [results, setResults] = useState(null);
  const [threshold, setThreshold] = useState(0.40);

  const loadingMessages = [
    "위치 기반 최적 중심점 연산 중...",
    "AI 시맨틱 임베딩 및 카테고리 매칭 중...",
    "후보 장소 공간 데이터베이스 필터링 중...",
    "가장 공평한 장소 최종 스코어링 중..."
  ];

  useEffect(() => {
    if (typeof window !== 'undefined' && window.Kakao && !window.Kakao.isInitialized()) {
      window.Kakao.init('1615ae46bd96dd33b598163becc2a353');
    }
    
    let interval;
    if (isLoading && !newOrigin) {
      let idx = 0;
      setProgressMsg(loadingMessages[0]);
      interval = setInterval(() => {
        idx = (idx + 1) % loadingMessages.length;
        setProgressMsg(loadingMessages[idx]);
      }, 700); // 0.7초마다 메시지 변경
    } else {
      setProgressMsg('');
    }
    return () => clearInterval(interval);
  }, [isLoading, newOrigin]);

  const addOrigin = async () => {
    if (newOrigin.trim() === '') return;
    
    setIsLoading(true);
    try {
      const res = await fetch(`/api/geocode?q=${encodeURIComponent(newOrigin)}`);
      const data = await res.json();
      if (data && data.length > 0) {
        setOrigins([
          ...origins, 
          { 
            id: Date.now(), 
            name: newOrigin, 
            address: data[0].display_name.split(',').slice(0,2).join(','), 
            latitude: parseFloat(data[0].lat), 
            longitude: parseFloat(data[0].lon), 
            weight: 1.0 
          }
        ]);
        setNewOrigin('');
      } else {
        alert("주소를 찾을 수 없습니다.");
      }
    } catch (e) {
      alert("주소 검색 오류가 발생했습니다.");
    }
    setIsLoading(false);
  };

  const removeOrigin = (id) => setOrigins(origins.filter(o => o.id !== id));
  
  const updateWeight = (id, delta) => {
    setOrigins(origins.map(o => {
      if (o.id === id) {
        const newWeight = Math.max(1.0, Math.min(5.0, o.weight + delta));
        return { ...o, weight: newWeight };
      }
      return o;
    }));
  };

  const handleSearch = async () => {
    if (origins.length === 0) {
      alert("출발지를 추가해주세요.");
      return;
    }
    if (!keyword) {
      alert("검색어를 입력해주세요.");
      return;
    }
    
    setIsLoading(true);
    setResults(null);
    try {
      const payload = {
        query: keyword,
        users: origins.map(o => ({
          name: o.name,
          latitude: o.latitude,
          longitude: o.longitude,
          weight: o.weight
        })),
        radius_meters: 15000,
        similarity_threshold: threshold,
        top_k: 7
      };
      
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) throw new Error("API Error");
      const data = await res.json();
      setResults(data.results);
    } catch (e) {
      alert("검색 중 오류가 발생했습니다.");
    }
    setIsLoading(false);
  };

  const handleShare = (res, idx) => {
    if (typeof window !== 'undefined' && window.Kakao) {
      window.Kakao.Share.sendDefault({
        objectType: 'location',
        address: res.address,
        addressTitle: res.name,
        content: {
          title: `[${idx + 1}위 추천] ${res.name}`,
          description: `SpotSync AI 추천 공평한 모임 장소\n카테고리: ${res.category}`,
          imageUrl: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80',
          link: {
            mobileWebUrl: window.location.href || 'http://localhost:3000',
            webUrl: window.location.href || 'http://localhost:3000',
          },
        },
        buttons: [
          {
            title: 'SpotSync에서 자세히 보기',
            link: {
              mobileWebUrl: window.location.href || 'http://localhost:3000',
              webUrl: window.location.href || 'http://localhost:3000',
            },
          },
        ],
      });
    } else {
      alert("카카오톡 공유 모듈을 불러오는 중입니다. 잠시 후 다시 시도해주세요.");
    }
  };

  return (
    <main className="min-h-screen max-w-md mx-auto bg-[#f2f4f6] pb-32 relative overflow-x-hidden">
      {/* Header */}
      <header className="pt-16 pb-8 px-6">
        <h1 className="text-[32px] font-bold text-[#191f28] leading-[1.3] tracking-tight">
          어디서 만날까요?<br/>
          <span className="text-[#3182f6]">SpotSync</span>가<br/>찾아드릴게요
        </h1>
      </header>

      {/* Origin Section */}
      <section className="px-6 space-y-4">
        {origins.map((origin) => (
          <div key={origin.id} className="toss-card flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-[#e8f3ff] rounded-full flex items-center justify-center text-xl shadow-inner shrink-0">
                📍
              </div>
              <div className="max-w-[150px]">
                <p className="text-[#191f28] font-bold text-[17px] truncate">{origin.name}</p>
                <div className="flex items-center mt-1 space-x-2">
                  <span className="text-[#3182f6] text-[13px] font-bold bg-[#e8f3ff] px-2 py-0.5 rounded-md">가중치 {origin.weight.toFixed(1)}x</span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className="flex bg-gray-100 rounded-xl overflow-hidden">
                <button onClick={() => updateWeight(origin.id, -0.5)} className="text-[#505967] hover:bg-gray-200 px-3 py-2 font-bold transition-colors">-</button>
                <button onClick={() => updateWeight(origin.id, 0.5)} className="text-[#505967] hover:bg-gray-200 px-3 py-2 font-bold transition-colors">+</button>
              </div>
              <button onClick={() => removeOrigin(origin.id)} className="text-[#8b95a1] p-2 hover:bg-gray-200 rounded-full transition-colors active:scale-95">
                ✕
              </button>
            </div>
          </div>
        ))}

        {/* Add Origin Input */}
        <div className="toss-card space-y-5 mt-2 border-dashed border-2 border-gray-200 bg-white/50">
          <h2 className="text-[18px] font-bold text-[#191f28]">출발지 추가</h2>
          <div className="flex space-x-2">
            <input 
              type="text" 
              placeholder="역 이름 (예: 강남역)"
              className="toss-input flex-1"
              value={newOrigin}
              onChange={(e) => setNewOrigin(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addOrigin()}
            />
            <button disabled={isLoading} onClick={addOrigin} className="bg-[#f2f4f6] text-[#3182f6] px-5 rounded-2xl font-bold text-lg hover:bg-[#e8eaed] transition-colors active:scale-95 disabled:opacity-50">
              {isLoading && newOrigin ? '...' : '추가'}
            </button>
          </div>
        </div>
      </section>

      {/* Map Section */}
      {(origins.length > 0 || results) && (
        <section className="px-6 mt-6">
          <MapComponent origins={origins} results={results} />
        </section>
      )}

      {/* AI Search Section */}
      <section className="px-6 mt-6">
        <div className="toss-card space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-[28px]">🤖</span>
              <h2 className="text-[20px] font-bold text-[#191f28]">어떤 장소를 찾으시나요?</h2>
            </div>
          </div>
          <input 
            type="text" 
            placeholder="예: 분위기 좋은 고깃집"
            className="toss-input bg-[#f9fafb]"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
          <div className="pt-2 border-t border-gray-100">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[14px] font-bold text-[#505967]">AI 검색 까다로움 정도</span>
              <span className="text-[13px] text-[#3182f6] font-bold bg-[#e8f3ff] px-2 py-0.5 rounded">
                {threshold < 0.4 ? '보통 (폭넓게)' : threshold < 0.6 ? '정확함 (추천)' : '매우 까다로움'}
              </span>
            </div>
            <input 
              type="range" 
              min="0.2" max="0.75" step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#3182f6]"
            />
          </div>
        </div>
      </section>

      {/* Results Section */}
      {results && (
        <section className="px-6 mt-6 pb-8 space-y-4">
          <h2 className="text-[22px] font-bold text-[#191f28] mb-4 flex items-center">
            ✨ 추천 모임 장소 <span className="text-[#3182f6] ml-2">{results.length}</span>
          </h2>
          {results.length === 0 ? (
            <div className="toss-card py-8 text-center">
              <span className="text-4xl mb-2 block">🥲</span>
              <p className="text-[#505967] font-medium">조건에 맞는 장소를 찾지 못했어요.</p>
            </div>
          ) : (
            results.map((res, idx) => (
              <div key={res.place_id} className="toss-card flex flex-col space-y-3 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl from-blue-50 to-transparent rounded-bl-full opacity-50"></div>
                <div className="flex justify-between items-start z-10">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className={`text-[13px] font-bold px-2 py-0.5 rounded-md ${idx === 0 ? 'bg-[#3182f6] text-white' : 'bg-[#e8f3ff] text-[#3182f6]'}`}>
                        {idx + 1}위
                      </span>
                      <h3 className="text-[19px] font-bold text-[#191f28]">{res.name}</h3>
                    </div>
                    <p className="text-[#8b95a1] text-[14px] mt-1.5 font-medium">{res.category}</p>
                  </div>
                  <div className="text-right pl-3">
                    <p className="text-[#3182f6] font-bold text-[16px]">{(res.distance_meters / 1000).toFixed(1)}km</p>
                    <p className="text-[#b0b8c1] text-[12px] mt-0.5">중심점 거리</p>
                  </div>
                </div>
                <div className="bg-[#f9fafb] p-3 rounded-xl mt-2 flex flex-col space-y-3">
                  <div className="flex items-start space-x-2">
                    <span className="text-[#8b95a1] mt-0.5 text-sm">📍</span>
                    <p className="text-[#505967] text-[14px] leading-snug flex-1">{res.address}</p>
                  </div>
                  <div className="flex space-x-2 pt-1">
                    <button
                      onClick={() => handleShare(res, idx)}
                      className="flex-none bg-[#3182f6]/10 text-[#3182f6] hover:bg-[#3182f6]/20 px-4 py-2 rounded-lg text-[13px] font-bold text-center transition-colors"
                    >
                      공유
                    </button>
                    <a 
                      href={`https://map.naver.com/v5/search/${encodeURIComponent(res.address + ' ' + res.name)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 bg-[#03c75a]/10 text-[#03c75a] hover:bg-[#03c75a]/20 py-2 rounded-lg text-[13px] font-bold text-center transition-colors"
                    >
                      네이버 지도
                    </a>
                    <a 
                      href={`https://map.kakao.com/link/search/${encodeURIComponent(res.address + ' ' + res.name)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 bg-[#fee500]/30 text-[#391b1b] hover:bg-[#fee500]/50 py-2 rounded-lg text-[13px] font-bold text-center transition-colors"
                    >
                      카카오 지도
                    </a>
                  </div>
                </div>
              </div>
            ))
          )}
        </section>
      )}

      {/* Fixed Bottom Button */}
      <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto p-6 bg-gradient-to-t from-[#f2f4f6] via-[#f2f4f6] to-transparent pointer-events-none z-50">
        <div className="pointer-events-auto pb-4">
          <button onClick={handleSearch} disabled={isLoading} className="toss-button shadow-2xl shadow-blue-500/20 py-4 text-[18px] disabled:opacity-50 flex flex-col items-center justify-center min-h-[64px]">
            {isLoading && !newOrigin ? (
              <>
                <div className="flex items-center space-x-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span className="font-bold">AI 엔진이 고민하는 중...</span>
                </div>
                <span className="text-blue-100 text-[13px] font-medium mt-1 animate-pulse">{progressMsg}</span>
              </>
            ) : (
              <span className="font-bold">가장 공평한 장소 찾기</span>
            )}
          </button>
        </div>
      </div>
    </main>
  );
}
