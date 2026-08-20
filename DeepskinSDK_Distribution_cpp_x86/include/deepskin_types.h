/**
 * @file deepskin_types.h
 * @brief Deepskin SDK - Type Definitions
 *
 * Simplified structure without pointers for safe DLL boundary passing.
 */

#ifndef DEEPSKIN_TYPES_H
#define DEEPSKIN_TYPES_H

// DLL export macro
#ifdef DEEPSKIN_EXPORTS
    #define DEEPSKIN_API __declspec(dllexport)
#else
    #define DEEPSKIN_API __declspec(dllimport)
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Error codes
#define DEEPSKIN_OK                 0
#define DEEPSKIN_ERR_NOT_FOUND      -1
#define DEEPSKIN_ERR_OPEN_FAILED    -2
#define DEEPSKIN_ERR_NOT_STARTED    -3
#define DEEPSKIN_ERR_BUFFER_SMALL   -4

// Gesture types (6 types)
#define GESTURE_NONE            0
#define GESTURE_PALM_PRESS      1
#define GESTURE_SLAP            2
#define GESTURE_STROKE          3
#define GESTURE_FIST_SMASH      4
#define GESTURE_FINGER_GATHER   5
#define GESTURE_SINGLE_TAP      6

// Peak info structure
typedef struct {
    int row;
    int col;
    int value;
} DeepskinPeakInfo;

// Simplified gesture event structure (NO POINTERS - safe for DLL boundary)
typedef struct {
    // Gesture type
    int gesture_type;
    const char* gesture_name;

    // Timing
    int start_frame;
    int end_frame;
    int duration_frames;
    double duration_ms;

    // Force statistics
    int force_max;
    int force_avg;
    int force_min;
    int force_peak;
    double force_std_dev;
    double force_energy;

    // Area statistics
    int area_max;
    int area_avg;
    int area_min;
    double area_std_dev;
    double contact_ratio;

    // Top peaks (up to 5)
    DeepskinPeakInfo top_peaks[5];
    int top_peaks_count;
    int total_peak_count;

    // Trajectory
    double centroid_start_x;
    double centroid_start_y;
    double centroid_end_x;
    double centroid_end_y;
    double drift;
    double drift_x;
    double drift_y;
    double total_distance;
    double velocity_avg;
    double velocity_max;
    double acceleration_avg;

    // Shape
    int shape_width;
    int shape_height;
    double shape_aspect_ratio;
    double shape_perimeter;
    double shape_convexity;
    double shape_eccentricity;
    double shape_fill_ratio;

    // Spread
    double spread_max;
    double spread_avg;
    double spread_min;
    double spread_std_dev;

    // Stability
    double centroid_variance_x;
    double centroid_variance_y;
} DeepskinGesture;

#ifdef __cplusplus
}
#endif

#endif // DEEPSKIN_TYPES_H
