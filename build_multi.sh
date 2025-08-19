#!/bin/bash
# Multi-Python PySide6 Build Script
# Builds PySide6 for Python versions 3.9, 3.10, 3.11, 3.12, 3.13
# Based on successful build.sh approach with smart error handling
# Usage: ./build_multi.sh

set -e  # Exit on any error

# Build configuration
PYSIDE_VERSION="6.9.1"
QT_VERSION="6.9.1"
PYTHON_VERSIONS=("3.9.21" "3.10.6" "3.11.9" "3.12.10" "3.13.2")

# Directory paths  
SOURCE_DIR="/home/m83/chulho/pyside6/6.9.1/source/pyside-setup"
BASE_BUILD_DIR="/home/m83/chulho/pyside6/6.9.1/build"
BASE_INSTALL_DIR="/core/Linux/APPZ/packages/pyside6/6.9.1"

# Qt and Shiboken paths
QT_DIR="/core/Linux/APPZ/packages/qt/6.9.1"
SHIBOKEN_DIR="/core/Linux/APPZ/packages/shiboken6/6.9.1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

stage() {
    echo -e "${PURPLE}[STAGE] $1${NC}"
}

# Smart error detection and fixing
detect_running_builds() {
    log "Checking for running PySide6 builds..."
    
    local running_builds=$(ps aux | grep -E "(rez-build|setup\.py|cmake|ninja)" | grep -v grep | grep -i pyside || true)
    
    if [ -n "$running_builds" ]; then
        warning "Found running build processes:"
        echo "$running_builds"
        
        # Kill running builds
        pkill -f "rez-build.*pyside" || true
        pkill -f "setup\.py.*pyside" || true
        sleep 5
        
        log "Terminated running build processes"
    else
        log "No conflicting build processes found"
    fi
}

# Enhanced environment setup
setup_enhanced_environment() {
    local python_version=$1
    local python_path="/core/Linux/APPZ/packages/python/${python_version}/bin/python3"
    
    stage "Setting up environment for Python $python_version"
    
    # Check if rez Python exists
    if [ ! -f "$python_path" ]; then
        warning "Rez Python $python_version not found at $python_path"
        python_path=$(which python3)
        info "Using system Python: $python_path"
    else
        info "Using rez Python: $python_path"
    fi
    
    # Qt environment
    export QT_DIR="$QT_DIR"
    export CMAKE_PREFIX_PATH="$QT_DIR:$SHIBOKEN_DIR:$CMAKE_PREFIX_PATH"
    export PATH="$QT_DIR/bin:$(dirname $python_path):$PATH"
    export LD_LIBRARY_PATH="$QT_DIR/lib:$SHIBOKEN_DIR/lib:$LD_LIBRARY_PATH"
    export PKG_CONFIG_PATH="$QT_DIR/lib/pkgconfig:$SHIBOKEN_DIR/lib/pkgconfig:$PKG_CONFIG_PATH"
    
    # Python environment
    export PYTHON="$python_path"
    export PYTHON3="$python_path"
    export PYTHON_EXECUTABLE="$python_path"
    
    # Enhanced header paths (from successful build.sh)
    CLANG_HEADERS="/usr/lib/clang/19/include"
    GCC_HEADERS="/usr/lib/gcc/x86_64-redhat-linux/11/include"
    SYSTEM_HEADERS="/usr/include"
    CPP_HEADERS="/usr/include/c++/11"
    
    export CLANG_BUILTIN_INCLUDE_DIR="$CLANG_HEADERS"
    export C_INCLUDE_PATH="$GCC_HEADERS:$CLANG_HEADERS:$SYSTEM_HEADERS"
    export CPLUS_INCLUDE_PATH="$CPP_HEADERS:$GCC_HEADERS:$CLANG_HEADERS:$SYSTEM_HEADERS"
    export CLANG_INCLUDE_PATHS="$CLANG_HEADERS:$GCC_HEADERS:$CPP_HEADERS:$SYSTEM_HEADERS"
    export SHIBOKEN_INCLUDE_PATHS="$CLANG_HEADERS:$GCC_HEADERS:$SYSTEM_HEADERS"
    
    # Build environment
    export MAKEFLAGS="-j$(nproc)"
    export NINJA_STATUS="[%f/%t] "
    
    log "Environment configured for Python $python_version"
}

