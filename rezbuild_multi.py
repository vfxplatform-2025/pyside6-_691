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

def install_python_dependencies(python_exe):
    """Python 빌드 의존성 설치"""
    print(f"📦 Installing Python dependencies...")
    
    required_packages = [
        "packaging",
        "wheel", 
        "setuptools"
    ]
    
    for package in required_packages:
        try:
            # 패키지가 이미 설치되어 있는지 확인
            result = subprocess.run([python_exe, "-c", f"import {package}"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {package} already installed")
                continue
        except:
            pass
        
        # 패키지 설치
        print(f"📦 Installing {package}...")
        try:
            subprocess.run([python_exe, "-m", "pip", "install", package], 
                          capture_output=True, text=True, check=True)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Failed to install {package}: {e}")
            # packaging은 필수이므로 실패시 에러
            if package == "packaging":
                raise RuntimeError(f"Failed to install required package: {package}")

def verify_prerequisites(python_version):
    """빌드 전 필수 구성 요소 확인 - 특정 Python 버전용"""
    print(f"🔍 Verifying build prerequisites for Python {python_version}...")
    
    # 특정 Python 버전 경로
    python_major_minor = ".".join(python_version.split(".")[:2])
    python_exe_paths = [
        f"/core/Linux/APPZ/packages/python/{python_version}/bin/python3",
        f"/core/Linux/APPZ/packages/python/{python_version}/bin/python"
    ]
    
    python_exe = None
    for path in python_exe_paths:
        if os.path.exists(path):
            python_exe = path
            break
    
    if not python_exe:
        raise RuntimeError(f"Python {python_version} not found. Expected paths: {python_exe_paths}")
    
    print(f"✅ Using Python: {python_exe}")
    
    # Python 버전 확인
    result = subprocess.run([python_exe, "--version"], capture_output=True, text=True)
    actual_version = result.stdout.strip()
    print(f"✅ Python version: {actual_version}")
    
    # PATH에 해당 Python 추가
    python_bin_dir = os.path.dirname(python_exe)
    current_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{python_bin_dir}:{current_path}"
    
    # Python 의존성 설치
    install_python_dependencies(python_exe)
    
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
    
    return python_exe, python_major_minor

def build_pyside6(python_version):
    """특정 Python 버전용 PySide6 빌드"""
    print(f"🛠️  Building PySide6 for Python {python_version}")
    
    # 환경 변수에서 경로 가져오기
    source_path = os.environ.get("REZ_BUILD_SOURCE_PATH", os.getcwd())
    build_path = os.environ.get("REZ_BUILD_PATH", os.path.join(source_path, "build"))
    install_path = os.environ.get("REZ_BUILD_INSTALL_PATH", "/core/Linux/APPZ/packages/pyside6/6.9.1")
    
    print(f"📁 Source path: {source_path}")
    print(f"📁 Build path: {build_path}")
    print(f"📁 Install path: {install_path}")
    
    # Python 검증 및 설정
    python_exe, python_major_minor = verify_prerequisites(python_version)
    
    # 소스 확인
    source_dir = ensure_source("6.9.1", source_path)
    
    # 빌드 디렉토리 정리
    clean_build_dir(build_path)
    os.makedirs(build_path, exist_ok=True)
    
    # Python 버전별 설치 경로
    python_install_path = os.path.join(install_path, "lib", f"python{python_major_minor}", "site-packages")
    
    # 환경 변수 설정
    env = os.environ.copy()
    
    # rez GCC 경로
    rez_gcc_root = "/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux"
    
    # 올바른 헤더 경로 순서 설정 (기본 C 헤더 우선)
    system_includes = []
    system_includes.extend([
        "/usr/include",  # 기본 시스템 C 헤더 (최우선)
    ])
    
    # rez GCC C 헤더들 (컴파일러 내장 헤더)
    rez_gcc_c_include = os.path.join(rez_gcc_root, "lib", "gcc", "x86_64-pc-linux-gnu", "11.5.0", "include")
    if os.path.exists(rez_gcc_c_include):
        system_includes.append(rez_gcc_c_include)
    
    # C++ 표준 라이브러리 헤더 (rez GCC 것만 사용)
    rez_gcc_cpp_include = os.path.join(rez_gcc_root, "include", "c++", "11")
    if os.path.exists(rez_gcc_cpp_include):
        system_includes.append(rez_gcc_cpp_include)
        system_includes.append(os.path.join(rez_gcc_cpp_include, "x86_64-pc-linux-gnu"))
    
    # 의존성 라이브러리 헤더들
    dependency_includes = [
        "/core/Linux/APPZ/packages/qt/6.9.1/include",
        "/core/Linux/APPZ/packages/shiboken6/6.9.1/include",
        "/core/Linux/APPZ/packages/numpy/1.26.4/lib/python3.13/site-packages/numpy/core/include",
        "/core/Linux/APPZ/packages/minizip_ng/4.0.10/include"
    ]
    
    all_includes = system_includes + dependency_includes
    cplus_include_path = ":".join(all_includes)
    
    # 컴파일러 환경 변수 설정
    env.update({
        "CC": f"{rez_gcc_root}/bin/gcc",
        "CXX": f"{rez_gcc_root}/bin/g++",
        "CPLUS_INCLUDE_PATH": cplus_include_path,
        "C_INCLUDE_PATH": ":".join(system_includes[:2]),  # 기본 C 헤더만
        "LD_LIBRARY_PATH": ":".join([
            "/core/Linux/APPZ/packages/qt/6.9.1/lib",
            "/core/Linux/APPZ/packages/shiboken6/6.9.1/lib",
            "/core/Linux/APPZ/packages/gcc/11.5.0/platform_linux/lib64",
            "/core/Linux/APPZ/packages/minizip_ng/4.0.10/lib",
            env.get("LD_LIBRARY_PATH", "")
        ]),
        "PKG_CONFIG_PATH": ":".join([
            "/core/Linux/APPZ/packages/qt/6.9.1/lib/pkgconfig",
            "/core/Linux/APPZ/packages/shiboken6/6.9.1/lib/pkgconfig"
        ]),
        "PYTHONPATH": python_install_path,
        "PYTHON_EXECUTABLE": python_exe,
    })
    
    print(f"🐍 Using Python executable: {python_exe}")
    print(f"📦 Python install path: {python_install_path}")
    
    # 빌드 명령어 구성 - Python별 빌드
    build_cmd = [
        python_exe, "setup.py", "build",
        f"--build-base={build_path}",
        "--parallel=4",
        "--verbose-build",
        "--standalone",
        "--ignore-git",
        "--cmake-args="
        f"-DCMAKE_PREFIX_PATH=/core/Linux/APPZ/packages/qt/6.9.1:/core/Linux/APPZ/packages/shiboken6/6.9.1 "
        f"-DCMAKE_INSTALL_PREFIX={install_path} "
        f"-DLLVM_INSTALL_DIR=/usr "
        f"-DPython_EXECUTABLE={python_exe} "
        f"-DPYTHON_EXECUTABLE={python_exe} "
        f"-DSHIBOKEN_PYTHON_INTERPRETER={python_exe} "
        f"-DPYSIDE_PYTHON_INTERPRETER={python_exe} "
        f"-DMINIZIP_INCLUDE_DIR=/core/Linux/APPZ/packages/minizip_ng/4.0.10/include "
        f"-DMINIZIP_LIBRARIES=/core/Linux/APPZ/packages/minizip_ng/4.0.10/lib/libminizip.so "
        f"-DCMAKE_BUILD_TYPE=Release "
        f"-DBUILD_TESTS=OFF "
        f"-DUSE_PYTHON_VERSION={python_major_minor}"
    ]
    
    print(f"🔧 Build command: {' '.join(build_cmd)}")
    
    # 빌드 실행
    subprocess.run(build_cmd, cwd=source_dir, env=env, check=True)
    
    # 설치 명령어
    install_cmd = [
        python_exe, "setup.py", "install",
        f"--build-base={build_path}",
        f"--prefix={install_path}",
        f"--install-platlib={python_install_path}",
        f"--install-purelib={python_install_path}",
        "--force"
    ]
    
    print(f"📦 Install command: {' '.join(install_cmd)}")
    
    # 설치 실행
    subprocess.run(install_cmd, cwd=source_dir, env=env, check=True)
    
    print(f"✅ PySide6 successfully built and installed for Python {python_version}")
    return python_install_path

def copy_missing_libraries(install_path):
    """누락된 라이브러리 파일들 복사"""
    print("🔗 Copying missing PySide6 libraries...")
    
    lib_dir = os.path.join(install_path, "lib")
    os.makedirs(lib_dir, exist_ok=True)
    
    # 복사해야 할 라이브러리 목록
    required_libs = [
        "libpyside6.abi3.so",
        "libpyside6.abi3.so.6.9", 
        "libpyside6.abi3.so.6.9.1",
        "libpyside6qml.abi3.so",
        "libpyside6qml.abi3.so.6.9",
        "libpyside6qml.abi3.so.6.9.1",
        "libshiboken6.abi3.so",
        "libshiboken6.abi3.so.6.9", 
        "libshiboken6.abi3.so.6.9.1"
    ]
    
    # 소스 경로들 (빌드 결과에서 찾기)
    source_locations = [
        "/core/Linux/APPZ/packages/shiboken6/6.9.1/lib",
        os.path.join(install_path, "lib")
    ]
    
    for lib_name in required_libs:
        target_path = os.path.join(lib_dir, lib_name)
        
        if os.path.exists(target_path):
            print(f"✅ {lib_name} already exists")
            continue
            
        # 소스 찾기
        for source_dir in source_locations:
            source_path = os.path.join(source_dir, lib_name)
            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)
                print(f"📋 Copied {lib_name}")
                break
        else:
            print(f"⚠️  Warning: {lib_name} not found in any source location")

def main():
    if len(sys.argv) < 3:
        print("Usage: python rezbuild_multi.py install <python_version>")
        print("Example: python rezbuild_multi.py install 3.9.21")
        sys.exit(1)
    
    command = sys.argv[1]
    python_version = sys.argv[2]
    
    if command != "install":
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    try:
        install_path = os.environ.get("REZ_BUILD_INSTALL_PATH", "/core/Linux/APPZ/packages/pyside6/6.9.1")
        
        print(f"🚀 Starting PySide6 multi-Python build for version {python_version}")
        
        # Python 버전별 빌드 및 설치
        python_site_packages = build_pyside6(python_version)
        
        # 누락된 라이브러리 복사
        copy_missing_libraries(install_path)
        
        print(f"🎉 PySide6 build completed successfully for Python {python_version}")
        print(f"📦 Installed to: {python_site_packages}")
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()