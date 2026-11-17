#include "lab.h"
#include <unistd.h>
static QUEUING_PORT_ID_TYPE input;
static void worker(void) {
    char message[1501] = {0};
    MESSAGE_SIZE_TYPE length = 0;
    RETURN_CODE_TYPE rc;
    for (;;) {
        RECEIVE_QUEUING_MESSAGE(input, 0, message, &length, &rc);
        if (rc == NO_ERROR) {
            message[length] = 0;
            lab_report("message_received", message);
            lab_finish(0);
        }
        if (rc != NO_ACTION) lab_finish(22);
        usleep(1000); /* Host-time polling; upstream timeout is not implemented. */
    }
}
void partition_init(void) {
    input = lab_port("in");
    lab_start(worker);
}
