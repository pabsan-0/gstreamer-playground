// Compile with:
// $ g++ opencv_gst.cpp -o opencv_gst `pkg-config --cflags --libs opencv4`

#include <stdio.h>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/opencv.hpp>
#include <string>
using std::string;


// This func to get the image format from a mat's .type()
string type2str(int type) {
    string r;

    uchar depth = type & CV_MAT_DEPTH_MASK;
    uchar chans = 1 + (type >> CV_CN_SHIFT);

    switch ( depth ) {
        case CV_8U:  r = "8U"; break;
        case CV_8S:  r = "8S"; break;
        case CV_16U: r = "16U"; break;
        case CV_16S: r = "16S"; break;
        case CV_32S: r = "32S"; break;
        case CV_32F: r = "32F"; break;
        case CV_64F: r = "64F"; break;
        default:     r = "User"; break;
    }

    r += "C";
    r += (chans+'0');

    return r;
}



int main(int argc, char** argv) {

    // == gstreamer pipeline ==
    //      gst-launch-1.0 v4l2src
    //      ! video/x-raw, framerate=30/1, width=640, height=480, format=RGB
    //      ! videoconvert
    //      ! THIS SCRIPT RIGH HERE
    //      ! videoconvert
    //      ! ximagesink


    // Source -> This script
    cv::VideoCapture cap("v4l2src ! video/x-raw, framerate=30/1, width=640, height=480 ! videoconvert ! appsink");
    if (!cap.isOpened()) {
        printf("=ERR= can't create video capture\n");
        return -1;
    }

    // This script -> Sink
    cv::VideoWriter writer;
    writer.open("appsrc ! videoconvert ! perf ! ximagesink", 0, (double)30, cv::Size(640, 480), true);
    if (!writer.isOpened()) {
        printf("=ERR= can't create video writer\n");
        return -1;
    }


    // Core opencv processing
    cv::Mat frame;
    int key;

    while (cap.isOpened()) {
        cap >> frame;
        if (frame.empty())
            break;

        // Verify image type then take some pixel value
        std::string typeMat = type2str(frame.type());
        cv::Vec3b bgrPixel = frame.at<cv::Vec3b>(0, 0);

        std::cout << typeMat  << "; ";
        std::cout << bgrPixel << "; ";
        std::cout << std::endl;

        // Draw rectangle on top of theimage
        cv::Rect rect(20, 20, 40, 40);
        cv::rectangle(frame, rect, cv::Scalar(0, 255, 0));

        writer << frame;
        key = cv::waitKey( 30 );
    }
}