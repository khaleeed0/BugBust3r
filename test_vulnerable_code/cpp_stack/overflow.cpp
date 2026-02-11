#include <cstring>
#include <iostream>

void stack_overflow(char* input) {
    char buffer[8];
    strcpy(buffer, input);  // Buffer overflow if input > 7 chars
    std::cout << buffer << std::endl;
}

int main() {
    char data[] = "123456789012";  // 12 chars - overflows buffer[8], ASan detects reliably
    stack_overflow(data);  // Triggers stack-buffer-overflow
    return 0;
}
