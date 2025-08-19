#!/bin/bash
# Multi-Python PySide6 6.9.1 Build Script for Rocky Linux 9
# Based on proven build.sh patterns - Fallback option for rezbuild.py
# Author: Claude Code Assistant
# Date: $(date)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Build configuration
PYSIDE_VERSION="6.9.1"
QT_VERSION="6.9.1"

# Python versions from readme.md (build.sh 검증된 순서로 정렬 - 3.13.2 먼저)
PYTHON_VERSIONS=("3.13.2" "3.12.10" "3.11.9" "3.10.6" "3.9.21")

# Directory paths
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$BASE_DIR/source/pyside-setup"
BUILD_BASE_DIR="$BASE_DIR/build"
INSTALL_DIR="/core/Linux/APPZ/packages/pyside6/6.9.1"

# Qt and Shiboken paths
QT_DIR="/core/Linux/APPZ/packages/qt/6.9.1"
SHIBOKEN_DIR="/core/Linux/APPZ/packages/shiboken6/6.9.1"

# Build statistics
BUILD_START_TIME=$(date +%s)
TOTAL_VERSIONS=${#PYTHON_VERSIONS[@]}
CURRENT_VERSION=0
SUCCESSFUL_BUILDS=()
FAILED_BUILDS=()

# Logging functions with progress tracking
log() {
    local elapsed=$(($(date +%s) - BUILD_START_TIME))
    local elapsed_str=$(format_duration $elapsed)
    if [ $TOTAL_VERSIONS -gt 0 ] && [ $CURRENT_VERSION -gt 0 ]; then
        local progress=$((CURRENT_VERSION * 100 / TOTAL_VERSIONS))
        echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} ${CYAN}[${elapsed_str}]${NC} ${GREEN}[${CURRENT_VERSION}/${TOTAL_VERSIONS} - ${progress}%]${NC} $1"
    else
        echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} ${CYAN}[${elapsed_str}]${NC} $1"
    fi
}

error() {
    log "${RED}[ERROR] $1${NC}"
}

warning() {
    log "${YELLOW}[WARNING] $1${NC}"
}

stage() {
    log "${PURPLE}🔧 $1${NC}"
}

success() {
    log "${GREEN}✅ $1${NC}"
}

# Time formatting function
format_duration() {
    local duration=$1
    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))
    local seconds=$((duration % 60))
    
    if [ $hours -gt 0 ]; then
        printf "%dh %dm %ds" $hours $minutes $seconds
    elif [ $minutes -gt 0 ]; then
        printf "%dm %ds" $minutes $seconds
    else
        printf "%ds" $seconds
    fi
}

# Enhanced error detection and cleanup
detect_and_terminate_builds() {
    stage "Checking for running build processes..."
    
    local terminated_count=0
    local pids=$(ps aux | grep -E "(rez-build|setup\.py|cmake|ninja)" | grep -v grep | grep -i pyside | awk '{print $2}' || true)
    
    if [ -n "$pids" ]; then
        warning "Found running build processes, terminating..."
        for pid in $pids; do
            if kill -TERM "$pid" 2>/dev/null; then
                sleep 5
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid" 2>/dev/null || true
                fi
                terminated_count=$((terminated_count + 1))
            fi
        done
        success "Terminated $terminated_count running build process(es)"
        sleep 3
    else
        success "No conflicting build processes found"
    fi
}

