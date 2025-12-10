#include <string.h>
#include <stdio.h>
#include <stdlib.h>

void buffer_overflow_vuln(char *input) {
    char buffer[10];
    strcpy(buffer, input);  // Buffer overflow vulnerability
    printf("%s", buffer);
}

void unsafe_scanf() {
    char buf[100];
    scanf("%s", buf);  // Unsafe scanf
}

int main() {
    char data[100] = "AAAAAAAAAAAAAAAAAAAAAAAA";
    buffer_overflow_vuln(data);
    return 0;
}

