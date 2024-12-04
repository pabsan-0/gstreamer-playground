// gcc --std=c99 -Wall $(pkg-config --cflags gstreamer-1.0) $(pkg-config --libs gstreamer-1.0) -lgstapp-1.0 -o gst-boilerplate gst-boilerplate.c

#include <gst/gst.h>

static gboolean
bus_callback (GstBus *bus, GstMessage *message, gpointer u_data)
{
    GMainLoop *loop = (GMainLoop *) u_data;

    g_print ("Got %s message\n", GST_MESSAGE_TYPE_NAME (message));

    switch (GST_MESSAGE_TYPE (message)) {
        case GST_MESSAGE_ERROR:{
            GError *err;
            gchar *debug;

            gst_message_parse_error (message, &err, &debug);
            g_print ("Error: %s\n", err->message);
            g_error_free (err);
            g_free (debug);

            g_main_loop_quit (loop);
            break;
        }
        case GST_MESSAGE_EOS:
            g_main_loop_quit (loop);
            break;
        default:
            break;
    }

    return TRUE;
}

gint 
main (gint argc, gchar *argv[]) 
{
    GstElement *pipeline;
    GError *error = NULL;
    GMainLoop *loop = NULL;
    GstBus *bus;
    guint bus_watch_id;

    gst_init (&argc, &argv);

    gchar* desc = \
        " videotestsrc pattern=ball motion=sweep is-live=true                 "
        "     ! videoconvert                                                  "
        "     ! video/x-raw,format=I420,width=640,height=640,framerate=30/1   "
        "     ! fpsdisplaysink                                                "
        ;;;;;;;;;;

    pipeline = gst_parse_launch (desc, &error);
    if (error) {
        g_printerr ("pipeline parsing error: %s\n", error->message);
        g_error_free (error);
        return 1;
    }

    bus = gst_pipeline_get_bus (GST_PIPELINE (pipeline));
    bus_watch_id = gst_bus_add_watch (bus, bus_callback, NULL);
    gst_object_unref (bus);

    gst_element_set_state (pipeline, GST_STATE_PLAYING);
    loop = g_main_loop_new (NULL, FALSE);
    g_main_loop_run (loop);

    gst_element_set_state (pipeline, GST_STATE_NULL);
    gst_object_unref (GST_OBJECT (pipeline));
    g_source_remove (bus_watch_id);
    g_main_loop_unref (loop);

    return 0;
}
