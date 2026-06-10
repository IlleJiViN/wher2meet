'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, MapPin, Share2, ExternalLink } from 'lucide-react';

export default function ResultsBottomSheet({ results, onClose, onShare }) {
  if (!results) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: "100%" }}
        animate={{ y: 0 }}
        exit={{ y: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-white rounded-t-[32px] shadow-[0_-10px_40px_rgba(0,0,0,0.1)] z-50 h-[85vh] flex flex-col"
      >
        {/* Drag handle area */}
        <div className="flex-none pt-4 pb-2 flex justify-center items-center relative">
          <div className="w-12 h-1.5 bg-gray-200 rounded-full"></div>
          <button 
            onClick={onClose}
            className="absolute right-4 p-2 bg-gray-100 rounded-full text-gray-500 hover:bg-gray-200 active:scale-95 transition-all"
          >
            <X size={20} />
          </button>
        </div>

        {/* Header */}
        <div className="px-6 pb-4 border-b border-gray-100">
          <h2 className="text-[22px] font-bold text-[#191f28] flex items-center">
            ✨ 추천 모임 장소 
            <span className="bg-[#e8f3ff] text-[#3182f6] text-[15px] px-2.5 py-0.5 rounded-lg ml-3">
              {results.length}곳
            </span>
          </h2>
          <p className="text-[#8b95a1] text-[14px] mt-1.5 font-medium">모두가 만족할 수 있는 최적의 중간 지점입니다.</p>
        </div>

        {/* Scrollable Results List */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 pb-10">
          {results.length === 0 ? (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                <span className="text-4xl">🥲</span>
              </div>
              <p className="text-[#505967] font-bold text-[17px]">조건에 맞는 장소를 찾지 못했어요.</p>
              <p className="text-[#8b95a1] text-[14px] mt-2">검색어의 까다로움 정도를 조절하거나<br/>다른 키워드로 검색해보세요.</p>
            </div>
          ) : (
            results.map((res, idx) => (
              <div key={res.place_id} className="bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)] rounded-2xl flex flex-col relative overflow-hidden group hover:shadow-[0_4px_20px_rgba(0,0,0,0.08)] transition-shadow">
                <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-blue-50 to-transparent rounded-bl-full opacity-60 pointer-events-none"></div>
                
                <div className="p-5 z-10">
                  <div className="flex justify-between items-start">
                    <div className="flex-1 pr-4">
                      <div className="flex items-center space-x-2.5 mb-1.5">
                        <span className={`text-[13px] font-extrabold px-2 py-0.5 rounded-lg ${idx === 0 ? 'bg-[#3182f6] text-white shadow-sm shadow-blue-500/20' : 'bg-[#f2f4f6] text-[#505967]'}`}>
                          {idx + 1}위
                        </span>
                        <h3 className="text-[19px] font-bold text-[#191f28] leading-tight break-keep">{res.name}</h3>
                      </div>
                      <p className="text-[#8b95a1] text-[13px] font-medium inline-block bg-gray-50 px-2 py-0.5 rounded">{res.category}</p>
                    </div>
                    
                    <div className="text-right shrink-0 flex flex-col items-end">
                      <div className="bg-[#e8f3ff] px-2.5 py-1 rounded-xl">
                        <p className="text-[#3182f6] font-bold text-[15px]">{(res.distance_meters / 1000).toFixed(1)}km</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-[#f9fafb] p-3.5 rounded-xl mt-4 flex flex-col space-y-3">
                    <div className="flex items-start space-x-2">
                      <MapPin size={16} className="text-[#8b95a1] mt-0.5 shrink-0" />
                      <p className="text-[#505967] text-[14px] leading-snug flex-1 break-keep">{res.address}</p>
                    </div>
                    
                    <div className="flex space-x-2 pt-1.5">
                      <button
                        onClick={() => onShare(res, idx)}
                        className="flex-none bg-white border border-gray-200 text-[#505967] hover:bg-gray-50 px-4 py-2.5 rounded-xl text-[14px] font-bold text-center transition-colors flex items-center justify-center"
                      >
                        <Share2 size={16} className="mr-1.5" />
                        공유
                      </button>
                      <a 
                        href={`https://map.kakao.com/link/search/${encodeURIComponent(res.address + ' ' + res.name)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 bg-[#fee500] text-[#391b1b] hover:bg-[#e6cf00] py-2.5 rounded-xl text-[14px] font-bold text-center transition-colors flex items-center justify-center shadow-sm"
                      >
                        <ExternalLink size={16} className="mr-1.5 opacity-60" />
                        카카오 지도
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
