# -*- coding: utf-8 -*-
import os, sys, shutil, subprocess, json, time, psutil
from pathlib import Path
from datetime import datetime
from threading import Thread, Event

# Smart Build Management Variables
_build_log_file = None
_error_count = 0
_retry_count = 0
_max_retries = 3
_auto_build_system = "/home/m83/chulho/auto-build-system/1.0.0"

def smart_log(message, level="INFO"):
    """Enhanced logging with auto-build system integration"""
    global _build_log_file
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    if _build_log_file:
        with open(_build_log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")
            f.flush()

def detect_and_terminate_builds():
    """Detect and safely terminate any running PySide6 builds"""
    smart_log("🔍 Checking for running build processes...")
    
    terminated_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if ('rez-build' in cmdline or 'setup.py' in cmdline) and 'pyside' in cmdline.lower():
                smart_log(f"🛑 Terminating running build: PID {proc.info['pid']}")
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except psutil.TimeoutExpired:
                    proc.kill()
                terminated_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if terminated_count > 0:
        smart_log(f"✅ Terminated {terminated_count} running build process(es)")
        time.sleep(3)  # Allow cleanup
    else:
        smart_log("✅ No conflicting build processes found")

def analyze_and_fix_errors():
    """Analyze build log and apply automatic fixes"""
    global _build_log_file, _error_count
    
    if not _build_log_file or not os.path.exists(_build_log_file):
        return False
    
    smart_log("🔍 Analyzing build errors...")
    
    fixes_applied = 0
    
    # Read recent log content
    try:
        with open(_build_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
        
        # Check for common PySide6 build issues
        if "stdbool.h" in log_content.lower() and "not found" in log_content.lower():
            fixes_applied += fix_stdbool_headers()
        
        if "shiboken" in log_content.lower() and ("include" in log_content.lower() or "header" in log_content.lower()):
            fixes_applied += fix_shiboken_wrapper()
        
        if "python" in log_content.lower() and "not found" in log_content.lower():
            fixes_applied += fix_python_environment()
        
        if "cmake" in log_content.lower() and ("qt" in log_content.lower() or "config" in log_content.lower()):
            fixes_applied += fix_cmake_configuration()
            
    except Exception as e:
        smart_log(f"⚠️  Error analyzing log: {e}")
    
    if fixes_applied > 0:
        smart_log(f"🔧 Applied {fixes_applied} automatic fixes")
        return True
    else:
        smart_log("ℹ️  No automatic fixes available for current errors")
        return False

def fix_stdbool_headers():
    """Fix stdbool.h header path issues"""
    smart_log("🔧 Applying stdbool.h header fix...")
    
    try:
        # Update environment variables
        header_paths = [
            "/usr/lib/clang/19/include",
            "/usr/lib/gcc/x86_64-redhat-linux/11/include",
            "/usr/include"
        ]
        
        current_c_include = os.environ.get("C_INCLUDE_PATH", "")
        current_cplus_include = os.environ.get("CPLUS_INCLUDE_PATH", "")
        
        for path in header_paths:
            if path not in current_c_include:
                os.environ["C_INCLUDE_PATH"] = f"{path}:{current_c_include}" if current_c_include else path
            if path not in current_cplus_include:
                os.environ["CPLUS_INCLUDE_PATH"] = f"{path}:{current_cplus_include}" if current_cplus_include else path
        
        smart_log("✅ Updated header environment variables")
        return 1
        
    except Exception as e:
        smart_log(f"❌ Failed to fix stdbool headers: {e}")
        return 0

def fix_shiboken_wrapper():
    """Update or create enhanced Shiboken wrapper"""
    smart_log("🔧 Updating Shiboken wrapper...")
    
    try:
        build_dir = os.environ.get("REZ_BUILD_PATH", "build")
        wrapper_dir = os.path.join(build_dir, "shiboken_wrapper")
        os.makedirs(wrapper_dir, exist_ok=True)
        
        wrapper_script = os.path.join(wrapper_dir, "shiboken6")
        
        wrapper_content = '''#!/bin/bash
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
'''
        
        with open(wrapper_script, 'w') as f:
            f.write(wrapper_content)
        
        os.chmod(wrapper_script, 0o755)
        
        # Update PATH
        current_path = os.environ.get("PATH", "")
        if wrapper_dir not in current_path:
            os.environ["PATH"] = f"{wrapper_dir}:{current_path}"
        
        smart_log(f"✅ Updated Shiboken wrapper: {wrapper_script}")
        return 1
        
    except Exception as e:
        smart_log(f"❌ Failed to fix Shiboken wrapper: {e}")
        return 0

def fix_python_environment():
    """Fix Python environment and paths"""
    smart_log("🔧 Fixing Python environment...")
    
    try:
        # Ensure rez Python is used
        rez_python_paths = [
            "/core/Linux/APPZ/packages/python/3.13.2/bin/python3",
            "/core/Linux/APPZ/packages/python/3.13.2/bin/python"
        ]
        
        for python_path in rez_python_paths:
            if os.path.exists(python_path):
                python_bin_dir = os.path.dirname(python_path)
                current_path = os.environ.get("PATH", "")
                if python_bin_dir not in current_path:
                    os.environ["PATH"] = f"{python_bin_dir}:{current_path}"
                    smart_log(f"✅ Added {python_bin_dir} to PATH")
                    return 1
        
        smart_log("⚠️  Rez Python not found, using system Python")
        return 0
        
    except Exception as e:
        smart_log(f"❌ Failed to fix Python environment: {e}")
        return 0

def fix_cmake_configuration():
    """Fix CMake configuration issues"""
    smart_log("🔧 Fixing CMake configuration...")
    
    try:
        # Ensure critical environment variables are set
        required_vars = {
            "QT_DIR": "/core/Linux/APPZ/packages/qt/6.9.1",
            "SHIBOKEN_DIR": "/core/Linux/APPZ/packages/shiboken6/6.9.1",
        }
        
        updates = 0
        for var, value in required_vars.items():
            if not os.environ.get(var) and os.path.exists(value):
                os.environ[var] = value
                updates += 1
                smart_log(f"✅ Set {var}={value}")
        
        # Update CMAKE_PREFIX_PATH
        cmake_paths = [
            "/core/Linux/APPZ/packages/qt/6.9.1",
            "/core/Linux/APPZ/packages/shiboken6/6.9.1"
        ]
        
        current_cmake_path = os.environ.get("CMAKE_PREFIX_PATH", "")
        for path in cmake_paths:
            if os.path.exists(path) and path not in current_cmake_path:
                if current_cmake_path:
                    os.environ["CMAKE_PREFIX_PATH"] = f"{path}:{current_cmake_path}"
                else:
                    os.environ["CMAKE_PREFIX_PATH"] = path
                updates += 1
        
        return updates
        
    except Exception as e:
        smart_log(f"❌ Failed to fix CMake configuration: {e}")
        return 0

def run_cmd(cmd, cwd=None):
    """Enhanced run_cmd with smart error handling"""
    global _error_count, _retry_count
    
    smart_log(f"🚀 Executing: {cmd}")
    
    for attempt in range(_max_retries):
        try:
            result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                                   capture_output=True, text=True)
            smart_log("✅ Command completed successfully")
            return result
            
        except subprocess.CalledProcessError as e:
            _error_count += 1
            smart_log(f"❌ Command failed (attempt {attempt + 1}/{_max_retries}): {e}")
            
            if e.stderr:
                smart_log(f"stderr: {e.stderr[:500]}")
            if e.stdout:
                smart_log(f"stdout: {e.stdout[:500]}")
            
            if attempt < _max_retries - 1:
                # Try to apply fixes before retry
                if analyze_and_fix_errors():
                    smart_log("🔄 Fixes applied, retrying...")
                    time.sleep(5)
                else:
                    smart_log(f"⏳ Waiting before retry {attempt + 2}...")
                    time.sleep(10 * (attempt + 1))
            else:
                smart_log("❌ All retry attempts exhausted")
                raise

def clean_build_dir(build_path):
    if os.path.exists(build_path):
        print(f"🧹 Cleaning build directory (preserving .rxt/.json): {build_path}")
        for item in os.listdir(build_path):
            if item.endswith(".rxt") or item.endswith(".json"):
                print(f"🔒 Preserving {item}")
                continue
            p = os.path.join(build_path, item)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)