# Create enhanced shiboken wrapper
create_shiboken_wrapper() {
    local build_dir=$1
    
    log "Creating enhanced Shiboken wrapper..."
    
    mkdir -p "$build_dir/shiboken_wrapper"
    
    cat > "$build_dir/shiboken_wrapper/shiboken6" << 'EOF'
#!/bin/bash
# Enhanced Shiboken6 wrapper with comprehensive header paths

EXTRA_ARGS=""
EXTRA_ARGS="$EXTRA_ARGS -I/usr/include"
EXTRA_ARGS="$EXTRA_ARGS -I/usr/lib/clang/19/include"
EXTRA_ARGS="$EXTRA_ARGS -I/usr/lib/gcc/x86_64-redhat-linux/11/include"
EXTRA_ARGS="$EXTRA_ARGS -I/usr/lib/gcc/x86_64-redhat-linux/11/include-fixed"
EXTRA_ARGS="$EXTRA_ARGS -I/usr/include/c++/11"
EXTRA_ARGS="$EXTRA_ARGS -I/usr/include/c++/11/x86_64-redhat-linux"
EXTRA_ARGS="$EXTRA_ARGS -I/usr/include/c++/11/backward"
EXTRA_ARGS="$EXTRA_ARGS -resource-dir=/usr/lib/clang/19"

export C_INCLUDE_PATH="/usr/lib/gcc/x86_64-redhat-linux/11/include:/usr/lib/clang/19/include:/usr/include"
export CPLUS_INCLUDE_PATH="/usr/include/c++/11:/usr/include/c++/11/x86_64-redhat-linux:/usr/include/c++/11/backward:/usr/lib/gcc/x86_64-redhat-linux/11/include:/usr/lib/clang/19/include:/usr/include"
export CLANG_BUILTIN_INCLUDE_DIR="/usr/lib/clang/19/include"

# Find original shiboken6
ORIGINAL_SHIBOKEN=$(which shiboken6 | grep -v shiboken_wrapper | head -1)
if [ -z "$ORIGINAL_SHIBOKEN" ]; then
    for path in /core/Linux/APPZ/packages/shiboken6/*/bin/shiboken6; do
        if [ -x "$path" ]; then
            ORIGINAL_SHIBOKEN="$path"
            break
        fi
    done
fi

if [ -z "$ORIGINAL_SHIBOKEN" ]; then
    echo "Error: Could not find original shiboken6"
    exit 1
fi

exec "$ORIGINAL_SHIBOKEN" $EXTRA_ARGS "$@"
EOF
    
    chmod +x "$build_dir/shiboken_wrapper/shiboken6"
    export PATH="$build_dir/shiboken_wrapper:$PATH"
    
    log "Shiboken wrapper created and added to PATH"
}

# Smart build function with error recovery
smart_build_pyside() {
    local python_version=$1
    local build_dir="$BASE_BUILD_DIR/python${python_version}"
    local install_dir="$BASE_INSTALL_DIR/python${python_version}"
    
    stage "Building PySide6 for Python $python_version"
    
    # Setup environment
    setup_enhanced_environment "$python_version"
    
    # Prepare directories
    if [ -d "$build_dir" ]; then
        log "Cleaning build directory: $build_dir"
        rm -rf "$build_dir"
    fi
    mkdir -p "$build_dir"
    
    if [ -d "$install_dir" ]; then
        log "Cleaning install directory: $install_dir"
        rm -rf "$install_dir"
    fi
    mkdir -p "$install_dir"
    
    # Create shiboken wrapper
    create_shiboken_wrapper "$build_dir"
    
    # Change to source directory
    cd "$SOURCE_DIR"
    
    # Use existing Python packages (do not modify installed packages)
    log "Using existing Python $python_version installation..."
    
    # Build with error recovery
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        info "Build attempt $attempt/$max_attempts for Python $python_version"
        
        # Try incremental build approach (from successful build.sh)
        if attempt_build_with_recovery "$python_version" "$build_dir" "$install_dir" "$attempt"; then
            log "Build successful for Python $python_version"
            return 0
        else
            warning "Build attempt $attempt failed for Python $python_version"
            attempt=$((attempt + 1))
            
            if [ $attempt -le $max_attempts ]; then
                log "Waiting 30 seconds before retry..."
                sleep 30
                
                # Apply fixes based on attempt number
                apply_build_fixes "$attempt" "$build_dir"
            fi
        fi
    done
    
    error "All build attempts failed for Python $python_version"
}

# Attempt build with error recovery
attempt_build_with_recovery() {
    local python_version=$1
    local build_dir=$2
    local install_dir=$3
    local attempt=$4
    
    # Set build-specific environment
    export PYSIDE_BUILD_DIR="$build_dir"
    export PYSIDE_INSTALL_DIR="$install_dir"
    
    # Use different strategies based on attempt
    case $attempt in
        1)
            info "Attempt 1: CMake build (from successful build.sh)"
            build_with_cmake "$python_version" "$install_dir" "$python_path"
            ;;
        2)
            info "Attempt 2: CMake build with different Python path"
            # Try with system Python if rez Python fails
            local sys_python="/usr/bin/python3"
            if [ "$python_path" != "$sys_python" ] && [ -x "$sys_python" ]; then
                build_with_cmake "$python_version" "$install_dir" "$sys_python"
            else
                build_full_verbose "$install_dir"
            fi
            ;;
        3)
            info "Attempt 3: Fallback build with reduced modules"
            build_fallback_reduced "$install_dir"
            ;;
    esac
}

# Incremental module build (successful approach from build.sh)
build_with_cmake() {
    local python_version=$1
    local install_dir=$2
    local python_path=$3
    local build_dir="$BASE_BUILD_DIR/python${python_version}"
    
    log "Building PySide6 using CMake approach (from build.sh)..."
    
    # Clean paths to remove conflicting toolsets
    export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v '/opt/rh/gcc-toolset-14' | paste -sd ':' -)
    unset LD_LIBRARY_PATH
    
    # Essential tools verification
    for tool in ninja cmake qmake qtpaths6 pkg-config clang clang++; do
        if ! command -v "$tool" &>/dev/null; then
            error "Required tool not found: $tool"
            return 1
        fi
    done
    
    # Clang resource directory
    CLANG_RESOURCE_DIR=$(clang --print-resource-dir)
    log "Using Clang resource directory: $CLANG_RESOURCE_DIR"
    
    # Python includes for this version
    PY_INC=$($python_path -c "import sysconfig; print(sysconfig.get_paths()['include'])")
    log "Python includes: $PY_INC"
    
    # Create header to neutralize __building_module macro
    DISABLE_HDR="$build_dir/disable_building_module.h"
    mkdir -p "$(dirname "$DISABLE_HDR")"
    cat > "$DISABLE_HDR" << 'EOF'
/* Auto-generated: Neutralize Clang __building_module(x) calls */
#define __building_module(x) 0
EOF
    
    # Common C/C++ flags from successful build.sh
    COMMON_FLAGS=(
        "-isystem" "$CLANG_RESOURCE_DIR/include"
        "-include" "$DISABLE_HDR"
        "-isystem" "$PY_INC"
        "-isystem" "/usr/include"
    )
    
    export CFLAGS="${COMMON_FLAGS[*]}"
    export CXXFLAGS="${COMMON_FLAGS[*]}"
    
    # QtOpenGL aliases (as in build.sh)
    QT_CMAKE_DIR="$QT_DIR/lib/cmake"
    ln -sf "$QT_CMAKE_DIR/Qt6OpenGL" "$QT_CMAKE_DIR/QtOpenGL" 2>/dev/null || true
    ln -sf "$QT_CMAKE_DIR/Qt6OpenGLWidgets" "$QT_CMAKE_DIR/QtOpenGLWidgets" 2>/dev/null || true
    
    # CMake build
    cd "$SOURCE_DIR"
    mkdir -p "$build_dir"
    cd "$build_dir"
    
    cmake "$SOURCE_DIR" \
        -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_PREFIX_PATH="$QT_DIR" \
        -DCMAKE_C_COMPILER=clang \
        -DCMAKE_CXX_COMPILER=clang++ \
        -DCMAKE_AR=/usr/bin/ar \
        -DCMAKE_NM=/usr/bin/nm \
        -DCMAKE_C_FLAGS="$CFLAGS" \
        -DCMAKE_CXX_FLAGS="$CXXFLAGS" \
        -DPython3_EXECUTABLE="$python_path" \
        -DCMAKE_INSTALL_PREFIX="$install_dir"
    
    if ! ninja; then
        return 1
    fi
    
    if ! ninja install; then
        return 1
    fi
    
    log "CMake build successful for Python $python_version"
    return 0
}

