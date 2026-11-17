#include "lab.h"
#include <string.h>
static QUEUING_PORT_ID_TYPE output;
static void worker(void) {
    char message[] = "Hello from partition A";
    RETURN_CODE_TYPE rc;
    SEND_QUEUING_MESSAGE(output, message, strlen(message), 0, &rc);
    if (rc != NO_ERROR) lab_finish(21);
    lab_report("message_sent", message);
    lab_finish(0);
}
void partition_init(void) {
    output = lab_port("out");
    lab_start(worker);
}
