#!/bin/bash
set -euo pipefail

mkdir -p /source /build /reports

if [ "${USE_DEMO:-false}" = "true" ]; then
  cat > /source/asan_demo.c << 'DEMO_EOF'
#include <string.h>
#include <stdio.h>
int main() {
  char buf[8];
  strcpy(buf, "AAAAAAAAAAAAAAAAAAAAAAAA");
  printf("%s\n", buf);
  return 0;
}
DEMO_EOF
  echo "[ASan] Created demo vulnerable C program"
fi

SRC_FILES=""
for ext in c cc cpp; do
  for f in /source/*."$ext"; do
    [ -f "$f" ] && SRC_FILES="$SRC_FILES $f"
  done
done

if [ -z "$SRC_FILES" ]; then
  echo "NO_SOURCES"
  exit 0
fi

echo "[ASan] Compiling:$SRC_FILES"
clang++ -fsanitize=address,undefined -g -O1 $SRC_FILES -o /build/asan_app

echo "[ASan] Running instrumented binary"
ASAN_OPTIONS=detect_leaks=1:abort_on_error=0:symbolize=1 /build/asan_app
