#!/bin/bash

echo "🛑 SpotSync 서버 종료 중..."

fuser -k 8001/tcp 2>/dev/null && echo "   ✅ 백엔드 (8001) 종료" || echo "   ⚪ 백엔드 이미 꺼져있음"
fuser -k 3000/tcp 2>/dev/null && echo "   ✅ 프론트엔드 (3000) 종료" || echo "   ⚪ 프론트엔드 이미 꺼져있음"

echo ""
echo "✅ 종료 완료!"
