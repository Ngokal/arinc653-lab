#include <algorithm>
#include <chrono>
#include <csignal>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <thread>
#include <vector>
#include <dlfcn.h>
#include <sched.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/wait.h>
#include <unistd.h>
extern "C" {
#include "lab.h"
#include "a653_i_shm_if.h"
extern a653_global_config_t global_config;
extern a653_channel_config_t channel_config[];
extern a653_partition_config_t partition_config[];
extern const char *modules[], *entries[];
extern int window_partition[], window_ms[], window_count;
extern int port_capacity[MAX_PARTITION][MAX_Q_PORT];
a653_shm_info_t *shm_ptr;
int a653_shm_init(void) { return 1; }
void setDebug(int) {}
void printDebug(int level, const char *fmt, ...) {
    if (level > 0) return;
    va_list args; va_start(args, fmt); vfprintf(stderr, fmt, args); va_end(args);
}
extern int own_partition_idx;
extern void initTime(void);
}
static int event_fd, own = -1;
static volatile sig_atomic_t stopping = 0;
static sem_t *gates;
static void (*application_worker)(void);
static std::string quote(const char *s) {
    std::string out = "\"";
    for (const unsigned char *p = (const unsigned char*)s; *p; ++p) {
        if (*p < 32 || *p >= 127) { char b[7]; snprintf(b,sizeof b,"\\u%04x",*p); out += b; }
        else { if (*p == '"' || *p == '\\') out += '\\'; out += *p; }
    }
    return out + "\"";
}
static void event(const char *type, const char *message, int partition, int code=0) {
    std::string line = "{\"event\":" + quote(type) + ",\"message\":" + quote(message)
        + ",\"partition_index\":" + std::to_string(partition) + ",\"code\":" + std::to_string(code)
        + ",\"pid\":" + std::to_string(getpid()) + "}\n";
    if (line.size() < 4096) { ssize_t ignored = write(event_fd,line.data(),line.size()); (void)ignored; }
}
extern "C" void lab_report(const char *type, const char *message) { event(type,message,own); }
extern "C" void lab_finish(int code) { _exit(code); }
extern "C" QUEUING_PORT_ID_TYPE lab_port(const char *name) {
    auto &pc = partition_config[own];
    for (int i=0;i<MAX_Q_PORT && pc.qp_config[i].ChannelId;i++) {
        auto &p=pc.qp_config[i];
        if (strcmp(p.name_str,name)) continue;
        for (int c=0;channel_config[c].ChannelId;c++) if(channel_config[c].ChannelId==p.ChannelId) {
            QUEUING_PORT_ID_TYPE id; RETURN_CODE_TYPE rc;
            CREATE_QUEUING_PORT(p.name_str,channel_config[c].maxMsgSize,port_capacity[own][i],
                                (PORT_DIRECTION_TYPE)p.Dir,FIFO,&id,&rc);
            if(rc!=NO_ERROR) _exit(23);
            event("port_created",name,own); return id;
        }
    }
    _exit(24);
}
static void gated_worker(void) {
    while (sem_wait(&gates[own]) && errno == EINTR) {}
    event("process_running","worker",own);
    application_worker();
    _exit(0);
}
extern "C" void lab_start(void (*worker)(void)) {
    application_worker=worker;
    PROCESS_ATTRIBUTE_TYPE a{};
    strcpy(a.NAME,"worker"); a.ENTRY_POINT=(SYSTEM_ADDRESS_TYPE)gated_worker;
    a.PERIOD=-1; a.TIME_CAPACITY=-1; a.BASE_PRIORITY=1; a.DEADLINE=SOFT;
    PROCESS_ID_TYPE id; RETURN_CODE_TYPE rc;
    CREATE_PROCESS(&a,&id,&rc); if(rc!=NO_ERROR) _exit(25);
    event("process_created","worker",own);
    START(id,&rc); if(rc!=NO_ERROR) _exit(26);
    event("partition_mode","NORMAL requested",own);
    SET_PARTITION_MODE(NORMAL,&rc);
    _exit(27);
}
static void signal_stop(int) { stopping=1; }
int main(int argc,char **argv) {
    pid_t controller=getppid();
    prctl(PR_SET_PDEATHSIG,SIGTERM);
    if(getppid()!=controller) return 41;
    event_fd=dup(STDOUT_FILENO); dup2(STDERR_FILENO,STDOUT_FILENO);
    signal(SIGTERM,signal_stop); signal(SIGINT,signal_stop);
    const int timeout_ms=argc>1?atoi(argv[1]):3000;
    shm_ptr=(a653_shm_info_t*)mmap(nullptr,sizeof(*shm_ptr),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);
    gates=(sem_t*)mmap(nullptr,sizeof(sem_t)*MAX_PARTITION,PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);
    if(shm_ptr==MAP_FAILED || gates==MAP_FAILED) return 30;
    cpu_set_t available; CPU_ZERO(&available);
    if(sched_getaffinity(0,sizeof available,&available)) return 31;
    int cpu=0; while(cpu<CPU_SETSIZE && !CPU_ISSET(cpu,&available)) ++cpu;
    cpu_set_t mask; CPU_ZERO(&mask); CPU_SET(cpu,&mask);
    if(sched_setaffinity(0,sizeof mask,&mask)) return 32;
    for(int c=0;c<MAX_CHANNEL;c++) shm_ptr->channel_info[c].Id=channel_config[c].ChannelId;
    std::vector<pid_t> children;
    std::vector<bool> alive(global_config.partition_number,true);
    int result=0;
    auto deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(timeout_ms);
    for(int i=0;i<global_config.partition_number;i++) {
        sem_init(&gates[i],1,0);
        auto &p=shm_ptr->partition_info[i]; p.init=1; p.running=1; sem_init(&p.sem_lock,1,0);
        pid_t parent_pid=getpid();
        pid_t pid=fork();
        if(pid<0) { result=33; break; }
        if(pid==0) {
            signal(SIGTERM,SIG_DFL); signal(SIGINT,SIG_DFL);
            prctl(PR_SET_PDEATHSIG,SIGKILL);
            if(getppid()!=parent_pid) _exit(34);
            own=i;
            while(!shm_ptr->partition_info[i].pid) usleep(100);
            a653_init_partition(); initTime();
            void *module=dlopen(modules[i],RTLD_NOW|RTLD_LOCAL);
            if(!module) { fprintf(stderr,"%s\n",dlerror()); _exit(35); }
            auto entry=(void(*)(void))dlsym(module,entries[i]); if(!entry) _exit(36);
            entry(); _exit(37);
        }
        children.push_back(pid); p.pid=pid;
        event("partition_started",partition_config[i].name_str,i,(int)pid);
    }
    // Initialize all ports before any worker is released (receiver creates the FIFO).
    bool ready=false;
    while(!stopping && !result && !ready && std::chrono::steady_clock::now()<deadline) {
        ready=true;
        for(size_t i=0;i<children.size();i++) {
            int status; if(waitpid(children[i],&status,WNOHANG)>0) {
                alive[i]=false; event("partition_exit","initialization failure",i,WIFEXITED(status)?WEXITSTATUS(status):128+WTERMSIG(status)); result=38;
            }
            if(shm_ptr->partition_info[i].init) ready=false;
        }
        usleep(1000);
    }
    for(size_t i=0;i<children.size();i++) if(alive[i]) { kill(children[i],SIGSTOP); int s; waitpid(children[i],&s,WUNTRACED); }
    while(!stopping && !result && ready && std::chrono::steady_clock::now()<deadline
          && std::any_of(alive.begin(),alive.end(),[](bool v){return v;})) {
        for(int w=0;w<window_count && !stopping && !result;w++) {
            int i=window_partition[w];
            auto until=std::chrono::steady_clock::now()+std::chrono::milliseconds(window_ms[w]);
            if(!alive[i]) {
                while(!stopping && std::chrono::steady_clock::now()<std::min(until,deadline)) usleep(1000);
                continue;
            }
            event("window_open","host scheduler",i);
            sem_post(&gates[i]); sem_post(&shm_ptr->partition_info[i].sem_lock); kill(children[i],SIGCONT);
            while(!stopping && std::chrono::steady_clock::now()<std::min(until,deadline)) {
                int s; if(alive[i] && waitpid(children[i],&s,WNOHANG)>0) {
                    alive[i]=false; int code=WIFEXITED(s)?WEXITSTATUS(s):128+WTERMSIG(s);
                    event("partition_exit","worker exited",i,code); if(code) result=39;
                    if(result) break;
                }
                usleep(1000);
            }
            if(alive[i]) { kill(children[i],SIGSTOP); int s; waitpid(children[i],&s,WUNTRACED); }
            event("window_closed","SIGSTOP acknowledged or process exited",i);
            if(std::chrono::steady_clock::now()>=deadline) break;
        }
    }
    bool timed_out=std::any_of(alive.begin(),alive.end(),[](bool v){return v;}) && !stopping && !result;
    if(timed_out) { event("timeout","run deadline exceeded",-1); result=40; }
    for(size_t i=0;i<children.size();i++) if(alive[i]) { kill(children[i],SIGKILL); int s; waitpid(children[i],&s,0); event("partition_cleaned","reaped",i); }
    event("run_finished",stopping?"stopped":"completed",-1,result);
    return result;
}
