# PySide6 6.9.1 다중 Python 버전 빌드 계획

## 프로젝트 개요

### 목표
Rocky Linux 9 환경에서 Rez 패키지 시스템을 이용해 PySide6 6.9.1을 다음 Python 버전들에 대해 빌드:
- Python 3.9.21
- Python 3.10.6  
- Python 3.11.9
- Python 3.12.10
- Python 3.13.2

### 핵심 요구사항
1. **rez-build -i 명령으로 빌드 실행**
2. **package.py 정의된 68개 도구 모두 빌드**
3. **모든 Python 버전에서 PySide6 바인딩 정상 작동**
4. **자동 에러 감지 및 수정 시스템 구현**

## 현재 상황 분석

### 성공 요소 (build.sh 기반)
- ✅ **검증된 빌드 방법**: build.sh가 Python 3.13.2에서 성공적으로 작동
- ✅ **헤더 경로 해결**: Clang/GCC 헤더 충돌 문제 해결된 상태
- ✅ **Shiboken6 래퍼**: 시스템 헤더 자동 추가 래퍼 구현됨
- ✅ **환경 설정**: Qt 6.9.1, Shiboken6 6.9.1 의존성 준비 완료

### 도전 과제
- 🔄 **다중 Python 지원**: 5개 버전 동시 빌드
- 🔄 **자동 에러 처리**: 빌드 실패 시 자동 복구
- 🔄 **Rez 통합**: rez-build -i 명령으로 실행

## 상세 실행 계획

### Phase 1: 기반 시스템 준비

#### 1.1 rezbuild.py 핵심 개선
**목표**: build.sh의 성공 패턴을 rezbuild.py에 통합

**주요 개선 사항**:
```python
# build.sh에서 성공한 환경 변수 설정
CLANG_HEADERS="/usr/lib/clang/19/include"
GCC_HEADERS="/usr/lib/gcc/x86_64-redhat-linux/11/include"
SYSTEM_HEADERS="/usr/include"
CPP_HEADERS="/usr/include/c++/11"

# Shiboken6 래퍼 생성 (build.sh 방식)
def create_shiboken_wrapper(build_path):
    wrapper_content = '''#!/bin/bash
    EXTRA_ARGS=""
    EXTRA_ARGS="$EXTRA_ARGS -I/usr/lib/clang/19/include"
    EXTRA_ARGS="$EXTRA_ARGS -I/usr/lib/gcc/x86_64-redhat-linux/11/include"
    EXTRA_ARGS="$EXTRA_ARGS -I/usr/include"
    EXTRA_ARGS="$EXTRA_ARGS -I/usr/include/c++/11"
    EXTRA_ARGS="$EXTRA_ARGS -resource-dir=/usr/lib/clang/19"
    
    exec /core/Linux/APPZ/packages/shiboken6/6.9.1/bin/shiboken6 $EXTRA_ARGS "$@"
    '''
```

#### 1.2 다중 Python 버전 지원 강화
**전략**: 각 Python 버전별로 독립적인 빌드 환경 구성

```python
PYTHON_VERSIONS = ["3.9.21", "3.10.6", "3.11.9", "3.12.10", "3.13.2"]

for python_version in PYTHON_VERSIONS:
    build_path = f"{BASE_BUILD_DIR}/python{python_version}"
    install_path = f"{INSTALL_DIR}/lib/python{major_minor}/site-packages"
    
    # 각 버전별 독립 빌드
    setup_python_environment(python_version)
    build_pyside6_for_version(python_version, build_path, install_path)
```

#### 1.3 스마트 에러 처리 시스템
**참조**: /home/m83/chulho/auto-build-system/1.0.0

**구현 기능**:
- **실시간 로그 분석**: 빌드 진행 중 에러 패턴 감지
- **자동 수정**: 알려진 문제에 대한 자동 해결책 적용
- **재시도 로직**: 최대 3회 재시도, 각 시도마다 다른 전략
- **프로세스 감지**: 기존 빌드 프로세스 감지 및 정리

### Phase 2: 빌드 전략 구현

#### 2.1 Primary 빌드 방법: rezbuild.py 기반
```bash
cd /home/m83/chulho/pyside6/6.9.1
rez-build -i
```

**빌드 순서**:
1. **환경 검증**: 모든 의존성 확인 (Qt, Shiboken6, Python 버전들)
2. **헤더 경로 설정**: build.sh 패턴 적용
3. **Shiboken 래퍼 생성**: 각 Python 버전별 래퍼 생성
4. **순차 빌드**: Python 3.13.2 → 3.12.10 → 3.11.9 → 3.10.6 → 3.9.21

#### 2.2 Fallback 빌드 방법: build_multi.sh
**활성화 조건**: rezbuild.py 방식이 연속 실패할 경우

```bash
cd /home/m83/chulho/pyside6/6.9.1
./build_multi.sh
```

**특징**:
- build.sh의 검증된 로직을 다중 Python 버전으로 확장
- 각 버전별 독립적인 빌드 환경
- 실패한 버전 건너뛰고 다음 버전 계속 진행

### Phase 3: 빌드 실행 및 모니터링

#### 3.1 실시간 모니터링
```python
# 빌드 진행률 추적
def monitor_build_progress():
    stages = ["환경설정", "헤더검증", "Shiboken래퍼", "Python빌드", "설치"]
    for stage in stages:
        log_stage_progress(stage)
        
# 에러 감지 및 자동 수정
def auto_error_recovery():
    error_patterns = {
        "stdbool.h not found": fix_header_paths,
        "Python.h not found": fix_python_paths,
        "shiboken6 failed": recreate_shiboken_wrapper
    }
```

