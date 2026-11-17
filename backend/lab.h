#pragma once
#include "a653Process.h"
#include "a653Partition.h"
#include "a653Queuing.h"
#include "a653Time.h"
#ifdef __cplusplus
extern "C" {
#endif
QUEUING_PORT_ID_TYPE lab_port(const char *name);
void lab_start(void (*worker)(void));
void lab_report(const char *event, const char *message);
void lab_finish(int code);
#ifdef __cplusplus
}
#endif
