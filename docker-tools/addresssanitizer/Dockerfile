FROM ubuntu:22.04

LABEL maintainer="BugBust3r" \
      description="AddressSanitizer (ASan) runtime container for C/C++ memory safety testing"

WORKDIR /app

# Install build toolchain and clang with AddressSanitizer support
RUN apt-get update && apt-get install -y --no-install-recommends \
    clang \
    clang-tools \
    build-essential \
    cmake \
    gdb \
    && rm -rf /var/lib/apt/lists/*

# Create directories used by the tool wrapper
RUN mkdir -p /source /build /reports

# Copy and make executable the run script
# Fix line endings (convert CRLF to LF) and make executable
COPY run_asan.sh /app/run_asan.sh
RUN sed -i 's/\r$//' /app/run_asan.sh && chmod +x /app/run_asan.sh

ENV ASAN_OPTIONS=detect_leaks=1:abort_on_error=1:symbolize=1

# Default command (overridden by tool wrapper)
CMD ["/app/run_asan.sh"]