#### 3.2 빌드 검증 체크포인트
각 Python 버전별로:
1. **빌드 완료 확인**: 필수 라이브러리 파일 존재 확인
2. **도구 설치 확인**: package.py의 68개 도구 검증
3. **바인딩 테스트**: 기본 PySide6 import 및 기능 테스트

### Phase 4: 설치 구조 및 통합

#### 4.1 최종 설치 구조
```
/core/Linux/APPZ/packages/pyside6/6.9.1/
├── bin/                    # 68개 PySide6 도구들
│   ├── pyside6-uic
│   ├── pyside6-rcc
│   ├── pyside6-designer
│   └── ... (총 68개)
├── lib/
│   ├── python3.9/site-packages/PySide6/
│   ├── python3.10/site-packages/PySide6/
│   ├── python3.11/site-packages/PySide6/
│   ├── python3.12/site-packages/PySide6/
│   └── python3.13/site-packages/PySide6/
├── include/                # 개발 헤더
├── share/                  # 문서 및 리소스
└── package.py             # Rez 패키지 정의 (다중 Python 지원)
```

#### 4.2 동적 Python 버전 감지
package.py의 commands() 함수에서 현재 활성 Python 버전 자동 감지:
```python
def commands():
    # 현재 Python 버전 감지
    result = subprocess.run(['python', '-c', 
        'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'], 
        capture_output=True, text=True)
    python_version = result.stdout.strip()
    
    # 해당 버전의 site-packages 경로 설정
    env.PYTHONPATH.prepend(f"{{root}}/lib/python{python_version}/site-packages")
```

## 에러 해결 시나리오

### Scenario 1: 헤더 파일 문제
**증상**: `stdbool.h not found`, `Python.h not found`
**해결**: 
1. 헤더 경로 재설정
2. Shiboken 래퍼 재생성  
3. C_INCLUDE_PATH, CPLUS_INCLUDE_PATH 환경변수 업데이트

### Scenario 2: Python 버전 충돌
**증상**: 잘못된 Python 버전 사용
**해결**:
1. PATH에서 해당 Python 버전 우선순위 조정
2. PYTHON_EXECUTABLE 명시적 설정
3. 가상환경 정리 후 재시도

### Scenario 3: Qt/Shiboken 의존성 문제  
**증상**: Qt 모듈 또는 Shiboken 찾을 수 없음
**해결**:
1. CMAKE_PREFIX_PATH 재설정
2. PKG_CONFIG_PATH 업데이트
3. 심볼릭 링크 확인 및 재생성

### Scenario 4: 메모리/디스크 부족
**증상**: 빌드 중단, 컴파일러 크래시
**해결**:
1. 병렬 작업 수 줄이기 (--jobs 1)
2. 임시 파일 정리
3. 모듈 단위 분할 빌드

## 성공 기준 및 검증

### 1차 검증: 빌드 완료
- [ ] 모든 Python 버전(3.9-3.13)에서 빌드 성공
- [ ] 빌드 로그에 `✅ Build successful` 메시지 확인
- [ ] /core/Linux/APPZ/packages/pyside6/6.9.1/ 설치 완료

### 2차 검증: 도구 설치
- [ ] /core/Linux/APPZ/packages/pyside6/6.9.1/bin/ 폴더에 68개 도구 존재
- [ ] 주요 도구 실행 테스트:
  ```bash
  pyside6-uic --version
  pyside6-rcc --help
  pyside6-designer --version
  shiboken6 --version
  ```

### 3차 검증: 바인딩 테스트
각 Python 버전별로:
```python
# 기본 import 테스트
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication, QWidget  
from PySide6.QtGui import QGuiApplication

# 버전 정보 확인
import PySide6
print(f"PySide6 version: {PySide6.__version__}")
```

### 4차 검증: Rez 통합
```bash
rez-env pyside6-6.9.1 python-3.13.2 -- python -c "import PySide6; print('Success!')"
rez-env pyside6-6.9.1 python-3.12.10 -- python -c "import PySide6; print('Success!')"
# ... 모든 Python 버전에 대해 테스트
```

## 타임라인 및 우선순위

### 즉시 실행 (Phase 1)
1. ⏰ **rezbuild.py 개선** - build.sh 패턴 통합
2. ⏰ **스마트 에러 처리** - auto-build-system 통합
3. ⏰ **다중 Python 지원** - 순차 빌드 로직 구현

### 빌드 실행 (Phase 2-3)  
4. ⏰ **rez-build -i 실행** - 기본 빌드 방법
5. ⏰ **실시간 모니터링** - 진행상황 추적 및 에러 대응
6. ⏰ **검증 및 테스트** - 각 단계별 성공 확인

### 마무리 (Phase 4)
7. ⏰ **통합 설치 완료** - 최종 패키지 구성
8. ⏰ **종합 테스트** - 모든 Python 버전 검증
9. ⏰ **문서화 완료** - 빌드 결과 및 사용법 정리

## 백업 및 복구 전략

### 빌드 실패 시 복구 순서
1. **로그 분석**: 실패 지점 및 원인 파악
2. **자동 수정 시도**: 알려진 패턴 기반 자동 해결
3. **수동 개입**: 새로운 문제에 대한 수동 수정
4. **부분 복구**: 성공한 Python 버전은 보존, 실패한 버전만 재시도
5. **전체 재시도**: 모든 설정 초기화 후 처음부터 재시작

### 데이터 보호
- **빌드 로그 보존**: 타임스탬프별 로그 파일 보관
- **중간 결과 백업**: 각 Python 버전별 빌드 결과 보존
- **설정 파일 버전 관리**: 수정된 파일들의 백업 유지

이 계획을 바탕으로 체계적이고 안정적인 다중 Python PySide6 빌드를 진행하겠습니다.