#!/usr/bin/env python3
"""
PySide6 Directory Structure Setup
_pyside6 스타일의 완전한 디렉토리 구조를 생성하는 도구
"""

import os
import shutil
from pathlib import Path

# 기본 경로 설정
PYSIDE6_ROOT = "/core/Linux/APPZ/packages/pyside6/6.9.1"
PYTHON3_13_SITE_PACKAGES = f"{PYSIDE6_ROOT}/lib/python3.13/site-packages"

def create_include_structure():
    """include 디렉토리 구조 생성"""
    print("🔧 Creating include directory structure...")
    
    include_dir = f"{PYSIDE6_ROOT}/include"
    os.makedirs(include_dir, exist_ok=True)
    
    # PySide6 헤더 파일들 복사
    pyside6_include_src = f"{PYTHON3_13_SITE_PACKAGES}/PySide6/include"
    pyside6_include_dst = f"{include_dir}/PySide6"
    
    if os.path.exists(pyside6_include_src):
        if os.path.exists(pyside6_include_dst):
            shutil.rmtree(pyside6_include_dst)
        shutil.copytree(pyside6_include_src, pyside6_include_dst)
        print(f"✅ Copied PySide6 headers to {pyside6_include_dst}")
    else:
        print(f"⚠️  PySide6 headers not found at {pyside6_include_src}")
    
    # Shiboken6 헤더 파일들 복사 (만약 있다면)
    shiboken6_include_src = f"{PYTHON3_13_SITE_PACKAGES}/shiboken6"
    shiboken6_include_dst = f"{include_dir}/shiboken6"
    
    # shiboken6에서 헤더 파일들 찾기
    shiboken_headers = []
    if os.path.exists(shiboken6_include_src):
        for item in os.listdir(shiboken6_include_src):
            if item.endswith('.h'):
                shiboken_headers.append(item)
    
    if shiboken_headers:
        os.makedirs(shiboken6_include_dst, exist_ok=True)
        for header in shiboken_headers:
            src_path = f"{shiboken6_include_src}/{header}"
            dst_path = f"{shiboken6_include_dst}/{header}"
            shutil.copy2(src_path, dst_path)
        print(f"✅ Copied {len(shiboken_headers)} Shiboken6 headers to {shiboken6_include_dst}")
    else:
        print(f"⚠️  No Shiboken6 headers found")

def create_lib_structure():
    """lib 디렉토리 구조 생성"""
    print("\n🔧 Creating lib directory structure...")
    
    lib_dir = f"{PYSIDE6_ROOT}/lib"
    
    # CMake 설정 파일들 복사
    cmake_src_dirs = [
        f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/lib/cmake",
        f"{PYTHON3_13_SITE_PACKAGES}/shiboken6",  # cmake 파일이 있을 수 있음
    ]
    
    cmake_dst = f"{lib_dir}/cmake"
    os.makedirs(cmake_dst, exist_ok=True)
    
    # 실제 cmake 파일들을 찾아서 복사
    found_cmake = False
    
    # PySide6/Qt/lib/cmake에서 찾기
    qt_cmake_src = f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/lib/cmake"
    if os.path.exists(qt_cmake_src):
        for item in os.listdir(qt_cmake_src):
            src_path = os.path.join(qt_cmake_src, item)
            dst_path = os.path.join(cmake_dst, item)
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
                print(f"✅ Copied CMake config: {item}")
                found_cmake = True
    
    if not found_cmake:
        print("⚠️  No CMake configurations found")
    
    # 공유 라이브러리들 복사
    lib_files = []
    
    # PySide6 라이브러리들
    pyside6_lib_src = f"{PYTHON3_13_SITE_PACKAGES}/PySide6"
    if os.path.exists(pyside6_lib_src):
        for item in os.listdir(pyside6_lib_src):
            if item.startswith('lib') and (item.endswith('.so') or item.endswith('.so.6.9')):
                lib_files.append((os.path.join(pyside6_lib_src, item), os.path.join(lib_dir, item)))
    
    # Shiboken6 라이브러리들
    shiboken6_lib_src = f"{PYTHON3_13_SITE_PACKAGES}/shiboken6"
    if os.path.exists(shiboken6_lib_src):
        for item in os.listdir(shiboken6_lib_src):
            if item.startswith('lib') and (item.endswith('.so') or item.endswith('.so.6.9')):
                lib_files.append((os.path.join(shiboken6_lib_src, item), os.path.join(lib_dir, item)))
    
    # 라이브러리 파일들 복사
    for src_path, dst_path in lib_files:
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            print(f"✅ Copied library: {os.path.basename(dst_path)}")
    
    # pkgconfig 디렉토리 생성 (필요한 경우)
    pkgconfig_dir = f"{lib_dir}/pkgconfig"
    os.makedirs(pkgconfig_dir, exist_ok=True)
    
    # pkgconfig 파일들 생성 (기본적인 것들)
    pyside6_pc_content = f"""prefix={PYSIDE6_ROOT}
exec_prefix=${{prefix}}
libdir=${{prefix}}/lib
includedir=${{prefix}}/include

Name: PySide6
Description: Python bindings for Qt6
Version: 6.9.1
Requires: Qt6Core Qt6Gui Qt6Widgets
Libs: -L${{libdir}} -lpyside6
Cflags: -I${{includedir}}
"""
    
    with open(f"{pkgconfig_dir}/pyside6.pc", 'w') as f:
        f.write(pyside6_pc_content)
    
    shiboken6_pc_content = f"""prefix={PYSIDE6_ROOT}
exec_prefix=${{prefix}}
libdir=${{prefix}}/lib
includedir=${{prefix}}/include

Name: Shiboken6
Description: CPython bindings generator for Qt6
Version: 6.9.1
Libs: -L${{libdir}} -lshiboken6
Cflags: -I${{includedir}}/shiboken6
"""
    
    with open(f"{pkgconfig_dir}/shiboken6.pc", 'w') as f:
        f.write(shiboken6_pc_content)
    
    print(f"✅ Created pkgconfig files")

