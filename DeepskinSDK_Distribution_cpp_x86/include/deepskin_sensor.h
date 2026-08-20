/**
 * @file deepskin_sensor.h
 * @brief Deepskin SDK - Main API Interface
 */

#ifndef DEEPSKIN_SENSOR_H
#define DEEPSKIN_SENSOR_H

#include "deepskin_types.h"

#ifdef __cplusplus
extern "C" {
#endif

// Basic control
DEEPSKIN_API int deepskin_init(void);
DEEPSKIN_API void deepskin_release(void);
DEEPSKIN_API int deepskin_enable(void);
DEEPSKIN_API void deepskin_disable(void);
DEEPSKIN_API void deepskin_reset(void);

// Data access
DEEPSKIN_API int deepskin_get_diff_matrix(double* out_data, int out_len);
DEEPSKIN_API int deepskin_get_current_json(char* out_json, int buf_size);
DEEPSKIN_API int deepskin_get_gesture(DeepskinGesture* gesture);
DEEPSKIN_API int deepskin_get_all_gestures_json(char* out_json, int buf_size);
DEEPSKIN_API int deepskin_get_recent_gestures_json(int count, char* out_json, int buf_size);

// Status query
DEEPSKIN_API int deepskin_is_touching(void);
DEEPSKIN_API int deepskin_get_matrix_size(int* tx, int* rx);

// Error handling
DEEPSKIN_API const char* deepskin_get_last_error(void);

#ifdef __cplusplus
}
#endif

#endif // DEEPSKIN_SENSOR_H
