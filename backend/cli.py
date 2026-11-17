#!/usr/bin/env python3
"""Linux CLI and schema-1 JSON Lines command server."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from config import generate, load

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.Lock()

def emit(event, **fields):
    with LOCK:
        print(json.dumps(dict(schema_version=1, clock='host_monotonic', host_time_ns=time.monotonic_ns(), event=event, **fields)), flush=True)

def build(project, directory):
    generate(project, directory)
    subprocess.run(['cmake', '-S', str(ROOT), '-B', str(directory)], check=True, stdout=sys.stderr)
    subprocess.run(['cmake', '--build', str(directory), '-j', '2'], check=True, stdout=sys.stderr)
    (directory/'project-path.txt').write_text(str(project.resolve()))

class Controller:
    def __init__(self, directory, timeout):
        self.directory, self.timeout = directory, timeout
        self.child = None
        self.thread = None
        self.code = 0

    def start(self):
        if self.thread and self.thread.is_alive(): raise ValueError('Run already active')
        if not (self.directory/'lab_runner').is_file(): raise ValueError('Build first')
        self.child = subprocess.Popen([str(self.directory/'lab_runner'), str(self.timeout)], stdout=subprocess.PIPE, text=True, start_new_session=True)
        def monitor():
            try:
                for line in self.child.stdout:
                    item = json.loads(line)
                    emit(item.pop('event'), **item)
            except Exception as exc:
                emit('error', message=str(exc))
                self.stop()
            finally:
                self.code = self.child.wait()
                emit('backend_exit', code=self.code)
        self.thread = threading.Thread(target=monitor)
        self.thread.start()

    def stop(self):
        if self.child and self.child.poll() is None:
            self.child.send_signal(signal.SIGTERM)
            try: self.child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(self.child.pid, signal.SIGKILL)
                self.child.wait()
        if self.thread and self.thread is not threading.current_thread(): self.thread.join(timeout=3)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('command',choices=['validate','build','run','serve'])
    ap.add_argument('--project',type=Path,default=ROOT/'examples/two-partitions/project.json')
    ap.add_argument('--build-dir',type=Path,default=ROOT/'build')
    ap.add_argument('--timeout-ms',type=int,default=3000)
    a=ap.parse_args(); directory=a.build_dir.resolve()
    if not 100 <= a.timeout_ms <= 60000: raise ValueError('timeout must be 100..60000 ms')
    load(a.project)
    if a.command=='validate': emit('config_valid'); return 0
    if a.command=='build': build(a.project,directory); emit('build_complete'); return 0
    if not (directory/'project-path.txt').is_file() or (directory/'project-path.txt').read_text()!=str(a.project.resolve()):
        raise ValueError('Build this project first')
    ctl=Controller(directory,a.timeout_ms)
    signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        if a.command=='run':
            ctl.start(); ctl.thread.join(); return ctl.code
        emit('backend_ready',commands=['start','stop','status','shutdown'])
        for line in sys.stdin:
            request_id=None
            try:
                cmd=json.loads(line)
                request_id=cmd.get('id')
                if set(cmd)!= {'schema_version','id','command'} or type(cmd['schema_version']) is not int or cmd['schema_version']!=1:
                    raise ValueError('Expected schema_version=1, id, command')
                name=cmd['command']
                if name=='start': ctl.start()
                elif name=='stop': ctl.stop()
                elif name=='status': pass
                elif name=='shutdown': ctl.stop(); emit('command_result',id=request_id,ok=True); break
                else: raise ValueError('Unsupported command: '+str(name))
                emit('command_result',id=request_id,ok=True,running=ctl.child is not None and ctl.child.poll() is None)
            except (ValueError, TypeError, AttributeError) as exc: emit('command_result',id=request_id,ok=False,error=str(exc))
        return 0
    finally: ctl.stop()

if __name__=='__main__':
    try: sys.exit(main())
    except KeyboardInterrupt: sys.exit(130)
    except (ValueError, TypeError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        emit('error',message=str(exc)); print(str(exc),file=sys.stderr); sys.exit(1)
