import cv2

# Check if OpenCV was built with GStreamer support
if cv2.getBuildInformation().find('GStreamer') != -1:
    print("OpenCV supports GStreamer.")
else:
    print("OpenCV does not support GStreamer.")

# Test GStreamer pipeline
gst_pipeline = 'videotestsrc ! videoconvert ! appsink'
cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Failed to open GStreamer pipeline.")
else:
    print("Successfully opened GStreamer pipeline.")
    # Read and display a frame to verify functionality
    ret, frame = cap.read()
    if ret:
        cv2.imshow('Frame', frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Failed to read frame from GStreamer pipeline.")
    cap.release()