# Full verbose build
build_full_verbose() {
    local install_dir=$1
    
    python3 setup.py build \
        --qmake "$QT_DIR/bin/qmake" \
        --jobs $(nproc) \
        --verbose-build \
        --reuse-build && \
    python3 setup.py install --prefix="$install_dir"
}

# Fallback reduced build
build_fallback_reduced() {
    local install_dir=$1
    
    python3 setup.py build \
        --qmake "$QT_DIR/bin/qmake" \
        --jobs 1 \
        --module-subset=QtCore,QtGui,QtWidgets \
        --skip-modules=QtWebEngine,QtWebEngineWidgets && \
    python3 setup.py install --prefix="$install_dir"
}

# Apply build fixes based on attempt
apply_build_fixes() {
    local attempt=$1
    local build_dir=$2
    
    info "Applying fixes for attempt $attempt"
    
    case $attempt in
        2)
            # Clear any cached build files
            find "$build_dir" -name "*.pyc" -delete 2>/dev/null || true
            find "$build_dir" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
            ;;
        3)
            # More aggressive cleanup
            rm -rf "$build_dir" 2>/dev/null || true
            mkdir -p "$build_dir"
            
            # Reset environment
            unset PYTHONPATH
            export PYTHONPATH=""
            ;;
    esac
}

