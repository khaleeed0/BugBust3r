#include <cstdlib>
#include <cstring>
#include <iostream>

int main() {
    char* heap_buf = (char*)malloc(10);
    strcpy(heap_buf, "OVERFLOW_DATA_VERY_LONG_STRING");  // Heap buffer overflow
    std::cout << heap_buf << std::endl;
    free(heap_buf);
    return 0;
}
