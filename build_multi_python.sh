#!/bin/bash
# PySide6 멀티 Python 버전 빌드 스크립트

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_ROOT="$SCRIPT_DIR"
INSTALL_ROOT="/core/Linux/APPZ/packages/pyside6/6.9.1"

# 빌드할 Python 버전들 정의
PYTHON_VERSIONS=(
    "3.9.21"
    "3.10.6" 
    "3.11.9"
    "3.12.10"
    "3.13.2"
)

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛠️  PySide6 Multi-Python Version Build${NC}"
echo "=================================================="

# 기존 설치 정리
echo -e "${YELLOW}🧹 Cleaning existing installation...${NC}"
if [ -d "$INSTALL_ROOT" ]; then
    rm -rf "$INSTALL_ROOT/lib/python*"
    echo "   Removed existing Python-specific directories"
fi

# 각 Python 버전별로 빌드
for python_version in "${PYTHON_VERSIONS[@]}"; do
    echo ""
    echo -e "${GREEN}🐍 Building PySide6 for Python ${python_version}...${NC}"
    echo "--------------------------------------------------"
    
    # Python 버전에서 메이저.마이너 추출
    python_major_minor=$(echo "$python_version" | cut -d'.' -f1,2)
    python_path="/core/Linux/APPZ/packages/python/${python_version}/bin/python3"
    
    # Python 존재 확인
    if [ ! -f "$python_path" ]; then
        echo -e "${RED}❌ Python ${python_version} not found at ${python_path}${NC}"
        continue
    fi
    
    echo -e "${BLUE}   Using Python: ${python_path}${NC}"
    
    # 빌드 환경 설정
    export REZ_BUILD_SOURCE_PATH="$BUILD_ROOT"
    export REZ_BUILD_PATH="$BUILD_ROOT/build_py${python_major_minor}"
    export REZ_BUILD_INSTALL_PATH="$INSTALL_ROOT"
    export REZ_BUILD_PROJECT_VERSION="6.9.1"
    export PYTHON_VERSION="$python_version"
    export PYTHON_MAJOR_MINOR="$python_major_minor"
    
    # 빌드 디렉토리 생성
    mkdir -p "$REZ_BUILD_PATH"
    
    echo -e "${BLUE}   Build directory: ${REZ_BUILD_PATH}${NC}"
    echo -e "${BLUE}   Install directory: ${REZ_BUILD_INSTALL_PATH}${NC}"
    
    # rez 환경에서 빌드 실행
    echo -e "${YELLOW}   🔧 Starting build...${NC}"
    
    if rez-env \
        gcc-11.5.0 \
        cmake-3.26.5 \
        ninja-1.11.1 \
        qt-6.9.1 \
        python-${python_version} \
        shiboken6-6.9.1 \
        numpy-1.26.4 \
        minizip_ng-4.0.10 \
        -- python rezbuild_multi.py install "$python_version"; then
        
        echo -e "${GREEN}   ✅ Python ${python_version} build completed successfully${NC}"
    else
        echo -e "${RED}   ❌ Python ${python_version} build failed${NC}"
        # 실패해도 다른 버전 계속 진행
    fi
done

echo ""
echo -e "${GREEN}🎉 Multi-Python PySide6 build completed!${NC}"
echo "=================================================="

# 최종 검증
echo -e "${BLUE}🧪 Verifying installations...${NC}"
for python_version in "${PYTHON_VERSIONS[@]}"; do
    python_major_minor=$(echo "$python_version" | cut -d'.' -f1,2)
    python_dir="$INSTALL_ROOT/lib/python${python_major_minor}/site-packages"
    
    if [ -d "$python_dir/PySide6" ]; then
        echo -e "${GREEN}   ✅ Python ${python_major_minor}: PySide6 installed${NC}"
    else
        echo -e "${RED}   ❌ Python ${python_major_minor}: PySide6 missing${NC}"
    fi
done

echo ""
echo -e "${BLUE}📋 Usage:${NC}"
echo "   rez-env python-3.9.21 pyside6-6.9.1 -- python -c \"import PySide6.QtCore\""
echo "   rez-env python-3.10.6 pyside6-6.9.1 -- python -c \"import PySide6.QtCore\""
echo "   rez-env python-3.11.9 pyside6-6.9.1 -- python -c \"import PySide6.QtCore\""
echo "   rez-env python-3.12.10 pyside6-6.9.1 -- python -c \"import PySide6.QtCore\""
echo "   rez-env python-3.13.2 pyside6-6.9.1 -- python -c \"import PySide6.QtCore\""