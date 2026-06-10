#!/bin/bash

DOCKER_EXE="/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"

echo "🚀 SpotSync 서버 시작 중..."

# 1. Docker PostGIS DB 실행
echo "🗄️  DB (PostGIS Docker) 시작 중..."
"$DOCKER_EXE" start spotsync-postgis 2>/dev/null
sleep 3
if "$DOCKER_EXE" ps --format '{{.Names}}' 2>/dev/null | grep -q spotsync-postgis; then
  echo "   ✅ PostGIS Docker 실행 중"
else
  echo "   ❌ PostGIS Docker 시작 실패! Docker Desktop이 켜져있는지 확인하세요."
  exit 1
fi

# 2. FastAPI 백엔드 백그라운드 실행
echo "📡 백엔드 (FastAPI) 시작 중... (포트 8001)"
fuser -k 8001/tcp 2>/dev/null
./venv/bin/uvicorn ai_search:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!
echo "   ✅ 백엔드 PID: $BACKEND_PID"

# 3. Next.js 프론트엔드 백그라운드 실행
echo "🌐 프론트엔드 (Next.js) 시작 중... (포트 3000)"
fuser -k 3000/tcp 2>/dev/null
export NVM_DIR="$HOME/.nvm"
source "$NVM_DIR/nvm.sh"
cd frontend && npm run dev -- -p 3000 &
FRONTEND_PID=$!
echo "   ✅ 프론트엔드 PID: $FRONTEND_PID"

echo ""
echo "========================================="
echo "  🎉 서버 준비 완료! (AI 모델 로딩 약 20초 소요)"
echo "  👉 브라우저에서 http://localhost:3000 접속"
echo "========================================="
echo ""
echo "  종료하려면 Ctrl+C 를 누르세요."
echo ""

# Ctrl+C 누르면 두 서버 모두 종료
trap "echo ''; echo '🛑 서버 종료 중...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '✅ 종료 완료'; exit 0" SIGINT SIGTERM

# 두 프로세스가 살아있는 동안 대기
wait $BACKEND_PID $FRONTEND_PID
