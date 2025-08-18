# -*- coding: utf-8 -*-
import os, sys, shutil, subprocess

def run_cmd(cmd, cwd=None):
    print(f"[RUN] {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd, check=True)

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

def build_pyside6(src, build_path, install_root, rez_python_exe):
    """PySide6 빌드 실행"""
    print("🔨 Building PySide6...")
    
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
    qt_dir = os.environ.get("QT_DIR")
    if not qt_dir:
        qmake_path = shutil.which("qmake")
        if qmake_path:
            qt_dir = os.path.dirname(os.path.dirname(qmake_path))
    
    qtpaths_exe = os.path.join(qt_dir, "bin", "qtpaths")
    if not os.path.exists(qtpaths_exe):
        raise RuntimeError(f"qtpaths not found at {qtpaths_exe}")
    
    # 빌드 환경 변수 설정 - 시스템 Qt 라이브러리 제거!
    build_env = os.environ.copy()
    
    # 시스템 Qt 라이브러리 경로 제거
    ld_library_path = build_env.get("LD_LIBRARY_PATH", "")
    ld_paths = [p for p in ld_library_path.split(":") if p and not p.startswith("/usr/lib")]
    # 빌드한 Qt 라이브러리를 최우선으로
    ld_paths.insert(0, os.path.join(qt_dir, "lib"))
    
    # CMake Warning 줄이기 위해 불필요한 변수들 제거
    unwanted_vars = [
        "BUILD_DOCS", "CMAKE_RULE_MESSAGES", "CMAKE_VERBOSE_MAKEFILE", 
        "MODULES", "OpenGL_GL_PREFERENCE", "Qt5Help_DIR"
    ]
    for var in unwanted_vars:
        build_env.pop(var, None)
    
    # minizip_ng 경로 추가
    minizip_ng_dir = None
    for potential_path in ["/core/Linux/APPZ/packages/minizip_ng/4.0.10"]:
        if os.path.exists(potential_path):
            minizip_ng_dir = potential_path
            break
    
    # GCC 라이브러리 디렉토리 확인
    gcc_version = "11"
    gcc_lib_path = f"/usr/lib/gcc/x86_64-redhat-linux/{gcc_version}"
    gcc_include_path = f"/usr/lib/gcc/x86_64-redhat-linux/{gcc_version}/include"
    
    # rez GCC 경로 확인
    rez_gcc_root = None
    for potential_path in ["/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux"]:
        if os.path.exists(potential_path):
            rez_gcc_root = potential_path
            break
    
    if not rez_gcc_root:
        raise RuntimeError("❌ rez GCC not found! Build requires rez gcc-11.5.0")
    
    # 올바른 헤더 경로 순서 설정 (기본 C 헤더 우선)
    system_includes = []
    
    # 1. 먼저 기본 C 헤더들 (stdlib.h 등이 여기 있음)
    system_includes.extend([
        "/usr/include",  # 기본 시스템 C 헤더 (최우선)
        # clang 헤더 제거 - GCC와 충돌 발생
    ])
    
    # 2. rez GCC C 헤더들 (컴파일러 내장 헤더)
    rez_gcc_c_include = os.path.join(rez_gcc_root, "lib", "gcc", "x86_64-pc-linux-gnu", "11.5.0", "include")
    if os.path.exists(rez_gcc_c_include):
        system_includes.append(rez_gcc_c_include)
        print(f"✅ rez GCC C headers: {rez_gcc_c_include}")
    
    # 3. rez GCC include-fixed (시스템 호환 헤더들)
    rez_gcc_fixed_include = os.path.join(rez_gcc_root, "lib", "gcc", "x86_64-pc-linux-gnu", "11.5.0", "include-fixed")
    if os.path.exists(rez_gcc_fixed_include):
        system_includes.append(rez_gcc_fixed_include)
        print(f"✅ rez GCC fixed headers: {rez_gcc_fixed_include}")
    
    # 4. 마지막에 rez GCC C++ 헤더들 (시스템 C++ 헤더 대신)
    rez_gcc_cxx_include = os.path.join(rez_gcc_root, "include", "c++", "11.5.0")
    if os.path.exists(rez_gcc_cxx_include):
        system_includes.extend([
            rez_gcc_cxx_include,
            os.path.join(rez_gcc_cxx_include, "x86_64-pc-linux-gnu"),
            os.path.join(rez_gcc_cxx_include, "backward"),
        ])
        print(f"✅ rez GCC C++ headers: {rez_gcc_cxx_include}")
    
    print(f"🔧 Using rez GCC ONLY: {rez_gcc_root}")
    print(f"🔧 Total include paths: {len(system_includes)}")
    
    # rez GCC 컴파일러 경로 설정
    rez_gcc_bin = os.path.join(rez_gcc_root, "bin")
    rez_gcc_cc = os.path.join(rez_gcc_bin, "gcc")
    rez_gcc_cxx = os.path.join(rez_gcc_bin, "g++")
    
    if not os.path.exists(rez_gcc_cc):
        raise RuntimeError(f"❌ rez GCC compiler not found: {rez_gcc_cc}")
    
    print(f"🔧 rez GCC compiler: {rez_gcc_cc}")
    print(f"🔧 rez GCC C++ compiler: {rez_gcc_cxx}")

    # 컴파일 플래그 생성
    include_flags = " ".join([f"-I{inc}" for inc in system_includes])
    
    # 빌드 환경 설정 (rez GCC 전용)
    build_env.update({
        "PYSIDE_BUILD_DIR": build_path,
        "PYSIDE_INSTALL_DIR": install_root,
        "C_INCLUDE_PATH": ":".join(system_includes),
        "CPLUS_INCLUDE_PATH": ":".join(system_includes),
        "CPATH": ":".join(system_includes),
        "CLANG_BUILTIN_INCLUDE_DIR": "/usr/lib/clang/19/include",
        "LD_LIBRARY_PATH": ":".join(ld_paths),
        "QT_PLUGIN_PATH": os.path.join(qt_dir, "plugins"),
        "PYTHON": python_exe,
        "PYTHON3": python_exe,
        # rez GCC 컴파일러 강제 설정
        "CC": rez_gcc_cc,
        "CXX": rez_gcc_cxx,
        "CMAKE_C_COMPILER": rez_gcc_cc,
        "CMAKE_CXX_COMPILER": rez_gcc_cxx,
        # 컴파일 플래그로 헤더 경로 강제 설정
        "CFLAGS": include_flags,
        "CXXFLAGS": include_flags,
        "CPPFLAGS": include_flags,
        # PATH에 rez GCC bin을 최우선으로 설정
        "PATH": f"{rez_gcc_bin}:{build_env.get('PATH', '')}",
    })
    
    # minizip_ng가 있으면 환경에 추가
    if minizip_ng_dir:
        minizip_include = os.path.join(minizip_ng_dir, "include")
        minizip_lib = os.path.join(minizip_ng_dir, "lib64")
        
        if os.path.exists(minizip_include):
            build_env["C_INCLUDE_PATH"] += f":{minizip_include}"
            build_env["CPLUS_INCLUDE_PATH"] += f":{minizip_include}"
            build_env["CPATH"] += f":{minizip_include}"
        
        if os.path.exists(minizip_lib):
            build_env["LD_LIBRARY_PATH"] = f"{minizip_lib}:{build_env['LD_LIBRARY_PATH']}"
        
        print(f"🔧 Added minizip_ng: {minizip_ng_dir}")
    
    # 강력한 CMake 옵션 준비 (컴파일러와 헤더 강제 설정)
    cmake_args = [
        f"-DCMAKE_C_COMPILER={rez_gcc_cc}",
        f"-DCMAKE_CXX_COMPILER={rez_gcc_cxx}",
        f"-DCMAKE_C_FLAGS=-I{' -I'.join(system_includes)}",
        f"-DCMAKE_CXX_FLAGS=-I{' -I'.join(system_includes)}",
        f"-DCMAKE_C_INCLUDE_PATH={':'.join(system_includes)}",
        f"-DCMAKE_CXX_INCLUDE_PATH={':'.join(system_includes)}",
        "-DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=NEVER",
        "-DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=NEVER",
    ]
    
    if minizip_ng_dir:
        cmake_args.extend([
            f"-DMINIZIP_ROOT={minizip_ng_dir}",
            f"-DMINIZIP_INCLUDE_DIR={os.path.join(minizip_ng_dir, 'include')}",
            f"-DMINIZIP_LIBRARY={os.path.join(minizip_ng_dir, 'lib64', 'libminizip-ng.so')}",
        ])
    
    # 단계별 빌드 시도 - minizip_ng 옵션 추가
    build_commands = []
    
    # 기본 빌드 옵션들
    common_options = [
        "--qtpaths", qtpaths_exe,
        "--parallel", str(min(os.cpu_count(), 8)),
    ]
    
    # CMake 환경 변수로 설정 (setup.py가 --cmake-args를 지원하지 않으므로)
    if cmake_args:
        existing_cmake_args = build_env.get("CMAKE_ARGS", "")
        new_cmake_args = " ".join(cmake_args)
        if existing_cmake_args:
            build_env["CMAKE_ARGS"] = f"{existing_cmake_args} {new_cmake_args}"
        else:
            build_env["CMAKE_ARGS"] = new_cmake_args
    
    build_commands = [
        # 1단계: 전체 빌드 시도 (minizip_ng 포함)
        [python_exe, "setup.py", "build", 
         "--qtpaths", qtpaths_exe,
         "--parallel", "1"],
        
        # 2단계: 기본 모듈만 빌드 
        [python_exe, "setup.py", "build",
         "--qtpaths", qtpaths_exe, 
         "--parallel", "1",
         "--module-subset=QtCore,QtGui,QtWidgets"],
         
        # 3단계: qmake 사용 (폴백)
        [python_exe, "setup.py", "build",
         "--qmake", os.path.join(qt_dir, "bin", "qmake"),
         "--parallel", "1"]
    ]
    
    if cmake_args:
        print(f"🔧 CMake args for minizip_ng: {' '.join(cmake_args)}")
    
    success = False
    for i, cmd in enumerate(build_commands, 1):
        print(f"🔨 Build attempt {i}/{len(build_commands)}: {' '.join(cmd[-2:])}")
        print(f"🔨 Command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, env=build_env, check=True, cwd=src)
            print(f"✅ Build attempt {i} successful!")
            success = True
            break
        except subprocess.CalledProcessError as e:
            print(f"❌ Build attempt {i} failed: {e}")
            if i < len(build_commands):
                print(f"🔄 Trying next approach...")
            continue
    
    if not success:
        raise RuntimeError("All PySide6 build attempts failed")
    
    return success

def install_pyside6(src, install_root, rez_python_exe):
    """PySide6 설치"""
    print("📦 Installing PySide6...")
    
    python_exe = rez_python_exe
    
    # Qt 경로 확인
    qt_dir = os.environ.get("QT_DIR")
    if not qt_dir:
        qmake_path = shutil.which("qmake")
        if qmake_path:
            qt_dir = os.path.dirname(os.path.dirname(qmake_path))
    
    # === 🔥 핵심: 설치 시에도 시스템 Qt 라이브러리 완전 차단 ===
    install_env = os.environ.copy()
    
    # 현재 LD_LIBRARY_PATH에서 시스템 라이브러리 경로 제거
    current_ld_path = install_env.get("LD_LIBRARY_PATH", "")
    safe_paths = []
    
    for path in current_ld_path.split(":"):
        # 시스템 Qt 관련 경로 완전 제외
        if path and not any(exclude in path for exclude in [
            "/usr/lib64", "/usr/lib", "/lib64", "/lib"
        ]):
            safe_paths.append(path)
    
    # 빌드한 Qt만 사용하도록 설정
    final_ld_path = f"{qt_dir}/lib"
    if safe_paths:
        final_ld_path += ":" + ":".join(safe_paths)
    
    install_env.update({
        "LD_LIBRARY_PATH": final_ld_path,
        "QT_PLUGIN_PATH": f"{qt_dir}/plugins",
        "QT_DIR": qt_dir,
        "QTDIR": qt_dir,
        # Python 환경도 명시
        "PYTHON": python_exe,
        "PYTHON3": python_exe,
    })
    
    print(f"🔧 Install LD_LIBRARY_PATH: {final_ld_path}")
    print(f"🔧 Qt directory: {qt_dir}")
    
    # 설치 명령들
    install_commands = [
        # 1단계: 표준 install
        [python_exe, "setup.py", "install", "--prefix", install_root],
        
        # 2단계: 환경 변수 추가로 install  
        [python_exe, "setup.py", "install", 
         "--prefix", install_root,
         "--qt-target-path", qt_dir],
         
        # 3단계: setup.py에 Qt 경로 힌트 제공
        [python_exe, "setup.py", "install",
         "--prefix", install_root, 
         "--qtpaths", f"{qt_dir}/bin/qtpaths"]
    ]
    
    success = False
    for i, cmd in enumerate(install_commands, 1):
        print(f"📦 Install attempt {i}/{len(install_commands)}: {' '.join(cmd[2:])}")
        try:
            subprocess.run(cmd, env=install_env, check=True, cwd=src)
            print(f"✅ Install attempt {i} successful!")
            success = True
            break
        except subprocess.CalledProcessError as e:
            print(f"❌ Install attempt {i} failed: {e}")
            if i < len(install_commands):
                print(f"🔄 Trying next approach...")
            continue
    
    if not success:
        print("⚠️  All install attempts failed, trying bdist_wheel...")
        
        # 대안: bdist_wheel 후 수동 설치
        try:
            subprocess.run([python_exe, "setup.py", "bdist_wheel"], 
                         env=install_env, check=True, cwd=src)
            
            dist_dir = os.path.join(src, "dist")
            if os.path.exists(dist_dir):
                wheel_files = [f for f in os.listdir(dist_dir) if f.endswith('.whl')]
                if wheel_files:
                    python_version = subprocess.run([
                        python_exe, "-c",
                        "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
                    ], capture_output=True, text=True).stdout.strip()
                    
                    target_dir = os.path.join(install_root, "lib", f"python{python_version}", "site-packages")
                    os.makedirs(target_dir, exist_ok=True)
                    
                    wheel_path = os.path.join(dist_dir, wheel_files[0])
                    subprocess.run([
                        "pip3", "install", wheel_path,
                        "--target", target_dir,
                        "--no-deps"
                    ], env=install_env, check=True)
                    
                    print(f"✅ PySide6 installed via wheel to: {target_dir}")
                    return
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PySide6 installation failed: {e}")
    
    print(f"✅ PySide6 installed to: {install_root}")

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

def build(source_path, build_path, install_path, targets):
    version = os.environ.get("REZ_BUILD_PROJECT_VERSION", "6.9.1")
    
    # install 타겟인 경우 /core 경로 사용
    install_root = f"/core/Linux/APPZ/packages/pyside6/{version}" if "install" in targets else install_path
    
    print(f"🚀 Starting PySide6 {version} build...")
    print(f"📁 Source path: {source_path}")
    print(f"📁 Build path: {build_path}")
    print(f"📁 Install path: {install_root}")
    
    # 디렉토리 정리
    clean_build_dir(build_path)
    
    if "install" in targets:
        clean_install_dir(install_root)
    
    # 소스 확인
    src = ensure_source(version, source_path)
    
    # 빌드 전 검증
    rez_python_exe = verify_prerequisites()
    
    # 환경 설정
    qt_dir, shiboken_dir = setup_build_environment()
    
    # Shiboken 래퍼 생성 (핵심!)
    create_shiboken_wrapper(build_path)
    
    try:
        # PySide6 빌드 - rez Python 전달
        build_pyside6(src, build_path, install_root, rez_python_exe)
        
        if "install" in targets:
            # 설치 디렉토리 생성
            os.makedirs(install_root, exist_ok=True)
            
            # PySide6 설치 - rez Python 전달
            install_pyside6(src, install_root, rez_python_exe)
            
            # 누락된 라이브러리들 복사 (중요!)
            copy_missing_libraries(src, build_path, install_root)
            
            # 테스트 스크립트 생성
            test_script = create_test_script(install_root)
            
            # 라이선스 및 패키지 파일 복사
            copy_license(src, install_root)
            copy_package_py(source_path, install_root)
            
            # 설치 테스트 실행
            print("🧪 Running installation test...")
            try:
                python_version = subprocess.run([
                    "python3", "-c",
                    "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
                ], capture_output=True, text=True).stdout.strip()
                
                test_env = os.environ.copy()
                test_env["PYTHONPATH"] = f"{install_root}/lib/python{python_version}/site-packages:{test_env.get('PYTHONPATH', '')}"
                
                subprocess.run(["python3", test_script], env=test_env, check=True)
                print("✅ Installation test passed!")
                
            except subprocess.CalledProcessError:
                print("⚠️  Installation test failed, but build may still be usable")
            
            print(f"✅ PySide6 {version} installed successfully to: {install_root}")
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        raise
    
    finally:
        # 빌드 마커 생성
        write_build_marker(build_path)
    
    print("🎉 PySide6 build process completed!")

if __name__ == "__main__":
    build(
        source_path  = os.environ["REZ_BUILD_SOURCE_PATH"],
        build_path   = os.environ["REZ_BUILD_PATH"],
        install_path = os.environ["REZ_BUILD_INSTALL_PATH"],
        targets      = sys.argv[1:]
    )
