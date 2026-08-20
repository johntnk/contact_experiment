/**
 * Test: Matrix Display
 * Show diff matrix updating in-place
 */

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include "deepskin_sensor.h"

#pragma comment(lib, "DeepskinSDK.lib")

// Clear entire console buffer
void clear_console(HANDLE hConsole) {
    CONSOLE_SCREEN_BUFFER_INFO csbi;
    GetConsoleScreenBufferInfo(hConsole, &csbi);
    DWORD size = csbi.dwSize.X * csbi.dwSize.Y;
    DWORD written;
    COORD start = {0, 0};
    FillConsoleOutputCharacter(hConsole, ' ', size, start, &written);
    FillConsoleOutputAttribute(hConsole, csbi.wAttributes, size, start, &written);
    SetConsoleCursorPosition(hConsole, start);
}

int main() {
    if (deepskin_init() != DEEPSKIN_OK) {
        printf("Init failed: %s\n", deepskin_get_last_error());
        return -1;
    }

    int tx = 0, rx = 0;
    deepskin_get_matrix_size(&tx, &rx);

    if (deepskin_enable() != DEEPSKIN_OK) {
        printf("Enable failed\n");
        deepskin_release();
        return -1;
    }

    double* matrix = (double*)malloc(tx * rx * sizeof(double));
    HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);

    while (1) {
        // Clear entire console buffer every frame (handles window resize)
        clear_console(hConsole);

        deepskin_get_diff_matrix(matrix, tx * rx);

        // Print matrix (tx rows, rx cols)
        for (int y = 0; y < tx; y++) {
            for (int x = 0; x < rx; x++) {
                int val = (int)matrix[y * rx + x];
                if (val > 0) {
                    printf("%4d ", val);
                } else {
                    printf("    ");
                }
            }
            printf("\n");
        }

        Sleep(100);
    }

    free(matrix);
    deepskin_disable();
    deepskin_release();
    return 0;
}