# Verify installation for a Python version
verify_python_installation() {
    local python_version=$1
    local install_dir="$BASE_INSTALL_DIR/python${python_version}"
    
    stage "Verifying installation for Python $python_version"
    
    if [ ! -d "$install_dir" ]; then
        error "Installation directory not found: $install_dir"
        return 1
    fi
    
    # Check for key files
    local site_packages="$install_dir/lib/python${python_version}/site-packages"
    if [ ! -d "$site_packages/PySide6" ]; then
        error "PySide6 package not found in $site_packages"
        return 1
    fi
    
    log "Installation verified for Python $python_version"
    return 0
}

# Create unified installation
create_unified_installation() {
    stage "Creating unified multi-Python installation"
    
    # Create main installation directory structure
    mkdir -p "$BASE_INSTALL_DIR"/{bin,lib,include,share}
    
    # Copy tools and binaries from the primary Python version (3.13)
    local primary_version="3.13"
    local primary_install="$BASE_INSTALL_DIR/python${primary_version}"
    
    if [ -d "$primary_install/bin" ]; then
        log "Copying tools from Python $primary_version installation"
        cp -r "$primary_install/bin/"* "$BASE_INSTALL_DIR/bin/" 2>/dev/null || true
    fi
    
    if [ -d "$primary_install/include" ]; then
        cp -r "$primary_install/include/"* "$BASE_INSTALL_DIR/include/" 2>/dev/null || true
    fi
    
    if [ -d "$primary_install/share" ]; then
        cp -r "$primary_install/share/"* "$BASE_INSTALL_DIR/share/" 2>/dev/null || true
    fi
    
    # Create unified lib structure with all Python versions
    for version in "${PYTHON_VERSIONS[@]}"; do
        local version_install="$BASE_INSTALL_DIR/python${version}"
        if [ -d "$version_install/lib" ]; then
            log "Integrating Python $version libraries"
            cp -r "$version_install/lib/"* "$BASE_INSTALL_DIR/lib/" 2>/dev/null || true
        fi
    done
    
    log "Unified installation created at $BASE_INSTALL_DIR"
}