# Find specific rez Python version
find_rez_python_version() {
    local python_version="$1"
    local python_exe_paths=(
        "/core/Linux/APPZ/packages/python/${python_version}/bin/python3"
        "/core/Linux/APPZ/packages/python/${python_version}/bin/python"
    )
    
    for path in "${python_exe_paths[@]}"; do
        if [ -x "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    
    warning "Rez Python $python_version not found, using system Python"
    echo "$(which python3)"
}

# Create enhanced shiboken wrapper (build.sh proven method)
create_shiboken_wrapper() {
    local build_dir="$1"
    local wrapper_dir="$build_dir/shiboken_wrapper"
    
    stage "Creating Shiboken wrapper (build.sh proven method)..."
    
    mkdir -p "$wrapper_dir"
    
    cat > "$wrapper_dir/shiboken6" << 'EOF'
#!/bin/bash
# Shiboken wrapper to add proper include paths (build.sh proven method)

# Add system headers to arguments - build.sh에서 성공한 정확한 경로들
EXTRA_ARGS=""
EXTRA_ARGS="$EXTRA_ARGS -I/usr/lib/clang/19/include"
EXTRA_ARGS="$EXTRA_ARGS -I/usr/lib/gcc/x86_64-redhat-linux/11/include"
EXTRA_ARGS="$EXTRA_ARGS -I/usr/include"
EXTRA_ARGS="$EXTRA_ARGS -I/usr/include/c++/11"
EXTRA_ARGS="$EXTRA_ARGS -resource-dir=/usr/lib/clang/19"

# Set environment - build.sh에서 검증된 환경변수
export C_INCLUDE_PATH="/usr/lib/gcc/x86_64-redhat-linux/11/include:/usr/lib/clang/19/include:/usr/include"
export CPLUS_INCLUDE_PATH="/usr/include/c++/11:/usr/lib/gcc/x86_64-redhat-linux/11/include:/usr/lib/clang/19/include:/usr/include"

# Call original shiboken6 with additional arguments
exec /core/Linux/APPZ/packages/shiboken6/6.9.1/bin/shiboken6 $EXTRA_ARGS "$@"
EOF
    
    chmod +x "$wrapper_dir/shiboken6"
    success "Created shiboken wrapper: $wrapper_dir/shiboken6"
    
    # Add wrapper to PATH
    export PATH="$wrapper_dir:$PATH"
}

# Set environment variables (build.sh proven method)
setup_build_environment() {
    local python_exe="$1"
    local python_version="$2"
    
    stage "Setting up build environment for Python $python_version (build.sh method)..."
    
    # build.sh에서 검증된 PATH 설정 (GCC toolset 경로 제거)
    local old_path="$PATH"
    local clean_path_parts=()
    
    IFS=':' read -ra PATH_PARTS <<< "$old_path"
    for part in "${PATH_PARTS[@]}"; do
        if [[ "$part" != *"gcc-toolset-14"* && "$part" != *"gcc-toolset-13"* ]]; then
            clean_path_parts+=("$part")
        fi
    done
    
    # build.sh에서 검증된 헤더 경로
    local clang_headers="/usr/lib/clang/19/include"
    local gcc_headers="/usr/lib/gcc/x86_64-redhat-linux/11/include"
    local system_headers="/usr/include"
    local cpp_headers="/usr/include/c++/11"
    
    # Verify header directories exist
    for header_dir in "$clang_headers" "$gcc_headers" "$system_headers" "$cpp_headers"; do
        if [ -d "$header_dir" ]; then
            log "✓ Found header directory: $header_dir"
        else
            warning "Header directory not found: $header_dir"
        fi
    done
    
    # build.sh에서 검증된 환경 변수 설정
    export PATH="$QT_DIR/bin:$SHIBOKEN_DIR/bin:$(IFS=:; echo "${clean_path_parts[*]}")"
    
    # Qt environment (build.sh 방식)
    export QT_DIR="$QT_DIR"
    export CMAKE_PREFIX_PATH="$QT_DIR:$SHIBOKEN_DIR"
    export LD_LIBRARY_PATH="$QT_DIR/lib:$SHIBOKEN_DIR/lib"
    export PKG_CONFIG_PATH="$QT_DIR/lib/pkgconfig:$SHIBOKEN_DIR/lib/pkgconfig"
    
    # build.sh에서 검증된 헤더 환경변수
    export CLANG_BUILTIN_INCLUDE_DIR="$clang_headers"
    export C_INCLUDE_PATH="$gcc_headers:$clang_headers:$system_headers"
    export CPLUS_INCLUDE_PATH="$cpp_headers:$gcc_headers:$clang_headers:$system_headers"
    export CLANG_INCLUDE_PATHS="$clang_headers:$gcc_headers:$cpp_headers:$system_headers"
    export SHIBOKEN_INCLUDE_PATHS="$clang_headers:$gcc_headers:$system_headers"
    
    # build.sh에서 검증된 추가 환경변수
    export LLVM_INSTALL_DIR="/usr"
    export CLANG_INCLUDE_PATH="$clang_headers"
    export CLANG_RESOURCE_DIR="$clang_headers"
    
    # Python environment
    export PYTHON="$python_exe"
    export PYTHON3="$python_exe"
    export PYTHON_EXECUTABLE="$python_exe"
    export PYTHONPATH="$INSTALL_DIR/lib/python$python_version/site-packages"
    
    # build.sh에서 검증된 QMAKE 설정
    export QMAKE="$QT_DIR/bin/qmake"
    export QT_QMAKE_EXECUTABLE="$QT_DIR/bin/qmake"
    
    success "Build environment configured for Python $python_version"
}

# Build PySide6 for specific Python version (build.sh proven method)
build_pyside6_for_version() {
    local python_version="$1"
    local python_exe="$2"
    local build_dir="$3"
    local install_dir="$4"
    
    stage "Building PySide6 for Python $python_version using build.sh proven method..."
    
    # Create version-specific build directory
    mkdir -p "$build_dir"
    
    # Create Shiboken wrapper
    create_shiboken_wrapper "$build_dir"
    
    # Setup environment
    setup_build_environment "$python_exe" "${python_version%.*}"
    
    # Change to source directory for setup.py
    cd "$SOURCE_DIR"
    
    stage "Starting PySide6 build with setup.py (build.sh proven method)..."
    
    # build.sh에서 성공한 setup.py 명령어
    if "$python_exe" setup.py build \
        --qmake "$QT_DIR/bin/qmake" \
        --jobs $(nproc) \
        --verbose-build; then
        
        success "Build completed successfully for Python $python_version"
        return 0
    else
        error "Build failed for Python $python_version"
        return 1
    fi
}

# Install PySide6 for specific Python version
install_pyside6_for_version() {
    local python_version="$1"
    local python_exe="$2"
    local install_dir="$3"
    
    stage "Installing PySide6 for Python $python_version..."
    
    cd "$SOURCE_DIR"
    
    # Create install directory
    mkdir -p "$install_dir"
    
    # Install using setup.py (build.sh method)
    if "$python_exe" setup.py install --prefix="$install_dir"; then
        success "Installation completed for Python $python_version"
        return 0
    else
        error "Installation failed for Python $python_version"
        return 1
    fi
}

# Verify installation
verify_installation() {
    local python_version="$1"
    local python_exe="$2"
    local install_dir="$3"
    
    stage "Verifying installation for Python $python_version..."
    
    local python_major_minor="${python_version%.*}"
    local site_packages="$install_dir/lib/python$python_major_minor/site-packages"
    
    # Check if PySide6 package exists
    if [ ! -d "$site_packages/PySide6" ]; then
        error "PySide6 package not found in $site_packages"
        return 1
    fi
    
    # Try to import PySide6
    local pythonpath_backup="$PYTHONPATH"
    export PYTHONPATH="$site_packages:$PYTHONPATH"
    
    if "$python_exe" -c "import PySide6; print(f'PySide6 {PySide6.__version__} imported successfully')" 2>/dev/null; then
        success "PySide6 import test passed for Python $python_version"
        export PYTHONPATH="$pythonpath_backup"
        return 0
    else
        error "PySide6 import test failed for Python $python_version"
        export PYTHONPATH="$pythonpath_backup"
        return 1
    fi
}

# Create tool wrappers (_pyside6 style)
create_tool_wrappers() {
    stage "Creating PySide6 tool wrappers (_pyside6 style)..."
    
    local python3_13_site_packages="$INSTALL_DIR/lib/python3.13/site-packages"
    local bin_dir="$INSTALL_DIR/bin"
    
    # Create bin directory
    mkdir -p "$bin_dir"
    
    # Qt libexec tools (both pyside6- and basic versions)
    local qt_tools=(
        "pyside6-uic:$python3_13_site_packages/PySide6/Qt/libexec/uic"
        "uic:$python3_13_site_packages/PySide6/Qt/libexec/uic"
        "pyside6-rcc:$python3_13_site_packages/PySide6/Qt/libexec/rcc"
        "rcc:$python3_13_site_packages/PySide6/Qt/libexec/rcc"
        "pyside6-qmlcachegen:$python3_13_site_packages/PySide6/Qt/libexec/qmlcachegen"
        "qmlcachegen:$python3_13_site_packages/PySide6/Qt/libexec/qmlcachegen"
        "pyside6-qmlimportscanner:$python3_13_site_packages/PySide6/Qt/libexec/qmlimportscanner"
        "qmlimportscanner:$python3_13_site_packages/PySide6/Qt/libexec/qmlimportscanner"
        "pyside6-qmltyperegistrar:$python3_13_site_packages/PySide6/Qt/libexec/qmltyperegistrar"
        "qmltyperegistrar:$python3_13_site_packages/PySide6/Qt/libexec/qmltyperegistrar"
    )
    
    # PySide6 binary tools (both versions)
    local pyside_tools=(
        "pyside6-assistant:$python3_13_site_packages/PySide6/assistant"
        "assistant:$python3_13_site_packages/PySide6/assistant"
        "pyside6-designer:$python3_13_site_packages/PySide6/designer"
        "designer:$python3_13_site_packages/PySide6/designer"
        "pyside6-linguist:$python3_13_site_packages/PySide6/linguist"
        "linguist:$python3_13_site_packages/PySide6/linguist"
        "pyside6-lrelease:$python3_13_site_packages/PySide6/lrelease"
        "lrelease:$python3_13_site_packages/PySide6/lrelease"
        "pyside6-lupdate:$python3_13_site_packages/PySide6/lupdate"
        "lupdate:$python3_13_site_packages/PySide6/lupdate"
        "pyside6-balsam:$python3_13_site_packages/PySide6/balsam"
        "balsam:$python3_13_site_packages/PySide6/balsam"
        "pyside6-balsamui:$python3_13_site_packages/PySide6/balsamui"
        "balsamui:$python3_13_site_packages/PySide6/balsamui"
        "pyside6-qmlformat:$python3_13_site_packages/PySide6/qmlformat"
        "qmlformat:$python3_13_site_packages/PySide6/qmlformat"
        "pyside6-qmllint:$python3_13_site_packages/PySide6/qmllint"
        "qmllint:$python3_13_site_packages/PySide6/qmllint"
        "pyside6-qmlls:$python3_13_site_packages/PySide6/qmlls"
        "qmlls:$python3_13_site_packages/PySide6/qmlls"
        "pyside6-qsb:$python3_13_site_packages/PySide6/qsb"
        "qsb:$python3_13_site_packages/PySide6/qsb"
        "pyside6-svgtoqml:$python3_13_site_packages/PySide6/svgtoqml"
        "svgtoqml:$python3_13_site_packages/PySide6/svgtoqml"
    )
    
    # Python script tools
    local python_tools=(
        "pyside6-android-deploy:$python3_13_site_packages/PySide6/scripts/android_deploy.py"
        "pyside6-deploy:$python3_13_site_packages/PySide6/scripts/deploy.py"
        "pyside6-metaobjectdump:$python3_13_site_packages/PySide6/scripts/metaobjectdump.py"
        "pyside6-project:$python3_13_site_packages/PySide6/scripts/project.py"
        "pyside6-qml:$python3_13_site_packages/PySide6/scripts/qml.py"
        "pyside6-qtpy2cpp:$python3_13_site_packages/PySide6/scripts/qtpy2cpp.py"
        "pyside6-genpyi:$python3_13_site_packages/PySide6/support/generate_pyi.py"
    )
    
    # Shiboken6 tools
    local shiboken_tools=(
        "shiboken6:$python3_13_site_packages/shiboken6_generator/shiboken6"
        "shiboken6-genpyi:$python3_13_site_packages/shiboken6_generator/shiboken6"
    )
    
    # Create binary tool wrappers
    for tool_entry in "${qt_tools[@]}" "${pyside_tools[@]}"; do
        local tool_name="${tool_entry%%:*}"
        local target_path="${tool_entry##*:}"
        
        if [ -f "$target_path" ]; then
            cat > "$bin_dir/$tool_name" << EOF
#!/bin/bash
# PySide6 $tool_name wrapper  
exec "$target_path" "\$@"
EOF
            chmod +x "$bin_dir/$tool_name"
        fi
    done
    
    # Create Python script wrappers
    for tool_entry in "${python_tools[@]}"; do
        local tool_name="${tool_entry%%:*}"
        local target_path="${tool_entry##*:}"
        
        if [ -f "$target_path" ]; then
            cat > "$bin_dir/$tool_name" << EOF
#!/bin/bash
# PySide6 $tool_name wrapper
exec python3 "$target_path" "\$@"
EOF
            chmod +x "$bin_dir/$tool_name"
        fi
    done
    
    # Create Shiboken6 wrappers
    for tool_entry in "${shiboken_tools[@]}"; do
        local tool_name="${tool_entry%%:*}"
        local target_path="${tool_entry##*:}"
        
        if [ -f "$target_path" ]; then
            cat > "$bin_dir/$tool_name" << EOF
#!/bin/bash
# PySide6 $tool_name wrapper  
exec "$target_path" "\$@"
EOF
            chmod +x "$bin_dir/$tool_name"
        fi
    done
    
    # Copy support files
    if [ -d "$python3_13_site_packages/PySide6/scripts" ]; then
        for script in android_deploy.py deploy.py metaobjectdump.py project.py qml.py qtpy2cpp.py pyside_tool.py; do
            if [ -f "$python3_13_site_packages/PySide6/scripts/$script" ]; then
                cp "$python3_13_site_packages/PySide6/scripts/$script" "$bin_dir/"
                chmod +x "$bin_dir/$script"
            fi
        done
        
        # Copy requirements file
        if [ -f "$python3_13_site_packages/PySide6/scripts/requirements-android.txt" ]; then
            cp "$python3_13_site_packages/PySide6/scripts/requirements-android.txt" "$bin_dir/"
        fi
    fi
    
    # Count created tools
    local tool_count=$(find "$bin_dir" -maxdepth 1 -type f | wc -l)
    success "Created $tool_count tool wrappers in $bin_dir"
}

# Setup directory structure (_pyside6 style)
setup_directory_structure() {
    stage "Setting up complete directory structure (_pyside6 style)..."
    
    local python3_13_site_packages="$INSTALL_DIR/lib/python3.13/site-packages"
    
    # Create include structure
    mkdir -p "$INSTALL_DIR/include"
    if [ -d "$python3_13_site_packages/PySide6/include" ]; then
        cp -r "$python3_13_site_packages/PySide6/include" "$INSTALL_DIR/include/PySide6"
    fi
    if [ -d "$python3_13_site_packages/shiboken6_generator/include" ]; then
        cp -r "$python3_13_site_packages/shiboken6_generator/include" "$INSTALL_DIR/include/shiboken6"
    fi
    
    # Setup lib structure with proper symlinks
    mkdir -p "$INSTALL_DIR/lib"/{cmake,pkgconfig}
    
    # Copy libraries and create symlinks
    local lib_dir="$INSTALL_DIR/lib"
    for lib_path in "$python3_13_site_packages/PySide6"/lib*.so.* "$python3_13_site_packages/shiboken6"/lib*.so.*; do
        if [ -f "$lib_path" ]; then
            local lib_name=$(basename "$lib_path")
            cp "$lib_path" "$lib_dir/"
            
            # Create versioned symlinks
            local base_name="${lib_name%.so.*}.so"
            local version_name="${lib_name%.1}"
            
            cd "$lib_dir"
            ln -sf "$lib_name" "$version_name"
            ln -sf "$version_name" "$base_name"
            cd - > /dev/null
        fi
    done
    
    # Create pkgconfig files
    cat > "$INSTALL_DIR/lib/pkgconfig/pyside6.pc" << EOF
prefix=$INSTALL_DIR
exec_prefix=\${prefix}
libdir=\${prefix}/lib
includedir=\${prefix}/include

Name: PySide6
Description: Python bindings for Qt6
Version: 6.9.1
Requires: Qt6Core Qt6Gui Qt6Widgets
Libs: -L\${libdir} -lpyside6
Cflags: -I\${includedir}
EOF
    
    cat > "$INSTALL_DIR/lib/pkgconfig/shiboken6.pc" << EOF
prefix=$INSTALL_DIR
exec_prefix=\${prefix}
libdir=\${prefix}/lib
includedir=\${prefix}/include

Name: Shiboken6
Description: CPython bindings generator for Qt6
Version: 6.9.1
Libs: -L\${libdir} -lshiboken6
Cflags: -I\${includedir}/shiboken6
EOF
    
    # Setup plugins structure
    mkdir -p "$INSTALL_DIR/plugins/designer"
    
    # Setup share structure
    mkdir -p "$INSTALL_DIR/share/PySide6"
    for subdir in doc glue typesystems; do
        if [ -d "$python3_13_site_packages/PySide6/$subdir" ]; then
            cp -r "$python3_13_site_packages/PySide6/$subdir" "$INSTALL_DIR/share/PySide6/"
        fi
    done
    
    success "Complete directory structure created at $INSTALL_DIR"
}

# Copy package.py to installation directory
copy_package_file() {
    stage "Copying Rez package definition..."
    
    local source_package="$BASE_DIR/package.py"
    local dest_package="$INSTALL_DIR/package.py"
    
    if [ -f "$source_package" ]; then
        cp "$source_package" "$dest_package"
        success "Copied package.py to $dest_package"
    else
        error "Source package.py not found: $source_package"
        return 1
    fi
}

# Create unified installation
create_unified_installation() {
    stage "Creating unified multi-Python installation..."
    
    # Create main installation directory structure
    mkdir -p "$INSTALL_DIR"/{bin,lib,include,share,plugins}
    
    # Setup complete directory structure
    setup_directory_structure
    
    # Create tool wrappers
    create_tool_wrappers
    
    # Copy Rez package definition
    copy_package_file
    
    success "Unified installation completed at $INSTALL_DIR"
}

# Build summary and statistics
show_build_summary() {
    local build_duration=$(($(date +%s) - BUILD_START_TIME))
    local duration_str=$(format_duration $build_duration)
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${WHITE}📊 Multi-Python PySide6 Build Summary${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "Duration: ${CYAN}$duration_str${NC}"
    echo -e "Total Python versions: ${BLUE}${#PYTHON_VERSIONS[@]}${NC}"
    echo -e "Successful builds: ${GREEN}${#SUCCESSFUL_BUILDS[@]}${NC}"
    echo -e "Failed builds: ${RED}${#FAILED_BUILDS[@]}${NC}"
    
    if [ ${#SUCCESSFUL_BUILDS[@]} -gt 0 ]; then
        echo -e "Build efficiency: ${CYAN}$((${#SUCCESSFUL_BUILDS[@]}*100/${#PYTHON_VERSIONS[@]}))%${NC}"
        echo -e "Average time per version: ${CYAN}$(format_duration $((build_duration/${#PYTHON_VERSIONS[@]})))${NC}"
    fi
    
    echo -e "Installation: ${BLUE}$INSTALL_DIR${NC}"
    
    if [ ${#SUCCESSFUL_BUILDS[@]} -eq ${#PYTHON_VERSIONS[@]} ]; then
        echo -e "Status: ${GREEN}✅ ALL BUILDS SUCCESS${NC}"
    elif [ ${#SUCCESSFUL_BUILDS[@]} -gt 0 ]; then
        echo -e "Status: ${YELLOW}⚠️  PARTIAL SUCCESS${NC}"
    else
        echo -e "Status: ${RED}❌ ALL BUILDS FAILED${NC}"
    fi
    echo "═══════════════════════════════════════════════════════════════"
    
    if [ ${#SUCCESSFUL_BUILDS[@]} -gt 0 ]; then
        echo -e "${GREEN}✅ Successful builds:${NC}"
        for version in "${SUCCESSFUL_BUILDS[@]}"; do
            echo "   - Python $version"
        done
    fi
    
    if [ ${#FAILED_BUILDS[@]} -gt 0 ]; then
        echo -e "${RED}❌ Failed builds:${NC}"
        for version in "${FAILED_BUILDS[@]}"; do
            echo "   - Python $version"
        done
    fi
}

# Main execution function
main() {
    log "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    log "${GREEN}🚀 Multi-Python PySide6 Build Script Starting (build.sh method)${NC}"
    log "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    log "📦 PySide6 version: $PYSIDE_VERSION"
    log "🐍 Target Python versions: ${PYTHON_VERSIONS[*]}"
    log "📁 Source directory: $SOURCE_DIR"
    log "📁 Install directory: $INSTALL_DIR"
    log "🎯 Total versions to build: ${#PYTHON_VERSIONS[@]}"
    
    # Preliminary checks
    detect_and_terminate_builds
    
    # Verify source directory
    if [ ! -d "$SOURCE_DIR" ]; then
        error "Source directory not found: $SOURCE_DIR"
        exit 1
    fi
    
    if [ ! -f "$SOURCE_DIR/setup.py" ] && [ ! -f "$SOURCE_DIR/CMakeLists.txt" ]; then
        error "PySide setup files not found in $SOURCE_DIR"
        exit 1
    fi
    
    # Verify dependencies
    if [ ! -d "$QT_DIR" ]; then
        error "Qt directory not found: $QT_DIR"
        exit 1
    fi
    
    if [ ! -d "$SHIBOKEN_DIR" ]; then
        error "Shiboken directory not found: $SHIBOKEN_DIR"
        exit 1
    fi
    
    success "All prerequisite checks passed"
    
    # Build for each Python version
    for python_version in "${PYTHON_VERSIONS[@]}"; do
        CURRENT_VERSION=$((CURRENT_VERSION + 1))
        log ""
        log "────────────────────────────────────────────────────────────────"
        stage "Building PySide6 for Python $python_version [$CURRENT_VERSION/${#PYTHON_VERSIONS[@]}]"
        log "────────────────────────────────────────────────────────────────"
        
        # Find Python executable
        python_exe=$(find_rez_python_version "$python_version")
        if [ -z "$python_exe" ]; then
            error "Python executable not found for version $python_version"
            FAILED_BUILDS+=("$python_version")
            continue
        fi
        
        log "🐍 Using Python executable: $python_exe"
        
        # Version-specific paths
        local version_build_dir="$BUILD_BASE_DIR/python$python_version"
        local python_major_minor="${python_version%.*}"
        
        # Clean build directory
        if [ -d "$version_build_dir" ]; then
            log "🧹 Cleaning build directory: $version_build_dir"
            rm -rf "$version_build_dir"
        fi
        
        # Build PySide6
        if build_pyside6_for_version "$python_version" "$python_exe" "$version_build_dir" "$INSTALL_DIR"; then
            # Install PySide6
            if install_pyside6_for_version "$python_version" "$python_exe" "$INSTALL_DIR"; then
                # Verify installation
                if verify_installation "$python_version" "$python_exe" "$INSTALL_DIR"; then
                    SUCCESSFUL_BUILDS+=("$python_version")
                    success "✅ Complete success for Python $python_version"
                else
                    FAILED_BUILDS+=("$python_version")
                    error "❌ Verification failed for Python $python_version"
                fi
            else
                FAILED_BUILDS+=("$python_version")
                error "❌ Installation failed for Python $python_version"
            fi
        else
            FAILED_BUILDS+=("$python_version")
            error "❌ Build failed for Python $python_version"
        fi
    done
    
    # Create unified installation if at least one build succeeded
    if [ ${#SUCCESSFUL_BUILDS[@]} -gt 0 ]; then
        create_unified_installation
    fi
    
    # Show final summary
    show_build_summary
    
    # Return appropriate exit code
    if [ ${#SUCCESSFUL_BUILDS[@]} -eq ${#PYTHON_VERSIONS[@]} ]; then
        log "🎉 All Python versions built successfully!"
        exit 0
    elif [ ${#SUCCESSFUL_BUILDS[@]} -gt 0 ]; then
        log "⚠️  Some Python versions built successfully"
        exit 1
    else
        log "💥 All Python version builds failed!"
        exit 1
    fi
}

# Run main function
main "$@"