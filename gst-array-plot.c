// example appsrc for gstreamer 1.0 with own mainloop & external buffers. based on example from gstreamer docs.
// public domain, 2015 by Florian Echtler <floe@butterbrot.org>
// modified, 2023 by Pablo Santana <psantana@catec.aero>
// compile with:
// gcc --std=c99 -Wall $(pkg-config --cflags gstreamer-1.0) -o gst-appsrc gst-appsrc.c $(pkg-config --libs gstreamer-1.0) -lgstapp-1.0

#include <gst/gst.h>
#include <gst/app/gstappsrc.h>
#include <stdio.h>
#include <stdint.h>


uint16_t arr[384*288];

static void 
prepare_buffer(GstAppSrc* appsrc) 
{

    static GstClockTime timestamp = 0;
    GstBuffer *buffer;
    guint size;
    GstFlowReturn ret;


    size = 384 * 288 * 2;
    buffer = gst_buffer_new_wrapped_full( 0, (gpointer)arr, size, 0, size, NULL, NULL );

    GST_BUFFER_PTS (buffer) = timestamp;
    GST_BUFFER_DURATION (buffer) = gst_util_uint64_scale_int (1, GST_SECOND, 4);

    timestamp += GST_BUFFER_DURATION (buffer);

    ret = gst_app_src_push_buffer(appsrc, buffer);

    if (ret != GST_FLOW_OK) {
        /* something wrong, stop pushing */
        // g_main_loop_quit (loop);
    }
}

static void 
cb_need_data (GstElement *appsrc, guint unused_size, gpointer u_data) 
{
    prepare_buffer((GstAppSrc*)appsrc);
}


static void 
print_caps (GstElement* ele) 
{
    GstCaps* caps;
    gchar* cap_str;
    g_object_get (G_OBJECT (ele), "caps", &caps, NULL);
    cap_str = gst_caps_to_string (caps);
    printf("%s\n", cap_str);
}


gint 
main (gint argc, gchar *argv[]) 
{

    GstElement *pipeline, *appsrc;
    GError *error = NULL;


    // Tune array to display a line 
    for (int x=0; x<288 ; x++) {
        for (int y=0; y<384; y++) {
            
            if (y == 1 * x + 0) {
                arr[x*384 + y] = 0xFFFF;
            } else {
                arr[x*384 + y] = 0;
            }
        }
    }


    /* init GStreamer */
    gst_init (&argc, &argv);
    
    gchar* desc =
        " appsrc                                                               "
        "     stream-type=0 format=time is-live=true name=source               "
        "     caps=video/x-raw,format=RGB16,width=384,height=288,framerate=0/1 "
        " ! videoconvert ! xvimagesink                                         ";

    pipeline = gst_parse_launch (desc, &error);
    if (error) {
        g_printerr ("pipeline parsing error: %s\n", error->message);
        g_error_free (error);
        return 1;
    }

    // Plug callbacks into appsrc
    appsrc = gst_bin_get_by_name (GST_BIN (pipeline), "source");
    g_assert (appsrc != NULL);
    g_signal_connect(appsrc, "need-data", G_CALLBACK(cb_need_data), NULL);
    gst_element_set_state (pipeline, GST_STATE_PLAYING);


    while (1) {
        prepare_buffer((GstAppSrc*) appsrc);
        g_main_context_iteration(g_main_context_default(),FALSE);
    }

    gst_element_set_state (pipeline, GST_STATE_NULL);
    gst_object_unref (GST_OBJECT (pipeline));

    return 0;
}
