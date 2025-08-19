#!/usr/bin/env python3
"""
PySide6 Tool Wrappers Creator
_pyside6 스타일의 사용자 친화적 래퍼 스크립트들을 생성하는 도구
"""

import os
import stat
from pathlib import Path

# 기본 경로 설정
PYSIDE6_ROOT = "/core/Linux/APPZ/packages/pyside6/6.9.1"
BIN_DIR = f"{PYSIDE6_ROOT}/bin"
PYTHON3_13_SITE_PACKAGES = f"{PYSIDE6_ROOT}/lib/python3.13/site-packages"

def create_directory():
    """bin 디렉토리 생성"""
    os.makedirs(BIN_DIR, exist_ok=True)
    print(f"✅ Created bin directory: {BIN_DIR}")

def create_wrapper_script(tool_name, target_path, script_type="binary"):
    """래퍼 스크립트 생성"""
    wrapper_path = f"{BIN_DIR}/{tool_name}"
    
    if script_type == "python":
        wrapper_content = f'''#!/bin/bash
# PySide6 {tool_name} wrapper
exec python3 "{target_path}" "$@"
'''
    else:  # binary
        wrapper_content = f'''#!/bin/bash
# PySide6 {tool_name} wrapper  
exec "{target_path}" "$@"
'''
    
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)
    
    # 실행 권한 부여
    os.chmod(wrapper_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    print(f"✅ Created wrapper: {tool_name} -> {target_path}")

def copy_support_files():
    """지원 파일들과 라이브러리들 복사"""
    import shutil
    
    print(f"\n🔧 Copying support files and libraries...")
    
    # Python 스크립트 파일들 직접 복사
    script_files = [
        ("android_deploy.py", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/android_deploy.py"),
        ("deploy.py", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/deploy.py"),
        ("metaobjectdump.py", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/metaobjectdump.py"),
        ("project.py", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/project.py"),
        ("qml.py", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/qml.py"),
        ("qtpy2cpp.py", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/qtpy2cpp.py"),
        ("pyside_tool.py", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/pyside_tool.py"),
        ("shiboken_tool.py", f"{PYTHON3_13_SITE_PACKAGES}/shiboken6_generator/shiboken6"),  # 실제로는 실행파일
        ("requirements-android.txt", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/requirements-android.txt"),
    ]
    
    for dest_name, source_path in script_files:
        dest_path = f"{BIN_DIR}/{dest_name}"
        if os.path.exists(source_path):
            if dest_name.endswith('.py') or dest_name.endswith('.txt'):
                shutil.copy2(source_path, dest_path)
                if dest_name.endswith('.py'):
                    os.chmod(dest_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                print(f"✅ Copied: {dest_name}")
            else:
                # shiboken_tool.py는 실제로는 바이너리이므로 래퍼로 생성
                create_wrapper_script("shiboken_tool.py", source_path, "binary")
        else:
            print(f"⚠️  Missing: {source_path}")
    
    # 라이브러리 디렉토리들 복사
    lib_dirs = [
        ("deploy_lib", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/../deploy_lib"),  # 실제로는 site-packages 내부에 없을 수 있음
        ("project_lib", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/../project_lib"),
        ("qtpy2cpp_lib", f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/../qtpy2cpp_lib"),
    ]
    
    # 실제 경로 찾기
    for lib_name, expected_path in lib_dirs:
        # PySide6 내부에서 라이브러리 찾기
        possible_paths = [
            f"{PYTHON3_13_SITE_PACKAGES}/PySide6/{lib_name}",
            f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/{lib_name}",
        ]
        
        source_found = None
        for path in possible_paths:
            if os.path.exists(path):
                source_found = path
                break
        
        if source_found:
            dest_path = f"{BIN_DIR}/{lib_name}"
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            shutil.copytree(source_found, dest_path)
            print(f"✅ Copied library: {lib_name}")
        else:
            print(f"⚠️  Library not found: {lib_name}")

def main():
    print("🔧 Creating PySide6 Tool Wrappers...")
    
    # bin 디렉토리 생성
    create_directory()
    
    # Qt libexec 도구들 (바이너리) - pyside6- 접두사 버전과 기본 버전 둘 다
    qt_tools = {
        "pyside6-uic": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/libexec/uic",
        "uic": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/libexec/uic",
        "pyside6-rcc": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/libexec/rcc", 
        "rcc": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/libexec/rcc",
        "pyside6-qmlcachegen": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/libexec/qmlcachegen",
        "qmlcachegen": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/libexec/qmlcachegen",
        "pyside6-qmlimportscanner": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/libexec/qmlimportscanner",
        "qmlimportscanner": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/libexec/qmlimportscanner",
        "pyside6-qmltyperegistrar": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/libexec/qmltyperegistrar",
        "qmltyperegistrar": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/Qt/libexec/qmltyperegistrar",
    }
    
    # PySide6 실행 파일들 (바이너리) - pyside6- 접두사 버전과 기본 버전 둘 다
    pyside_tools = {
        "pyside6-assistant": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/assistant",
        "assistant": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/assistant",
        "pyside6-designer": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/designer",
        "designer": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/designer",
        "pyside6-linguist": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/linguist",
        "linguist": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/linguist",
        "pyside6-lrelease": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/lrelease",
        "lrelease": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/lrelease",
        "pyside6-lupdate": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/lupdate",
        "lupdate": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/lupdate",
        "pyside6-balsam": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/balsam",
        "balsam": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/balsam",
        "pyside6-balsamui": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/balsamui",
        "balsamui": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/balsamui",
        "pyside6-qmlformat": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/qmlformat",
        "qmlformat": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/qmlformat",
        "pyside6-qmllint": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/qmllint",
        "qmllint": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/qmllint",
        "pyside6-qmlls": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/qmlls",
        "qmlls": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/qmlls",
        "pyside6-qsb": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/qsb",
        "qsb": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/qsb",
        "pyside6-svgtoqml": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/svgtoqml",
        "svgtoqml": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/svgtoqml",
    }
    
    # Python 스크립트들
    python_scripts = {
        "pyside6-android-deploy": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/android_deploy.py",
        "pyside6-deploy": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/deploy.py",
        "pyside6-metaobjectdump": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/metaobjectdump.py",
        "pyside6-project": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/project.py",
        "pyside6-qml": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/qml.py",
        "pyside6-qtpy2cpp": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/scripts/qtpy2cpp.py",
        "pyside6-genpyi": f"{PYTHON3_13_SITE_PACKAGES}/PySide6/support/generate_pyi.py",
    }
    
    # Shiboken6 도구들
    shiboken_tools = {
        "shiboken6": f"{PYTHON3_13_SITE_PACKAGES}/shiboken6_generator/shiboken6",
        "shiboken6-genpyi": f"{PYTHON3_13_SITE_PACKAGES}/shiboken6_generator/shiboken6",  # 같은 실행파일
    }
    
    print(f"\n🔧 Creating Qt libexec tool wrappers...")
    for tool_name, target_path in qt_tools.items():
        if os.path.exists(target_path):
            create_wrapper_script(tool_name, target_path, "binary")
        else:
            print(f"⚠️  Missing: {target_path}")
    
    print(f"\n🔧 Creating PySide6 tool wrappers...")
    for tool_name, target_path in pyside_tools.items():
        if os.path.exists(target_path):
            create_wrapper_script(tool_name, target_path, "binary")
        else:
            print(f"⚠️  Missing: {target_path}")
    
    print(f"\n🔧 Creating Python script wrappers...")
    for tool_name, target_path in python_scripts.items():
        if os.path.exists(target_path):
            create_wrapper_script(tool_name, target_path, "python")
        else:
            print(f"⚠️  Missing: {target_path}")
    
    print(f"\n🔧 Creating Shiboken6 tool wrappers...")
    for tool_name, target_path in shiboken_tools.items():
        if os.path.exists(target_path):
            create_wrapper_script(tool_name, target_path, "binary")
        else:
            print(f"⚠️  Missing: {target_path}")
    
    # 지원 파일들과 라이브러리 복사
    copy_support_files()
    
    print(f"\n🎉 Wrapper script creation completed!")
    print(f"📁 All tools available in: {BIN_DIR}")
    
    # 생성된 도구 목록 출력
    created_tools = [f for f in os.listdir(BIN_DIR) if os.path.isfile(os.path.join(BIN_DIR, f))]
    created_dirs = [f for f in os.listdir(BIN_DIR) if os.path.isdir(os.path.join(BIN_DIR, f))]
    
    print(f"📊 Created {len(created_tools)} tool wrappers and {len(created_dirs)} support directories:")
    print("Tools:")
    for tool in sorted(created_tools):
        print(f"   - {tool}")
    if created_dirs:
        print("Support directories:")
        for dir_name in sorted(created_dirs):
            print(f"   - {dir_name}/")

if __name__ == "__main__":
    main()