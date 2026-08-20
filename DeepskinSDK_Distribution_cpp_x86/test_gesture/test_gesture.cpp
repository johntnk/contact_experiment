/**
 * Test: Gesture Detection
 * Detect gestures and output type as number 1-6
 */

#include <windows.h>
#include <stdio.h>
#include "deepskin_sensor.h"

#pragma comment(lib, "DeepskinSDK.lib")

int main() {
    printf("\n=== Gesture Test ===\n");
    printf("1=PalmPress 2=Slap 3=Stroke 4=FistSmash 5=FingerGather 6=SingleTap\n\n");

    if (deepskin_init() != DEEPSKIN_OK) {
        printf("Init failed: %s\n", deepskin_get_last_error());
        return -1;
    }

    if (deepskin_enable() != DEEPSKIN_OK) {
        printf("Enable failed\n");
        deepskin_release();
        return -1;
    }

    printf("Touch sensor to detect gestures...\n\n");

    int count = 0;

    while (1) {
        DeepskinGesture gesture;
        if (deepskin_get_gesture(&gesture)) {
            count++;
            printf("#%d  type=%d  force=%d  area=%d  dur=%.0fms\n",
                count, gesture.gesture_type, gesture.force_max, gesture.area_max, gesture.duration_ms);
        }
        Sleep(50);
    }

    deepskin_disable();
    deepskin_release();
    return 0;
}