def clean_install_dir(install_path):
    if os.path.exists(install_path):
        print(f"🧹 Attempting to remove install directory: {install_path}")
        try:
            # 강제 삭제를 위해 권한 변경
            def handle_remove_readonly(func, path, exc):
                try:
                    os.chmod(path, 0o777)
                    func(path)
                except:
                    pass  # NFS 파일이면 무시
            
            shutil.rmtree(install_path, onerror=handle_remove_readonly)
            print(f"✅ Install directory removed: {install_path}")
        except OSError as e:
            if "Device or resource busy" in str(e) or ".nfs" in str(e):
                print(f"⚠️  Warning: Cannot remove {install_path} (NFS busy files)")
                print(f"    Will install over existing files")
            else:
                raise

def ensure_source(version, source_path):
    """이미 준비된 소스 디렉토리 확인"""
    src = os.path.join(source_path, "source", "pyside-setup")
    if not os.path.isdir(src):
        raise RuntimeError(f"PySide6 source not found at {src}. Please ensure source is prepared manually.")
    
    print(f"✅ Source present: {src}")
    
    # CMakeLists.txt나 setup.py 존재 확인으로 유효성 검증
    if not (os.path.exists(os.path.join(src, "setup.py")) or 
            os.path.exists(os.path.join(src, "CMakeLists.txt"))):
        raise RuntimeError(f"Invalid PySide6 source directory: {src}")
    
    print(f"✅ Source validation passed")
    return src

def verify_prerequisites():
    """빌드 전 필수 구성 요소 확인"""
    print("🔍 Verifying build prerequisites...")
    
    # Python 확인 - rez 환경의 Python 사용!
    python_exe = shutil.which("python3")
    if not python_exe:
        raise RuntimeError("Python 3 not found in PATH")
    
    # rez 환경의 Python인지 확인
    if "/core/Linux/APPZ/packages/python" not in python_exe:
        print(f"⚠️  Warning: Using system Python: {python_exe}")
        print("🔍 Looking for rez Python...")
        
        # rez 환경에서 Python 찾기
        rez_python_paths = [
            "/core/Linux/APPZ/packages/python/3.13.2/bin/python3",
            "/core/Linux/APPZ/packages/python/3.13.2/bin/python"
        ]
        
        for rez_python in rez_python_paths:
            if os.path.exists(rez_python):
                python_exe = rez_python
                print(f"✅ Found rez Python: {python_exe}")
                # PATH 업데이트
                python_bin_dir = os.path.dirname(python_exe)
                current_path = os.environ.get("PATH", "")
                os.environ["PATH"] = f"{python_bin_dir}:{current_path}"
                break
        else:
            raise RuntimeError("Rez Python not found. Please ensure python-3.13.2 package is loaded.")
    else:
        print(f"✅ Using rez Python: {python_exe}")
    
    result = subprocess.run([python_exe, "--version"], capture_output=True, text=True)
    python_version = result.stdout.strip()
    print(f"✅ Python: {python_version}")
    
    # qmake 확인
    qmake_exe = shutil.which("qmake")
    if not qmake_exe:
        raise RuntimeError("qmake not found in PATH")
    print(f"✅ qmake found: {qmake_exe}")
    
    # shiboken6 확인
    shiboken_exe = shutil.which("shiboken6")
    if not shiboken_exe:
        raise RuntimeError("shiboken6 not found in PATH")
    print(f"✅ shiboken6 found: {shiboken_exe}")
    
    # 필수 헤더 확인
    required_headers = [
        "/usr/lib/clang/19/include/stdbool.h",
        "/usr/lib/gcc/x86_64-redhat-linux/11/include/stdbool.h"
    ]
    
    python_include = subprocess.run([
        python_exe, "-c", 
        "import sysconfig; print(sysconfig.get_path('include'))"
    ], capture_output=True, text=True).stdout.strip()
    
    python_h = os.path.join(python_include, "Python.h")
    if not os.path.exists(python_h):
        raise RuntimeError(f"Python.h not found at {python_h}")
    print(f"✅ Python.h found: {python_h}")
    
    for header in required_headers:
        if os.path.exists(header):
            print(f"✅ Header found: {header}")
        else:
            print(f"⚠️  Header missing: {header}")
    
    print("✅ Prerequisites verification completed")
    return python_exe  # rez Python 경로 반환

