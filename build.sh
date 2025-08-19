#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# 0) devtoolset-14 경로 제거 (ld.bfd 충돌 방지)
# -----------------------------------------------------------------------------
OLD_PATH="$PATH"
PATH="$(printf "%s\n" "$OLD_PATH" | tr ':' '\n' \
       | grep -v '/opt/rh/gcc-toolset-14' \
       | paste -sd ':' -)"
export PATH
unset LD_LIBRARY_PATH

# -----------------------------------------------------------------------------
# 1) 필수 툴 검사 (ldconfig 는 특별 처리)
# -----------------------------------------------------------------------------
# ldconfig 는 /sbin, /usr/sbin 도 검사
if ! LDCONFIG_CMD=$(command -v ldconfig 2>/dev/null); then
  if [ -x /sbin/ldconfig ]; then
    LDCONFIG_CMD=/sbin/ldconfig
  elif [ -x /usr/sbin/ldconfig ]; then
    LDCONFIG_CMD=/usr/sbin/ldconfig
  else
    echo "❌ ldconfig not found"
    exit 1
  fi
fi
echo "🔍 ldconfig: ${LDCONFIG_CMD}"
# ldconfig 디렉터리를 PATH 앞으로 추가
export PATH="$(dirname "$LDCONFIG_CMD"):${PATH}"

# 나머지 툴들은 PATH 상에서 찾습니다
for cmd in ninja cmake qmake qtpaths6 pkg-config python3.13 clang clang++ ar nm; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "❌ $cmd not found"
    exit 1
  fi
done

# -----------------------------------------------------------------------------
# 2) Clang 리소스 헤더 위치
# -----------------------------------------------------------------------------
CLANG_RESOURCE_DIR=$(clang --print-resource-dir)
echo "🔍 Clang resource headers: ${CLANG_RESOURCE_DIR}/include"

# -----------------------------------------------------------------------------
# 3) Python 개발 헤더 위치
# -----------------------------------------------------------------------------
PY_INC=$(python3.13 - <<<'import sysconfig; print(sysconfig.get_paths()["include"])')
echo "🔍 Python headers: ${PY_INC}"

# -----------------------------------------------------------------------------
# 4) __building_module 매크로 중립화용 임시 헤더 생성
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISABLE_HDR="$SCRIPT_DIR/disable_building_module.h"
cat > "$DISABLE_HDR" << 'EOF'
/* 자동 생성: Clang 내장 __building_module(x) 호출을 무력화 */
#define __building_module(x) 0
EOF

# -----------------------------------------------------------------------------
# 5) 공통 C/C++ 플래그
# -----------------------------------------------------------------------------
COMMON_FLAGS=(
  "-isystem" "${CLANG_RESOURCE_DIR}/include"
  "-include"  "${DISABLE_HDR}"
  "-isystem"  "${PY_INC}"
  "-isystem"  "/usr/include"
)
CFLAGS="${COMMON_FLAGS[*]}"
CXXFLAGS="${COMMON_FLAGS[*]}"

# -----------------------------------------------------------------------------
# 6) QtOpenGL alias
# -----------------------------------------------------------------------------
QT_PREFIX="/core/Linux/APPZ/packages/qt/6.9.1"
QT_CMAKE_DIR="${QT_PREFIX}/lib/cmake"
ln -sf "${QT_CMAKE_DIR}/Qt6OpenGL"        "${QT_CMAKE_DIR}/QtOpenGL"
ln -sf "${QT_CMAKE_DIR}/Qt6OpenGLWidgets" "${QT_CMAKE_DIR}/QtOpenGLWidgets"

# -----------------------------------------------------------------------------
# 7) 소스/빌드 디렉터리
# -----------------------------------------------------------------------------
SRC_DIR="$SCRIPT_DIR/source/pyside-setup-6.9.1"
BUILD_DIR="$SCRIPT_DIR/build"
if [ ! -f "$SRC_DIR/CMakeLists.txt" ]; then
  echo "❌ CMakeLists.txt not found in $SRC_DIR"
  exit 1
fi

# -----------------------------------------------------------------------------
# 8) 빌드 디렉터리 생성 및 진입
# -----------------------------------------------------------------------------
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# -----------------------------------------------------------------------------
# 9) CMake 구성
# -----------------------------------------------------------------------------
cmake "$SRC_DIR"                              \
  -G Ninja                                     \
  -DCMAKE_BUILD_TYPE=Release                   \
  -DCMAKE_PREFIX_PATH="$QT_PREFIX"             \
  -DCMAKE_C_COMPILER=clang                     \
  -DCMAKE_CXX_COMPILER=clang++                 \
  -DCMAKE_AR=/usr/bin/ar                       \
  -DCMAKE_NM=/usr/bin/nm                       \
  -DCMAKE_C_FLAGS="$CFLAGS"                    \
  -DCMAKE_CXX_FLAGS="$CXXFLAGS"                \
  -DPython3_EXECUTABLE=$(command -v python3.13)

# -----------------------------------------------------------------------------
# 10) 실제 빌드
# -----------------------------------------------------------------------------
ninja

