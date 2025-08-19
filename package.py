# -*- coding: utf-8 -*-
import os

name        = "pyside6"
version     = "6.9.1"
authors     = ["The Qt Project"]
description = "Python bindings for Qt6 (PySide6) : Using Pyside 6.9.1"

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
    "python-3.13.2",
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
    "pyside6-metaobjectdump",         # 메타오브젝트 덤프 (기존)
    "pyside6-qtpy2cpp",               # Python → C++ 변환
    
    # Shiboken 도구들
    "shiboken6",                      # 바인딩 생성기
    "shiboken6-genpyi"                # Shiboken용 stub 생성
]

build_command = "python {root}/rezbuild.py install"

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

    env.QT_PLUGIN_PATH.prepend("/core/Linux/APPZ/packages/qt/6.9.1/plugins")
    env.QT_PLUGIN_PATH.prepend("{root}/plugins")
    env.QT_PLUGIN_PATH.prepend("{root}/lib/PySide6/plugins")
    env.PYSIDE_DESIGNER_PLUGINS = "{root}/plugins/designer"
    
    env.LD_LIBRARY_PATH.prepend("{root}/lib")
    env.CMAKE_PREFIX_PATH.prepend("{root}")
    
    # 디버그 정보 출력 (선택적)
    # env.PYSIDE6_PYTHON_VERSION = python_version
    
uuid = "pyside6-6.9.1"    
    
