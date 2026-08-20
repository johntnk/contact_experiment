/**
 * Test: JSON Output
 * Output complete JSON for each gesture
 */

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include "deepskin_sensor.h"

#pragma comment(lib, "DeepskinSDK.lib")

int main() {
    printf("\n=== JSON Output Test ===\n\n");

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

    printf("Touch sensor to see JSON...\n\n");

    double* matrix = (double*)malloc(tx * rx * sizeof(double));
    char json[32768];
    int count = 0;

    while (1) {
        deepskin_get_diff_matrix(matrix, tx * rx);

        DeepskinGesture gesture;
        if (deepskin_get_gesture(&gesture)) {
            count++;
            printf("--- Gesture #%d ---\n", count);

            if (deepskin_get_recent_gestures_json(1, json, sizeof(json)) == DEEPSKIN_OK) {
                printf("%s\n\n", json);
            }
        }

        Sleep(50);
    }

    free(matrix);
    deepskin_disable();
    deepskin_release();
    return 0;
}