def create_plugins_structure():
    """plugins 디렉토리 구조 생성"""
    print("\n🔧 Creating plugins directory structure...")
    
    plugins_dir = f"{PYSIDE6_ROOT}/plugins"
    designer_dir = f"{plugins_dir}/designer"
    os.makedirs(designer_dir, exist_ok=True)
    
    # Qt Designer 플러그인 찾기
    possible_plugin_paths = [
        f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/plugins/designer",
        f"{PYTHON3_13_SITE_PACKAGES}/PySide6/plugins/designer",
        f"{PYTHON3_13_SITE_PACKAGES}/PySide6",  # 플러그인이 여기에 있을 수도
    ]
    
    plugin_found = False
    for src_path in possible_plugin_paths:
        if os.path.exists(src_path):
            if os.path.isdir(src_path):
                # 디렉토리인 경우 안의 .so 파일들 복사
                for item in os.listdir(src_path):
                    if item.endswith('.so') and 'plugin' in item.lower():
                        shutil.copy2(os.path.join(src_path, item), os.path.join(designer_dir, item))
                        print(f"✅ Copied plugin: {item}")
                        plugin_found = True
            elif src_path.endswith('.so') and 'plugin' in src_path.lower():
                # 파일인 경우 직접 복사
                shutil.copy2(src_path, designer_dir)
                print(f"✅ Copied plugin: {os.path.basename(src_path)}")
                plugin_found = True
    
    if not plugin_found:
        print("⚠️  No Qt Designer plugins found")

def create_share_structure():
    """share 디렉토리 구조 생성"""
    print("\n🔧 Creating share directory structure...")
    
    share_dir = f"{PYSIDE6_ROOT}/share"
    pyside6_share_dir = f"{share_dir}/PySide6"
    os.makedirs(pyside6_share_dir, exist_ok=True)
    
    # 문서 파일들 복사
    doc_src = f"{PYTHON3_13_SITE_PACKAGES}/PySide6/doc"
    doc_dst = f"{pyside6_share_dir}/doc"
    
    if os.path.exists(doc_src):
        if os.path.exists(doc_dst):
            shutil.rmtree(doc_dst)
        shutil.copytree(doc_src, doc_dst)
        print(f"✅ Copied documentation to {doc_dst}")
    else:
        print(f"⚠️  Documentation not found at {doc_src}")
    
    # glue 파일들 복사
    glue_src = f"{PYTHON3_13_SITE_PACKAGES}/PySide6/glue"
    glue_dst = f"{pyside6_share_dir}/glue"
    
    if os.path.exists(glue_src):
        if os.path.exists(glue_dst):
            shutil.rmtree(glue_dst)
        shutil.copytree(glue_src, glue_dst)
        print(f"✅ Copied glue files to {glue_dst}")
    else:
        print(f"⚠️  Glue files not found at {glue_src}")
    
    # typesystems 파일들 복사
    typesystems_src = f"{PYTHON3_13_SITE_PACKAGES}/PySide6/typesystems"
    typesystems_dst = f"{pyside6_share_dir}/typesystems"
    
    if os.path.exists(typesystems_src):
        if os.path.exists(typesystems_dst):
            shutil.rmtree(typesystems_dst)
        shutil.copytree(typesystems_src, typesystems_dst)
        print(f"✅ Copied typesystems to {typesystems_dst}")
    else:
        print(f"⚠️  Typesystems not found at {typesystems_src}")

def main():
    print("🏗️  Setting up PySide6 Directory Structure (_pyside6 style)...")
    print(f"📁 Target directory: {PYSIDE6_ROOT}")
    
    # 각 구조 생성
    create_include_structure()
    create_lib_structure()
    create_plugins_structure()
    create_share_structure()
    
    print(f"\n🎉 Directory structure setup completed!")
    print(f"📊 Structure summary:")
    
    # 구조 요약 출력
    for root_item in ['bin', 'include', 'lib', 'plugins', 'share']:
        item_path = f"{PYSIDE6_ROOT}/{root_item}"
        if os.path.exists(item_path):
            if os.path.isdir(item_path):
                item_count = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
                dir_count = len([f for f in os.listdir(item_path) if os.path.isdir(os.path.join(item_path, f))])
                print(f"   - {root_item}/: {item_count} files, {dir_count} directories")
            else:
                print(f"   - {root_item}: file")
        else:
            print(f"   - {root_item}: missing")

if __name__ == "__main__":
    main()