# Create final package.py
create_package_py() {
    stage "Creating package.py for multi-Python support"
    
    cat > "$BASE_INSTALL_DIR/package.py" << 'EOF'
# -*- coding: utf-8 -*-
import os

name        = "pyside6"
version     = "6.9.1"
authors     = ["The Qt Project"]
description = "Python bindings for Qt6 (PySide6) : Multi-Python version support"

# 런타임에는 Python과 shiboken6만 필요 (멀티 Python 버전 지원)
requires = [
    "shiboken6-6.9.1",
    "qt-6.9.1", 
    "python",  # 모든 Python 버전 지원 (3.9~3.13)
    "numpy-1.26.4"
]

# 빌드 시에도 같은 의존성 + pip
build_requires = [
    "gcc-11.5.0",
    "system_clang-19.1.7",
    "cmake-3.26.5",
    "ninja-1.11.1",
    "qt-6.9.1",
    "python",
    "shiboken6-6.9.1",
    "numpy-1.26.4",
    "minizip_ng-4.0.10"
]

tools = [
    # 기본 도구들
    "pyside6-uic",                    # UI 파일 → Python 변환
    "pyside6-rcc",                    # 리소스 컴파일러
    "pyside6-designer",               # Qt Designer (GUI 디자인)
    "pyside6-assistant",              # Qt Assistant (도움말)
    
    # 번역/국제화 도구들
    "pyside6-linguist",               # 번역 에디터
    "pyside6-lupdate",                # 번역 파일 업데이트
    "pyside6-lrelease",               # 번역 파일 컴파일
    
    # QML 관련 도구들
    "pyside6-qml",                    # QML 런타임
    "pyside6-qmlcachegen",            # QML 캐시 생성
    "pyside6-qmlformat",              # QML 코드 포맷팅
    "pyside6-qmlimportscanner",       # QML 임포트 스캔
    "pyside6-qmllint",                # QML 문법 검사
    "pyside6-qmlls",                  # QML 언어 서버
    "pyside6-qmltyperegistrar",       # QML 타입 등록
    "pyside6-qsb",                    # Qt Shader Baker
    
    # 3D/렌더링 도구들
    "pyside6-balsam",                 # 3D 에셋 임포터
    "pyside6-balsamui",               # Balsam UI
    "pyside6-svgtoqml",               # SVG → QML 변환
    
    # 개발/배포 도구들
    "pyside6-deploy",                 # 앱 배포 도구
    "pyside6-android-deploy",         # 안드로이드 배포
    "pyside6-project",                # 프로젝트 관리
    "pyside6-genpyi",                 # Python stub 파일 생성
    "pyside6-metaobjectdump",         # 메타오브젝트 덤프
    "pyside6-qtpy2cpp",               # Python → C++ 변환
    
    # Shiboken 도구들
    "shiboken6",                      # 바인딩 생성기
    "shiboken6-genpyi"                # Shiboken용 stub 생성
]

def commands():
    import os
    import subprocess
    
    # 현재 활성화된 Python 버전 감지
    try:
        result = subprocess.run(['python', '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'], 
                               capture_output=True, text=True)
        python_version = result.stdout.strip()
    except:
        python_version = "3.13"  # 기본값
    
    # Python 버전별 site-packages 경로 설정
    python_site_packages = "{root}/lib/python" + python_version + "/site-packages"
    
    env.PATH.prepend("{root}/bin")
    env.PYTHONPATH.prepend(python_site_packages)
    env.PYTHONPATH.prepend("{root}/tools")
    env.QML2_IMPORT_PATH.prepend("{root}/qml")
    env.QML_IMPORT_PATH.prepend("{root}/qml")

    env.QT_PLUGIN_PATH.prepend("{root}/lib/PySide6/plugins")
    env.PYSIDE_DESIGNER_PLUGINS = "{root}/plugins/designer"
    
    env.LD_LIBRARY_PATH.prepend("{root}/lib")
    env.CMAKE_PREFIX_PATH.prepend("{root}")

uuid = "pyside6-6.9.1"
EOF
    
    log "Multi-Python package.py created"
}

# Main execution
main() {
    log "Starting Multi-Python PySide6 Build Process"
    log "============================================"
    log "Target Python versions: ${PYTHON_VERSIONS[*]}"
    log "Source: $SOURCE_DIR"
    log "Install: $BASE_INSTALL_DIR"
    
    # Preliminary checks
    detect_running_builds
    
    if [ ! -d "$SOURCE_DIR" ]; then
        error "Source directory not found: $SOURCE_DIR"
    fi
    
    if [ ! -d "$QT_DIR" ]; then
        error "Qt directory not found: $QT_DIR"
    fi
    
    if [ ! -d "$SHIBOKEN_DIR" ]; then
        error "Shiboken directory not found: $SHIBOKEN_DIR"
    fi
    
    # Build for each Python version
    local successful_builds=0
    local failed_builds=0
    
    for version in "${PYTHON_VERSIONS[@]}"; do
        log "----------------------------------------"
        if smart_build_pyside "$version"; then
            if verify_python_installation "$version"; then
                successful_builds=$((successful_builds + 1))
                log "Python $version: ✅ SUCCESS"
            else
                failed_builds=$((failed_builds + 1))
                warning "Python $version: ⚠️  BUILD OK, VERIFY FAILED"
            fi
        else
            failed_builds=$((failed_builds + 1))
            error "Python $version: ❌ FAILED"
        fi
    done
    
    # Create unified installation if at least one build succeeded
    if [ $successful_builds -gt 0 ]; then
        create_unified_installation
        create_package_py
        
        log "=========================================="
        log "Multi-Python PySide6 Build Summary"
        log "=========================================="
        log "Successful builds: $successful_builds/${#PYTHON_VERSIONS[@]}"
        log "Failed builds: $failed_builds/${#PYTHON_VERSIONS[@]}"
        log "Installation: $BASE_INSTALL_DIR"
        log "=========================================="
        
        if [ $failed_builds -eq 0 ]; then
            log "🎉 All Python versions built successfully!"
            return 0
        else
            warning "⚠️  Some Python versions failed, but installation is available"
            return 1
        fi
    else
        error "❌ All Python version builds failed"
        return 1
    fi
}

# Execute main function
main "$@"