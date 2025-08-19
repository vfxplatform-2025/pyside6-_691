# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 필요한 가이드를 제공합니다.

## 저장소 개요

VFX Platform 2025 호환성을 위한 PySide6 6.9.1 빌드 저장소입니다. 다중 Python 버전 지원(3.9-3.13)으로 PySide6(Qt6용 Python 바인딩)을 컴파일하기 위한 빌드 스크립트와 설정을 포함합니다.

## 아키텍처

### 핵심 빌드 구조
- **소스 관리**: PySide6 소스 코드는 `source/pyside-setup/` 디렉토리에 위치
- **빌드 스크립트**: 스마트 오류 처리 및 재시도 메커니즘을 가진 다양한 빌드 방법
- **다중 Python 지원**: Python 버전 3.9.21, 3.10.6, 3.11.9, 3.12.10, 3.13.2 지원
- **Rez 패키지 시스템**: 의존성 해결을 위한 Rez 패키지 관리 사용

### 주요 구성 요소

1. **빌드 스크립트**:
   - `build.sh` - Ninja를 사용한 검증된 CMake 기반 빌드 방법
   - `build_multi.sh` - 포괄적인 오류 처리를 가진 다중 Python 버전 빌드
   - `complete_build.py` - 검증된 build.sh 방법을 사용하는 Python 기반 빌드
   - `rezbuild.py` - 스마트 오류 감지 및 자동 수정을 가진 고급 빌드 매니저

2. **패키지 설정**:
   - `package.py` - 다중 Python 버전 지원을 가진 Rez 패키지 정의
   - 도구, 의존성, 환경 설정 정의

## 빌드 명령어

### 주요 빌드 명령어
```bash
# 표준 단일 빌드 (검증된 build.sh 방법 사용)
./build.sh

# 다중 Python 버전 빌드
./build_multi.sh

# Python 기반 완전 빌드
python complete_build.py

# Rez 기반 빌드 (스마트 오류 처리)
rez-build -i
```

### 빌드 의존성
- **Qt 6.9.1**: `/core/Linux/APPZ/packages/qt/6.9.1` 위치
- **Shiboken6 6.9.1**: `/core/Linux/APPZ/packages/shiboken6/6.9.1` 위치
- **GCC 11.5.0**: 특정 헤더 경로를 가진 GCC 툴셋 사용
- **System Clang 19.1.7**: 코드 분석 및 헤더 처리용
- **CMake 3.26.5** 및 **Ninja 1.11.1**: 빌드 시스템 도구

### 환경 요구사항
빌드 시스템은 복잡한 헤더 경로 관리를 처리합니다:
- Clang 헤더: `/usr/lib/clang/19/include`
- GCC 헤더: `/usr/lib/gcc/x86_64-redhat-linux/11/include`
- C++ 헤더: `/usr/include/c++/11`
- Python 헤더: Python 버전별로 동적 감지

## 빌드 시스템 기능

### 스마트 빌드 관리 (`rezbuild.py`)
- **오류 감지**: 일반적인 빌드 문제를 자동으로 감지하고 수정
- **빌드 프로세스 종료**: 충돌하는 빌드 프로세스를 안전하게 종료
- **헤더 경로 관리**: 적절한 include 경로로 Shiboken 래퍼 생성
- **재시도 로직**: 다양한 전략으로 최대 3번 빌드 시도
- **다중 Python 조정**: 지원되는 모든 Python 버전에 대한 빌드

### Shiboken 래퍼 시스템
Shiboken 코드 생성을 위한 적절한 헤더 경로를 추가하는 래퍼 스크립트 생성:
```bash
# 자동 생성된 래퍼가 시스템 헤더 추가
-I/usr/lib/clang/19/include
-I/usr/lib/gcc/x86_64-redhat-linux/11/include  
-I/usr/include/c++/11
```

### 빌드 전략
1. **CMake 빌드**: Ninja와 직접 CMake (가장 빠르고 안정적)
2. **Setup.py 빌드**: 포괄적인 환경 설정으로 setup.py로 폴백
3. **축소 모듈 빌드**: 전체 빌드 실패 시 핵심 모듈만 빌드

## 개발 워크플로우

### 변경사항 적용
1. 빌드 스크립트 또는 설정 수정
2. 먼저 단일 Python 버전으로 테스트: `./build.sh`
3. 다중 Python 빌드 테스트: `./build_multi.sh`
4. 오류 처리를 위한 프로덕션 빌드에는 `rezbuild.py` 사용

### 빌드 문제 디버깅
- 타임스탬프가 있는 로그 파일에서 빌드 로그 확인
- 자동 오류 감지 및 수정을 위해 `rezbuild.py` 사용
- 헤더 경로 및 환경 변수 확인
- 충돌하는 빌드 프로세스 확인

### 설치 테스트
```python
# 테스트 스크립트는 install_root/bin/test_pyside6.py에 자동 생성됨
python test_pyside6.py
```

## 설치 구조

### 다중 Python 레이아웃
```
/core/Linux/APPZ/packages/pyside6/6.9.1/
├── bin/                    # PySide6 도구들 (uic, rcc, designer 등)
├── lib/
│   ├── python3.9/site-packages/PySide6/
│   ├── python3.10/site-packages/PySide6/
│   ├── python3.11/site-packages/PySide6/
│   ├── python3.12/site-packages/PySide6/
│   └── python3.13/site-packages/PySide6/
├── include/                # 개발 헤더
├── share/                  # 문서 및 리소스
└── package.py             # Rez 패키지 정의
```

### 사용 가능한 도구들
- **UI 도구**: pyside6-uic, pyside6-rcc, pyside6-designer
- **QML 도구**: pyside6-qml, pyside6-qmllint, pyside6-qmlformat
- **배포 도구**: pyside6-deploy, pyside6-android-deploy
- **개발 도구**: shiboken6, pyside6-genpyi, pyside6-metaobjectdump

## 중요 사항

- 이 빌드 시스템은 PySide6 코드 생성을 위한 복잡한 C++ 헤더 해결을 처리합니다
- 빌드 프로세스는 각 Python 버전에 대해 버전별 설치를 생성합니다
- 환경 변수가 중요합니다 - 빌드 스크립트가 이를 자동으로 처리합니다
- Shiboken 래퍼는 시스템 헤더 충돌 해결에 필수적입니다
- 빌드 로그에는 컴파일 문제 해결을 위한 상세 정보가 포함됩니다