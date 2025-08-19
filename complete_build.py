#!/usr/bin/env python3
"""
Complete PySide6 build script using build.sh proven approach
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

def main():
    print("🛠️  Complete PySide6 Build (using build.sh proven approach)")
    print("=" * 70)
    
    # Set base paths
    script_dir = Path(__file__).parent
    source_dir = script_dir / "source" / "pyside-setup"  
    build_dir = script_dir / "build_complete"
    install_dir = Path("/core/Linux/APPZ/packages/pyside6/6.9.1")
    qt_prefix = "/core/Linux/APPZ/packages/qt/6.9.1"
    shiboken_dir = "/core/Linux/APPZ/packages/shiboken6/6.9.1"
    
    print(f"Source: {source_dir}")
    print(f"Build: {build_dir}")
    print(f"Install: {install_dir}")
    
    # Clean build directory
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)
    
    # Set environment like build.sh
    env = os.environ.copy()
    
    # Remove problematic GCC toolset paths
    old_path = env.get("PATH", "")
    clean_path_parts = []
    for part in old_path.split(":"):
        if "gcc-toolset-14" not in part and "gcc-toolset-13" not in part:
            clean_path_parts.append(part)
    
    # Set PATH with Qt and Shiboken first
    env["PATH"] = f"{qt_prefix}/bin:{shiboken_dir}/bin:" + ":".join(clean_path_parts)
    
    # Remove problematic library path
    if "LD_LIBRARY_PATH" in env:
        del env["LD_LIBRARY_PATH"]
    
    # Set Qt environment
    env["QT_DIR"] = qt_prefix
    env["CMAKE_PREFIX_PATH"] = f"{qt_prefix}:{shiboken_dir}"
    env["LD_LIBRARY_PATH"] = f"{qt_prefix}/lib:{shiboken_dir}/lib"
    env["PKG_CONFIG_PATH"] = f"{qt_prefix}/lib/pkgconfig:{shiboken_dir}/lib/pkgconfig"
    
    # Python environment
    python_version = "3.13"
    env["PYTHONPATH"] = f"{install_dir}/lib/python{python_version}/site-packages"
    
    # System headers - exactly like build.sh
    clang_headers = "/usr/lib/clang/19/include"
    gcc_headers = "/usr/lib/gcc/x86_64-redhat-linux/11/include"
    system_headers = "/usr/include"
    cpp_headers = "/usr/include/c++/11"
    
    # Verify header directories exist
    for header_dir in [clang_headers, gcc_headers, system_headers, cpp_headers]:
        if Path(header_dir).exists():
            print(f"✓ Found header directory: {header_dir}")
        else:
            print(f"⚠️  Header directory not found: {header_dir}")
    
    # Verify stdbool.h files
    for stdbool_path in [f"{clang_headers}/stdbool.h", f"{gcc_headers}/stdbool.h"]:
        if Path(stdbool_path).exists():
            print(f"✓ Found stdbool.h at: {stdbool_path}")
    
    # Set environment variables for Shiboken's Clang
    env["CLANG_BUILTIN_INCLUDE_DIR"] = clang_headers
    env["C_INCLUDE_PATH"] = f"{gcc_headers}:{clang_headers}:{system_headers}"
    env["CPLUS_INCLUDE_PATH"] = f"{cpp_headers}:{gcc_headers}:{clang_headers}:{system_headers}"
    env["CLANG_INCLUDE_PATHS"] = f"{clang_headers}:{gcc_headers}:{cpp_headers}:{system_headers}"
    env["SHIBOKEN_INCLUDE_PATHS"] = f"{clang_headers}:{gcc_headers}:{system_headers}"
    
    # Build environment
    env["MAKEFLAGS"] = f"-j{os.cpu_count()}"
    env["NINJA_STATUS"] = "[%f/%t] "
    
    # Create shiboken wrapper like build.sh
    shiboken_wrapper_dir = build_dir / "shiboken_wrapper"
    shiboken_wrapper_dir.mkdir()
    
    shiboken_wrapper_script = shiboken_wrapper_dir / "shiboken6"
    with open(shiboken_wrapper_script, 'w') as f:
        f.write(f'''#!/bin/bash
# Shiboken wrapper to add proper include paths

# Add system headers to arguments
EXTRA_ARGS=""
EXTRA_ARGS="$EXTRA_ARGS -I{clang_headers}"
EXTRA_ARGS="$EXTRA_ARGS -I{gcc_headers}"
EXTRA_ARGS="$EXTRA_ARGS -I{system_headers}"
EXTRA_ARGS="$EXTRA_ARGS -I{cpp_headers}"
EXTRA_ARGS="$EXTRA_ARGS -resource-dir=/usr/lib/clang/19"

# Set environment
export C_INCLUDE_PATH="{gcc_headers}:{clang_headers}:{system_headers}"
export CPLUS_INCLUDE_PATH="{cpp_headers}:{gcc_headers}:{clang_headers}:{system_headers}"

# Call original shiboken6 with additional arguments
exec {shiboken_dir}/bin/shiboken6 $EXTRA_ARGS "$@"
''')
    
    shiboken_wrapper_script.chmod(0o755)
    
    # Add wrapper to PATH
    env["PATH"] = f"{shiboken_wrapper_dir}:{env['PATH']}"
    
    # Change to source directory for setup.py
    os.chdir(source_dir)
    
    # Setup environment for setup.py
    env["QMAKE"] = f"{qt_prefix}/bin/qmake"
    env["QT_QMAKE_EXECUTABLE"] = f"{qt_prefix}/bin/qmake"
    
    # Set extensive environment variables to help Shiboken find headers
    env["C_INCLUDE_PATH"] = f"{gcc_headers}:{clang_headers}:{system_headers}:/usr/include/linux"
    env["CPLUS_INCLUDE_PATH"] = f"{cpp_headers}:{gcc_headers}:{clang_headers}:{system_headers}:/usr/include/linux"
    env["CLANG_BUILTIN_INCLUDE_DIR"] = clang_headers
    env["CLANG_INCLUDE_DIRS"] = f"{clang_headers}:{gcc_headers}:{system_headers}"
    
    # Force Shiboken to use system clang with proper headers
    env["LLVM_INSTALL_DIR"] = "/usr"
    env["CLANG_INCLUDE_PATH"] = clang_headers
    env["CLANG_RESOURCE_DIR"] = clang_headers
    
    # Set build directory
    env["PYSIDE_BUILD_DIR"] = str(build_dir)
    env["PYSIDE_INSTALL_DIR"] = str(install_dir)
    
    print("🔧 Starting PySide6 build with all modules...")
    
    try:
        # Build all modules using setup.py like successful build.sh
        cmd = [
            "python3", "setup.py", "build",
            "--qmake", f"{qt_prefix}/bin/qmake",
            "--jobs", str(os.cpu_count()),
            "--verbose-build"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env, cwd=str(source_dir))
        
        if result.returncode != 0:
            print("❌ Build failed")
            return 1
            
        print("✅ Build completed successfully")
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return 1
    
    print("📦 Installing PySide6...")
    try:
        # Install using setup.py
        cmd = ["python3", "setup.py", "install", "--prefix", str(install_dir)]
        
        result = subprocess.run(cmd, env=env, cwd=str(source_dir))
        
        if result.returncode != 0:
            print("❌ Installation failed")
            return 1
            
        print("✅ Installation completed")
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return 1
    
    # Verify installation
    bin_dir = install_dir / "bin"
    if bin_dir.exists():
        print("📋 Installed tools:")
        tools = list(bin_dir.glob("*"))
        for tool in tools[:10]:  # Show first 10 tools
            print(f"  {tool.name}")
        if len(tools) > 10:
            print(f"  ... and {len(tools) - 10} more tools")
        print(f"Total tools installed: {len(tools)}")
    else:
        print("⚠️  No tools directory found")
    
    print("🎉 Complete PySide6 build finished!")
    return 0

if __name__ == "__main__":
    sys.exit(main())