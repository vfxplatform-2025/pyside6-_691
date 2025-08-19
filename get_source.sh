#!/usr/bin/env bash
set -e
set -x

# 사용할 실제 git 태그
real_tag="v6.9.1"

# REZ 또는 디렉토리 이름에서 version 추출
if [ -n "$REZ_BUILD_PROJECT_VERSION" ]; then
    version="$REZ_BUILD_PROJECT_VERSION"
else
    dirname=$(basename "$PWD")
    version="${dirname#pyside6-}"
    echo "⚠️ REZ_BUILD_PROJECT_VERSION 미설정, 디렉토리명에서 추출: $version"
fi

# 디렉토리 경로 설정
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="${script_dir}/source"
target_dir="${source_dir}/pyside-setup-${version}"

# 🔁 source 디렉토리 전체 정리
echo "🧹 Removing existing source dir: $source_dir"
rm -rf "$source_dir"
mkdir -p "$source_dir"

# 📥 clone & checkout
echo "📥 Cloning pyside-setup tag=$real_tag to $target_dir"
git clone https://code.qt.io/pyside/pyside-setup.git "$target_dir"
cd "$target_dir"
git fetch --tags
git checkout "$real_tag"

# 🔄 submodule 초기화
echo "🔁 Initializing submodules"
git submodule update --init --recursive

# ✅ 확인
echo "✅ PySide6 source ready: $target_dir"
ls -l "$target_dir/sources"