def setup_build_environment():
    """PySide6 빌드를 위한 환경 설정"""
    print("🔧 Setting up build environment...")
    
    # Qt 경로 확인
    qt_dir = os.environ.get("QT_DIR")
    if not qt_dir:
        qmake_path = shutil.which("qmake")
        if qmake_path:
            qt_dir = os.path.dirname(os.path.dirname(qmake_path))
    
    if not qt_dir or not os.path.exists(qt_dir):
        raise RuntimeError("Qt installation not found")
    
    print(f"✅ Qt directory: {qt_dir}")
    
    # Shiboken 경로 확인
    shiboken_dir = os.environ.get("SHIBOKEN_DIR")
    if not shiboken_dir:
        shiboken_path = shutil.which("shiboken6")
        if shiboken_path:
            shiboken_dir = os.path.dirname(os.path.dirname(shiboken_path))
    
    print(f"✅ Shiboken directory: {shiboken_dir}")
    
    # minizip_ng 경로 확인
    minizip_ng_dir = os.environ.get("MINIZIP_NG_ROOT")
    if not minizip_ng_dir:
        # rez 환경에서 minizip_ng 패키지 경로 찾기
        for potential_path in ["/core/Linux/APPZ/packages/minizip_ng/4.0.10"]:
            if os.path.exists(potential_path):
                minizip_ng_dir = potential_path
                break
    
    print(f"✅ minizip_ng directory: {minizip_ng_dir}")
    
    # 환경 변수 설정
    cmake_prefix_paths = [qt_dir, shiboken_dir]
    if minizip_ng_dir:
        cmake_prefix_paths.append(minizip_ng_dir)
    cmake_prefix_paths.append(os.environ.get('CMAKE_PREFIX_PATH', ''))
    
    env_vars = {
        "QMAKE": os.path.join(qt_dir, "bin", "qmake"),
        "QT_QMAKE_EXECUTABLE": os.path.join(qt_dir, "bin", "qmake"),
        "CMAKE_PREFIX_PATH": ":".join(filter(None, cmake_prefix_paths)),
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"🔧 {key}={value}")
    
    return qt_dir, shiboken_dir

def create_shiboken_wrapper(build_path):
    """Shiboken 래퍼 스크립트 생성 (핵심 해결책!)"""
    wrapper_dir = os.path.join(build_path, "shiboken_wrapper")
    os.makedirs(wrapper_dir, exist_ok=True)
    
    wrapper_script = os.path.join(wrapper_dir, "shiboken6")
    
    wrapper_content = '''#!/bin/bash
# Shiboken wrapper to add proper include paths

# Add rez GCC headers (same as our build environment)
EXTRA_ARGS=""
EXTRA_ARGS="$EXTRA_ARGS -I/usr/include"
EXTRA_ARGS="$EXTRA_ARGS -I/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/lib/gcc/x86_64-pc-linux-gnu/11.5.0/include"
EXTRA_ARGS="$EXTRA_ARGS -I/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/lib/gcc/x86_64-pc-linux-gnu/11.5.0/include-fixed"
EXTRA_ARGS="$EXTRA_ARGS -I/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/include/c++/11.5.0"
EXTRA_ARGS="$EXTRA_ARGS -I/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/include/c++/11.5.0/x86_64-pc-linux-gnu"
EXTRA_ARGS="$EXTRA_ARGS -I/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/include/c++/11.5.0/backward"

# Set environment to match our build environment
export C_INCLUDE_PATH="/usr/include:/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/lib/gcc/x86_64-pc-linux-gnu/11.5.0/include:/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/lib/gcc/x86_64-pc-linux-gnu/11.5.0/include-fixed"
export CPLUS_INCLUDE_PATH="/usr/include:/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/lib/gcc/x86_64-pc-linux-gnu/11.5.0/include:/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/lib/gcc/x86_64-pc-linux-gnu/11.5.0/include-fixed:/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/include/c++/11.5.0:/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/include/c++/11.5.0/x86_64-pc-linux-gnu:/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/include/c++/11.5.0/backward"

# Find original shiboken6
ORIGINAL_SHIBOKEN=$(which shiboken6 | grep -v shiboken_wrapper | head -1)
if [ -z "$ORIGINAL_SHIBOKEN" ]; then
    # Fallback paths
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

# Call original shiboken6 with additional arguments
exec "$ORIGINAL_SHIBOKEN" $EXTRA_ARGS "$@"
'''
    
    with open(wrapper_script, 'w') as f:
        f.write(wrapper_content)
    
    os.chmod(wrapper_script, 0o755)
    print(f"🔧 Created shiboken wrapper: {wrapper_script}")
    
    # PATH 앞에 래퍼 디렉토리 추가
    os.environ["PATH"] = f"{wrapper_dir}:{os.environ.get('PATH', '')}"
    
    return wrapper_dir

def build_pyside6_direct(src, build_path, install_root, rez_python_exe):
    """PySide6 직접 빌드 (CMake를 이용해 기존 shiboken6 사용)"""
    print("🔨 Building PySide6 directly using CMake with existing shiboken6...")
    
    # rez Python 사용
    python_exe = rez_python_exe
    python_version = subprocess.run([
        python_exe, "-c", 
        "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    ], capture_output=True, text=True).stdout.strip()
    
    print(f"🐍 Using Python: {python_exe}")
    print(f"🐍 Python version: {python_version}")
    
    # 경로 설정
    qt_dir = "/core/Linux/APPZ/packages/qt/6.9.1"
    shiboken_dir = "/core/Linux/APPZ/packages/shiboken6/6.9.1"
    pyside_src = os.path.join(src, "sources", "pyside6")
    
    # 빌드 디렉토리 생성
    pyside_build_dir = os.path.join(build_path, "pyside6")
    os.makedirs(pyside_build_dir, exist_ok=True)
    os.chdir(pyside_build_dir)
    
    # 환경 변수 설정
    build_env = os.environ.copy()
    gcc13_root = "/opt/rh/gcc-toolset-13/root/usr"
    gcc13_base = "/opt/rh/gcc-toolset-13/root"
    
    rpmlibdir = "/usr/lib64"
    gcc13_ld_paths = [
        f"{gcc13_base}{rpmlibdir}",
        f"{gcc13_base}/usr/lib"
    ]
    
    dependency_lib_paths = [
        "/core/Linux/APPZ/packages/qt/6.9.1/lib",
        "/core/Linux/APPZ/packages/shiboken6/6.9.1/lib",
        "/core/Linux/APPZ/packages/minizip_ng/4.0.10/lib",
    ]
    
    build_env.update({
        "CC": f"{gcc13_root}/bin/gcc",
        "CXX": f"{gcc13_root}/bin/g++",
        "PATH": f"{qt_dir}/bin:{gcc13_root}/bin:{build_env.get('PATH', '')}",
        "LD_LIBRARY_PATH": ":".join(gcc13_ld_paths + dependency_lib_paths + [build_env.get("LD_LIBRARY_PATH", "")]),
        "PKG_CONFIG_PATH": f"{qt_dir}/lib/pkgconfig:{shiboken_dir}/lib/pkgconfig:{build_env.get('PKG_CONFIG_PATH', '')}",
        "CMAKE_PREFIX_PATH": f"{qt_dir}:{shiboken_dir}",
    })
    
    # CMake 설정
    cmake_args = [
        "cmake",
        pyside_src,
        f"-DCMAKE_INSTALL_PREFIX={install_root}",
        f"-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_PREFIX_PATH={qt_dir};{shiboken_dir}",
        f"-DPython_EXECUTABLE={python_exe}",
        f"-DPYTHON_EXECUTABLE={python_exe}",
        f"-DBUILD_TESTS=OFF",
        f"-DUSE_PYTHON_VERSION={python_version}",
        "-G", "Ninja"
    ]
    
    print(f"🔧 CMake command: {' '.join(cmake_args)}")
    
    try:
        # CMake 설정 실행
        result = subprocess.run(cmake_args, cwd=pyside_build_dir, env=build_env, check=True)
        print("✅ CMake configuration successful!")
        
        # Ninja 빌드 실행
        ninja_cmd = ["ninja", f"-j{os.cpu_count()}"]
        print(f"🔧 Ninja command: {' '.join(ninja_cmd)}")
        result = subprocess.run(ninja_cmd, cwd=pyside_build_dir, env=build_env, check=True)
        print("✅ Ninja build successful!")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Direct PySide6 build failed: {e}")
        return False

def build_pyside6(src, build_path, install_root, rez_python_exe):
    """PySide6 빌드 실행 - 직접 빌드 방식 우선 시도"""
    print("🔨 Building PySide6...")
    
    # 먼저 직접 CMake 빌드 시도
    if build_pyside6_direct(src, build_path, install_root, rez_python_exe):
        return True
    
    print("🔧 Direct build failed, trying setup.py method...")
    
    # 소스 디렉토리로 이동
    os.chdir(src)
    
    # rez Python 사용!
    python_exe = rez_python_exe
    python_version = subprocess.run([
        python_exe, "-c", 
        "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    ], capture_output=True, text=True).stdout.strip()
    
    print(f"🐍 Using Python: {python_exe}")
    print(f"🐍 Python version: {python_version}")
    
    # Qt 경로 확인
    qt_dir = os.environ.get("QT_DIR", "/core/Linux/APPZ/packages/qt/6.9.1")
    shiboken_dir = os.environ.get("SHIBOKEN_DIR", "/core/Linux/APPZ/packages/shiboken6/6.9.1")
    
    print(f"🔧 Qt directory: {qt_dir}")
    print(f"🔧 Shiboken directory: {shiboken_dir}")
    
    # build.sh와 동일한 환경 변수 설정
    build_env = os.environ.copy()
    
    # GCC 13 toolset 설정
    gcc13_root = "/opt/rh/gcc-toolset-13/root/usr"
    gcc13_base = "/opt/rh/gcc-toolset-13/root"
    
    # GCC 라이브러리 경로 설정
    dependency_lib_paths = [
        "/core/Linux/APPZ/packages/qt/6.9.1/lib",
        "/core/Linux/APPZ/packages/shiboken6/6.9.1/lib",
        "/core/Linux/APPZ/packages/minizip_ng/4.0.10/lib",
    ]
    
    # GCC 13 toolset LD_LIBRARY_PATH 계산
    rpmlibdir = "/usr/lib64"
    gcc13_ld_paths = [
        f"{gcc13_base}{rpmlibdir}",
        f"{gcc13_base}/usr/lib"
    ]
    
    # 환경 변수 업데이트 (build.sh 성공 방식)
    build_env.update({
        # Qt 환경
        "QT_DIR": qt_dir,
        "CMAKE_PREFIX_PATH": f"{qt_dir}:{shiboken_dir}:{build_env.get('CMAKE_PREFIX_PATH', '')}",
        "PATH": f"{qt_dir}/bin:{build_env.get('PATH', '')}",
        "LD_LIBRARY_PATH": f"{qt_dir}/lib:{':'.join(gcc13_ld_paths + dependency_lib_paths)}:{build_env.get('LD_LIBRARY_PATH', '')}",
        "PKG_CONFIG_PATH": f"{qt_dir}/lib/pkgconfig:{build_env.get('PKG_CONFIG_PATH', '')}",
        
        # Shiboken 환경
        "SHIBOKEN_DIR": shiboken_dir,
        
        # GCC 13 toolset 환경
        "CC": f"{gcc13_root}/bin/gcc",
        "CXX": f"{gcc13_root}/bin/g++",
        "MANPATH": f"{gcc13_root}/share/man:{build_env.get('MANPATH', '')}",
        "INFOPATH": f"{gcc13_root}/share/info:{build_env.get('INFOPATH', '')}",
        
        # Python 환경
        "PYTHON": python_exe,
        "PYTHON3": python_exe, 
        "PYTHON_EXECUTABLE": python_exe,
        "PYTHONPATH": f"{install_root}/lib/python{python_version}/site-packages:{build_env.get('PYTHONPATH', '')}",
        
        # 헤더 경로 설정 (build.sh에서 성공한 방식)
        "CLANG_HEADERS": "/usr/lib/clang/19/include",
        "GCC_HEADERS": "/usr/lib/gcc/x86_64-redhat-linux/11/include",
        "SYSTEM_HEADERS": "/usr/include",
        "CPP_HEADERS": "/usr/include/c++/11",
        "CLANG_BUILTIN_INCLUDE_DIR": "/usr/lib/clang/19/include",
        "C_INCLUDE_PATH": "/usr/lib/gcc/x86_64-redhat-linux/11/include:/usr/lib/clang/19/include:/usr/include",
        "CPLUS_INCLUDE_PATH": "/usr/include/c++/11:/usr/lib/gcc/x86_64-redhat-linux/11/include:/usr/lib/clang/19/include:/usr/include",
        "CLANG_INCLUDE_PATHS": "/usr/lib/clang/19/include:/usr/lib/gcc/x86_64-redhat-linux/11/include:/usr/include/c++/11:/usr/include",
        "SHIBOKEN_INCLUDE_PATHS": "/usr/lib/clang/19/include:/usr/lib/gcc/x86_64-redhat-linux/11/include:/usr/include",
        
        # 빌드 환경
        "MAKEFLAGS": f"-j{os.cpu_count()}",
        "NINJA_STATUS": "[%f/%t] ",
        "PYSIDE_BUILD_DIR": build_path,
        "PYSIDE_INSTALL_DIR": install_root,
    })
    
    print("✅ Build environment configured using build.sh method")
    print(f"🔧 CC={build_env['CC']}")
    print(f"🔧 CXX={build_env['CXX']}")
    
    # build.sh에서 성공한 방식: --only 옵션을 사용해 PySide6만 빌드
    print("🔧 Building PySide6 only (skip shiboken6)...")
    
    try:
        # PySide6만 빌드하는 명령어 
        pyside_only_cmd = [
            python_exe, "setup.py", "build",
            "--qmake", f"{qt_dir}/bin/qmake",
            "--parallel", str(os.cpu_count()),
            "--module-subset=PySide6",
            "--skip-modules=shiboken6",
            "--reuse-build",
            f"--shiboken-target-path={shiboken_dir}",
            "--verbose-build"
        ]
        
        print(f"🔧 PySide6 only build command: {' '.join(pyside_only_cmd)}")
        result = subprocess.run(pyside_only_cmd, cwd=src, env=build_env, check=True)
        print("✅ PySide6 build successful!")
        return True
            
    except subprocess.CalledProcessError as e:
        print(f"❌ PySide6 build failed: {e}")
        return False

def install_pyside6(src, build_path, install_root, rez_python_exe):
    """PySide6 설치 (rezbuild_multi.py 성공 방식)"""
    print("📦 Installing PySide6...")
    
    python_exe = rez_python_exe
    python_version = subprocess.run([
        python_exe, "-c", 
        "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    ], capture_output=True, text=True).stdout.strip()
    
    # Python 설치 경로 계산
    python_install_path = f"{install_root}/lib/python{python_version}/site-packages"
    
    # 현재 빌드 환경 유지
    install_env = os.environ.copy()
    
    # 설치 명령어 (rezbuild_multi.py 방식)
    install_cmd = [
        python_exe, "setup.py", "install",
        f"--build-base={build_path}",
        f"--prefix={install_root}",
        f"--install-platlib={python_install_path}",
        f"--install-purelib={python_install_path}",
        "--force"
    ]
    
    print(f"📦 Install command: {' '.join(install_cmd)}")
    
    # 설치 실행
    try:
        subprocess.run(install_cmd, cwd=src, env=install_env, check=True)
        print(f"✅ PySide6 successfully installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ PySide6 install failed: {e}")
        return False

def build_pyside_tools(python_exe, src, build_path, install_root, env):
    """pyside-tools 별도 빌드 (rezbuild_multi.py 방식)"""
    print("🔧 Building pyside-tools separately...")
    
    # pyside-tools만 빌드
    tools_build_cmd = [
        python_exe, "setup.py", "build",
        f"--build-base={build_path}",
        "--parallel=4",
        "--verbose-build",
        "--standalone",
        "--ignore-git",
        f"--qtpaths=/core/Linux/APPZ/packages/qt/6.9.1/bin/qtpaths",
        f"--cmake=/usr/bin/cmake",
        f"--shiboken-config-dir=/core/Linux/APPZ/packages/shiboken6/6.9.1/lib/cmake/Shiboken6",
        f"--shiboken-target-path=/core/Linux/APPZ/packages/shiboken6/6.9.1",
        "--module-subset=pyside-tools",
    ]
    
    print(f"🔧 Tools build command: {' '.join(tools_build_cmd)}")
    
    try:
        subprocess.run(tools_build_cmd, cwd=src, env=env, check=True)
        
        # pyside-tools 설치
        python_version = subprocess.run([
            python_exe, "-c", 
            "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        ], capture_output=True, text=True).stdout.strip()
        
        python_install_path = f"{install_root}/lib/python{python_version}/site-packages"
        
        tools_install_cmd = [
            python_exe, "setup.py", "install",
            f"--build-base={build_path}",
            f"--prefix={install_root}",
            f"--install-platlib={python_install_path}",
            f"--install-purelib={python_install_path}",
            f"--install-scripts={install_root}/bin",  # bin wrapper 스크립트들 설치 경로
            "--force"
        ]
        
        print(f"📦 Tools install command: {' '.join(tools_install_cmd)}")
        subprocess.run(tools_install_cmd, cwd=src, env=env, check=True)
        
        print("✅ pyside-tools successfully built and installed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ pyside-tools build/install failed: {e}")
        return False

def create_test_script(install_root):
    """설치 후 테스트 스크립트 생성"""
    bin_dir = os.path.join(install_root, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    
    test_script = os.path.join(bin_dir, "test_pyside6.py")
    
    test_content = '''#!/usr/bin/env python3
import sys
import os

def test_pyside6():
    """PySide6 설치 테스트"""
    print("🧪 Testing PySide6 installation...")
    
    try:
        from PySide6.QtCore import QCoreApplication, QTimer
        print("✅ PySide6.QtCore import successful!")
        
        from PySide6.QtWidgets import QApplication, QWidget
        print("✅ PySide6.QtWidgets import successful!")
        
        from PySide6.QtGui import QGuiApplication
        print("✅ PySide6.QtGui import successful!")
        
        # 버전 정보
        try:
            version = QCoreApplication.applicationVersion()
            if version:
                print(f"✅ PySide6 version: {version}")
            else:
                print("✅ PySide6 version: (not set)")
        except:
            print("✅ PySide6 version check completed")
        
        print("✅ PySide6 installation test passed!")
        return True
        
    except ImportError as e:
        print(f"❌ PySide6 import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ PySide6 test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_pyside6()
    sys.exit(0 if success else 1)
'''
    
    with open(test_script, 'w') as f:
        f.write(test_content)
    
    os.chmod(test_script, 0o755)
    print(f"📄 Created test script: {test_script}")
    
    return test_script

def copy_license(src, install_root):
    """라이선스 파일 복사"""
    for fname in ("LICENSE", "COPYING", "LICENSE.txt"):
        src_path = os.path.join(src, fname)
        if os.path.isfile(src_path):
            dst_path = os.path.join(install_root, "LICENSE")
            print(f"📄 Copying {fname} → {dst_path}")
            shutil.copy(src_path, dst_path)
            return
    
    # 라이선스 파일이 없으면 기본 정보 생성
    license_content = """PySide6 - Python bindings for Qt6

PySide6 is distributed under the GNU Lesser General Public License (LGPL) version 3.

For full license details, see:
- https://www.gnu.org/licenses/lgpl-3.0.html
- https://doc.qt.io/qtforpython/licenses.html

This package was built from source and includes Qt6 bindings for Python.
"""
    
    license_path = os.path.join(install_root, "LICENSE")
    with open(license_path, 'w') as f:
        f.write(license_content)
    
    print(f"📄 Created license file: {license_path}")

def copy_missing_libraries(src, build_path, install_root):
    """빌드된 라이브러리들을 install 경로로 복사"""
    print("📚 Copying missing PySide6 libraries...")
    
    build_dir = os.path.join(src, "..", "build", "qfp-py3.13-qt6.9.1-64bit-release", "build", "pyside6")
    lib_dir = os.path.join(install_root, "lib")
    pyside_lib_dir = os.path.join(lib_dir, "python3.13", "site-packages", "PySide6")
    
    # 1. Core PySide6 libraries
    libpyside_dir = os.path.join(build_dir, "libpyside")
    if os.path.exists(libpyside_dir):
        for lib_file in os.listdir(libpyside_dir):
            if lib_file.startswith("libpyside6") and lib_file.endswith(".so"):
                src_lib = os.path.join(libpyside_dir, lib_file)
                dst_lib = os.path.join(lib_dir, lib_file)
                if os.path.isfile(src_lib):
                    shutil.copy2(src_lib, dst_lib)
                    print(f"📚 Copied {lib_file}")
    
    # 2. PySide6 QML libraries
    libpysideqml_dir = os.path.join(build_dir, "libpysideqml")
    if os.path.exists(libpysideqml_dir):
        for lib_file in os.listdir(libpysideqml_dir):
            if lib_file.startswith("libpyside6qml") and lib_file.endswith(".so"):
                src_lib = os.path.join(libpysideqml_dir, lib_file)
                dst_lib = os.path.join(lib_dir, lib_file)
                if os.path.isfile(src_lib):
                    shutil.copy2(src_lib, dst_lib)
                    print(f"📚 Copied {lib_file}")
    
    # 3. All PySide6 modules (.so files)
    pyside_build_dir = os.path.join(build_dir, "PySide6")
    if os.path.exists(pyside_build_dir):
        os.makedirs(pyside_lib_dir, exist_ok=True)
        
        # Copy .so modules
        for item in os.listdir(pyside_build_dir):
            if item.endswith(".abi3.so"):
                src_file = os.path.join(pyside_build_dir, item)
                dst_file = os.path.join(pyside_lib_dir, item)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)
                    print(f"📚 Copied module {item}")
        
        # Copy Python files and stubs
        for item in os.listdir(pyside_build_dir):
            if item.endswith((".py", ".pyi")):
                src_file = os.path.join(pyside_build_dir, item)
                dst_file = os.path.join(pyside_lib_dir, item)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)
        
        # Copy support directory
        support_src = os.path.join(pyside_build_dir, "support")
        support_dst = os.path.join(pyside_lib_dir, "support")
        if os.path.exists(support_src):
            if os.path.exists(support_dst):
                shutil.rmtree(support_dst)
            shutil.copytree(support_src, support_dst)
            print("📚 Copied support directory")
    
    # 4. Create symbolic links for library versions
    os.chdir(lib_dir)
    for lib_pattern in ["libpyside6.abi3.so", "libpyside6qml.abi3.so"]:
        full_lib = None
        for f in os.listdir("."):
            if f.startswith(lib_pattern) and f.count(".") >= 3:  # e.g., libpyside6.abi3.so.6.9.1
                full_lib = f
                break
        
        if full_lib:
            # Create version links
            version_parts = full_lib.split(".")
            if len(version_parts) >= 5:  # libpyside6.abi3.so.6.9.1
                base_name = ".".join(version_parts[:3])  # libpyside6.abi3.so
                short_version = ".".join(version_parts[:4])  # libpyside6.abi3.so.6.9
                
                # Create links
                if not os.path.exists(base_name):
                    os.symlink(full_lib, base_name)
                    print(f"📚 Created link: {base_name} -> {full_lib}")
                if not os.path.exists(short_version):
                    os.symlink(full_lib, short_version)
                    print(f"📚 Created link: {short_version} -> {full_lib}")

def copy_package_py(source_path, install_path):
    src = os.path.join(source_path, "package.py")
    dst = os.path.join(install_path, "package.py")
    print(f"📄 Copying package.py → {dst}")
    shutil.copy(src, dst)

def write_build_marker(build_path):
    marker = os.path.join(build_path, "build.rxt")
    print(f"📝 Touching build marker: {marker}")
    open(marker, "a").close()

def build_multi_python(source_path, build_path, install_path, targets):
    """Multi-Python version build function according to updated readme.md"""
    global _build_log_file
    
    version = os.environ.get("REZ_BUILD_PROJECT_VERSION", "6.9.1")
    
    # Python versions from updated readme.md
    python_versions = ["3.9.21", "3.10.6", "3.11.9", "3.12.10", "3.13.2"]
    
    # Setup smart build logging
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    _build_log_file = os.path.join(build_path, f"multi_python_pyside6_{timestamp}.log")
    
    # install 타겟인 경우 /core 경로 사용
    install_root = f"/core/Linux/APPZ/packages/pyside6/{version}" if "install" in targets else install_path
    
    smart_log("="*60)
    smart_log("🚀 Multi-Python PySide6 Build Manager Starting")
    smart_log("="*60)
    smart_log(f"📦 PySide6 version: {version}")
    smart_log(f"🐍 Target Python versions: {', '.join(python_versions)}")
    smart_log(f"📁 Source path: {source_path}")
    smart_log(f"📁 Build path: {build_path}")
    smart_log(f"📁 Install path: {install_root}")
    smart_log(f"📝 Log file: {_build_log_file}")
    
    # Terminate any running builds
    detect_and_terminate_builds()
    
    # Apply pre-build fixes
    smart_log("🔧 Applying pre-build environment fixes...")
    fix_python_environment()
    fix_cmake_configuration()
    fix_stdbool_headers()
    fix_shiboken_wrapper()
    
    # 소스 확인
    src = ensure_source(version, source_path)
    
    successful_builds = []
    failed_builds = []
    
    for python_version in python_versions:
        smart_log(f"\n{'='*60}")
        smart_log(f"🐍 Building PySide6 for Python {python_version}")
        smart_log(f"{'='*60}")
        
        try:
            # Create version-specific build directory
            python_major_minor = ".".join(python_version.split(".")[:2])
            version_build_path = os.path.join(build_path, f"py{python_major_minor}")
            
            # Clean version-specific build directory
            clean_build_dir(version_build_path)
            
            # Find specific Python version
            rez_python_exe = find_rez_python_version(python_version)
            if not rez_python_exe:
                error_msg = f"Python {python_version} not found"
                smart_log(f"❌ {error_msg}", "ERROR")
                failed_builds.append((python_version, error_msg))
                continue
            
            smart_log(f"🐍 Using Python executable: {rez_python_exe}")
            
            # 환경 설정
            qt_dir, shiboken_dir = setup_build_environment()
            
            # Shiboken 래퍼 생성
            create_shiboken_wrapper(version_build_path)
            
            # PySide6 빌드
            if build_pyside6(src, version_build_path, install_root, rez_python_exe):
                smart_log(f"✅ Build successful for Python {python_version}")
                
                if "install" in targets:
                    # 설치 디렉토리 생성
                    os.makedirs(install_root, exist_ok=True)
                    
                    # PySide6 설치
                    if install_pyside6(src, version_build_path, install_root, rez_python_exe):
                        smart_log(f"✅ Installation successful for Python {python_version}")
                        python_site_packages = os.path.join(install_root, "lib", f"python{python_major_minor}", "site-packages")
                        successful_builds.append((python_version, python_site_packages))
                    else:
                        error_msg = f"Installation failed for Python {python_version}"
                        smart_log(f"❌ {error_msg}", "ERROR")
                        failed_builds.append((python_version, error_msg))
                else:
                    successful_builds.append((python_version, version_build_path))
            else:
                error_msg = f"Build failed for Python {python_version}"
                smart_log(f"❌ {error_msg}", "ERROR")  
                failed_builds.append((python_version, error_msg))
                
        except Exception as e:
            error_msg = f"Exception for Python {python_version}: {str(e)}"
            smart_log(f"❌ {error_msg}", "ERROR")
            failed_builds.append((python_version, error_msg))
            continue
    
    # Post-build tasks for successful builds
    if successful_builds and "install" in targets:
        smart_log("🔧 Performing post-build tasks...")
        
        # 누락된 라이브러리들 복사
        copy_missing_libraries(src, build_path, install_root)
        
        # 테스트 스크립트 생성
        test_script = create_test_script(install_root)
        
        # 라이선스 및 패키지 파일 복사
        copy_license(src, install_root)
        copy_package_py(source_path, install_root)
        
        # 통합 설치 테스트
        smart_log("🧪 Running multi-Python installation tests...")
        test_multi_python_installation(install_root, successful_builds)
    
    # 빌드 마커 생성
    write_build_marker(build_path)
    
    # Final results summary
    smart_log(f"\n{'='*60}")
    smart_log("🎯 Multi-Python Build Summary")
    smart_log(f"{'='*60}")
    
    if successful_builds:
        smart_log("✅ Successful builds:")
        for version, path in successful_builds:
            smart_log(f"   - Python {version}: {path}")
    
    if failed_builds:
        smart_log("❌ Failed builds:")
        for version, error in failed_builds:
            smart_log(f"   - Python {version}: {error}")
    
    # Final verification
    if successful_builds:
        smart_log("🔍 Performing final verification...")
        if verify_installation(install_root):
            smart_log("🎉 Multi-Python PySide6 build completed successfully!")
            smart_log("✅ All required tools are present and functional")
        else:
            smart_log("⚠️  Build completed but verification issues detected")
    
    smart_log("📊 Build Statistics:")
    smart_log(f"   Total Python versions: {len(python_versions)}")
    smart_log(f"   Successful builds: {len(successful_builds)}")  
    smart_log(f"   Failed builds: {len(failed_builds)}")
    smart_log(f"   Total errors encountered: {_error_count}")
    smart_log(f"   Log file: {_build_log_file}")
    
    if successful_builds and not failed_builds:
        smart_log("🎉 All Python versions built successfully!")
        return True
    elif successful_builds:
        smart_log("⚠️  Partial success - some Python versions built successfully")
        return True
    else:
        smart_log("💥 All Python version builds failed!")
        return False

def find_rez_python_version(python_version):
    """Find specific rez Python version executable"""
    python_exe_paths = [
        f"/core/Linux/APPZ/packages/python/{python_version}/bin/python3",
        f"/core/Linux/APPZ/packages/python/{python_version}/bin/python"
    ]
    
    for path in python_exe_paths:
        if os.path.exists(path):
            smart_log(f"✅ Found Python {python_version}: {path}")
            return path
    
    smart_log(f"⚠️ Python {python_version} not found at expected paths", "WARNING")
    return None

def test_multi_python_installation(install_root, successful_builds):
    """Test PySide6 installation for each successful Python version"""
    smart_log("🧪 Testing PySide6 installation for each Python version...")
    
    for python_version, site_packages in successful_builds:
        try:
            python_exe = find_rez_python_version(python_version)
            if python_exe:
                smart_log(f"🧪 Testing Python {python_version}...")
                
                test_env = os.environ.copy()
                test_env["PYTHONPATH"] = f"{site_packages}:{test_env.get('PYTHONPATH', '')}"
                
                # Test basic import
                test_cmd = [python_exe, "-c", "import PySide6; print(f'PySide6 {PySide6.__version__} imported successfully')"]
                result = subprocess.run(test_cmd, env=test_env, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    smart_log(f"✅ Python {python_version}: {result.stdout.strip()}")
                else:
                    smart_log(f"❌ Python {python_version} test failed: {result.stderr}", "ERROR")
        except Exception as e:
            smart_log(f"❌ Python {python_version} test error: {e}", "ERROR")

def build(source_path, build_path, install_path, targets):
    """Main build function - now uses multi-Python approach by default"""
    return build_multi_python(source_path, build_path, install_path, targets)

def verify_installation(install_root):
    """Verify the final PySide6 installation"""
    smart_log("🔍 Verifying PySide6 installation...")
    
    if not os.path.exists(install_root):
        smart_log(f"❌ Installation directory not found: {install_root}")
        return False
    
    # Check for required tools from package.py
    bin_dir = os.path.join(install_root, "bin")
    required_tools = [
        "pyside6-uic", "pyside6-rcc", "pyside6-designer", "pyside6-assistant",
        "pyside6-linguist", "pyside6-lupdate", "pyside6-lrelease",
        "pyside6-qml", "pyside6-deploy", "shiboken6"
    ]
    
    missing_tools = []
    if os.path.exists(bin_dir):
        for tool in required_tools:
            tool_path = os.path.join(bin_dir, tool)
            if not os.path.exists(tool_path):
                missing_tools.append(tool)
    else:
        smart_log(f"⚠️  Bin directory not found: {bin_dir}")
        missing_tools = required_tools
    
    if missing_tools:
        smart_log(f"⚠️  Missing tools ({len(missing_tools)}/{len(required_tools)}): {missing_tools[:5]}...")
        return False
    else:
        smart_log(f"✅ All {len(required_tools)} required tools are present")
    
    # Test basic import
    try:
        test_script = os.path.join(install_root, "test_pyside6.py")
        if os.path.exists(test_script):
            result = subprocess.run(
                ["python3", test_script],
                cwd=install_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                smart_log("✅ PySide6 import test passed")
                return True
            else:
                smart_log(f"❌ PySide6 import test failed: {result.stderr}")
                return False
        else:
            smart_log("⚠️  Test script not found, skipping import test")
            return True  # Still consider successful if tools are present
    except Exception as e:
        smart_log(f"❌ Import test error: {e}")
        return False

if __name__ == "__main__":
    build(
        source_path  = os.environ["REZ_BUILD_SOURCE_PATH"],
        build_path   = os.environ["REZ_BUILD_PATH"],
        install_path = os.environ["REZ_BUILD_INSTALL_PATH"],
        targets      = sys.argv[1:]
    )
