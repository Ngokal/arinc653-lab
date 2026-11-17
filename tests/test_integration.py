"""Real C builds and bounded Linux integration experiments; no mock APEX."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, str(ROOT/'backend/cli.py')]

class PrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='arinc test ')
        cls.root = Path(cls.temp.name)
        cls.example = cls.root/'project'
        shutil.copytree(ROOT/'examples/two-partitions', cls.example)
        cls.build = cls.root/'build'
        cls.args = ['--project',str(cls.example/'project.json'),'--build-dir',str(cls.build)]
        cls.compile()

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    @classmethod
    def compile(cls):
        r = subprocess.run(CLI+['build']+cls.args,capture_output=True,text=True,timeout=60)
        if r.returncode: raise AssertionError(r.stderr)
        return r

    def run_example(self, timeout=1000):
        r=subprocess.run(CLI+['run']+self.args+['--timeout-ms',str(timeout)],capture_output=True,text=True,timeout=8)
        events=[json.loads(line) for line in r.stdout.splitlines()]
        self.assertTrue(events)
        self.assertTrue(all(e['schema_version']==1 and e['clock']=='host_monotonic' for e in events))
        for e in events:
            if e['event']=='partition_started':
                self.assertFalse(Path('/proc') .joinpath(str(e['code'])).exists(), 'partition leaked')
        return r,events

    def test_delivery_and_repeatability(self):
        for _ in range(3):
            r,events=self.run_example()
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual([e['message'] for e in events if e['event']=='message_received'],['Hello from partition A'])

    def test_source_edit_rebuild(self):
        p=self.example/'partition_a.c'; original=p.read_text()
        try:
            p.write_text(original.replace('Hello from partition A','Edited C message'))
            self.compile()
            r,events=self.run_example()
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual([e['message'] for e in events if e['event']=='message_received'],['Edited C message'])
        finally: p.write_text(original); self.compile()

    def test_failure_and_loop_cleanup(self):
        p=self.example/'partition_a.c'; original=p.read_text()
        try:
            for body,expected in [('lab_finish(7);', 'partition_exit'),('raise(11);', 'partition_exit'),('for (;;) { }','timeout')]:
                p.write_text('#include <signal.h>\n'+original.replace('char message[]', body+'\n    char message[]'))
                self.compile()
                r,events=self.run_example(250)
                self.assertNotEqual(r.returncode,0)
                self.assertIn(expected,[e['event'] for e in events])
                if expected=='partition_exit': self.assertTrue(any(e['event']=='partition_exit' and e['code']==(139 if 'raise' in body else 7) for e in events))
                else:
                    self.assertGreaterEqual(sum(e['event']=='window_closed' and e['partition_index']==0 for e in events),2)
                    proc=subprocess.Popen(CLI+['run']+self.args+['--timeout-ms','500'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                    sender=None; observed=False
                    try:
                        for line in proc.stdout:
                            event=json.loads(line)
                            if event['event']=='partition_started' and event['partition_index']==0: sender=event['code']
                            if event['event']=='window_open' and event['partition_index']==1:
                                state=Path(f'/proc/{sender}/status').read_text()
                                self.assertIn('T (stopped)',state); observed=True; break
                        self.assertTrue(observed)
                        proc.communicate(timeout=5)
                    finally:
                        if proc.poll() is None: proc.kill(); proc.wait()
                        proc.stdout.close(); proc.stderr.close()
        finally: p.write_text(original); self.compile()

    def test_invalid_configuration(self):
        p=self.example/'kernel.json'; original=p.read_text()
        cases=[dict(json.loads(original), unknown=True),dict(json.loads(original),major_frame_ms=99)]
        try:
            for case in cases:
                p.write_text(json.dumps(case))
                r=subprocess.run(CLI+['validate']+self.args,capture_output=True,text=True)
                self.assertNotEqual(r.returncode,0)
                self.assertEqual(json.loads(r.stdout)['event'],'error')
        finally: p.write_text(original)

    def test_third_partition(self):
        manifest=self.example/'partitions.json'; kernel=self.example/'kernel.json'
        original, original_kernel=manifest.read_text(), kernel.read_text()
        try:
            parts=json.loads(original)
            parts.append(dict(id='C',name='Observer',sources=['partition_c.c'],build_target='partition_c',entry_point='partition_init',address_space='space_C',limits=dict(max_processes=1)))
            (self.example/'partition_c.c').write_text('#include "lab.h"\nstatic void worker(void) { lab_report("observer", "third partition"); lab_finish(0); }\nvoid partition_init(void) { lab_start(worker); }\n')
            manifest.write_text(json.dumps(parts))
            k=json.loads(original_kernel); k['major_frame_ms']=60; k['windows'].append(dict(partition='C',duration_ms=20)); kernel.write_text(json.dumps(k))
            self.compile()
            r,events=self.run_example()
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(sum(e['event']=='partition_started' for e in events),3)
            self.assertTrue(any(e['event']=='observer' and e['partition_index']==2 for e in events))
            self.assertTrue(any(e['event']=='message_received' for e in events))
        finally:
            manifest.write_text(original); kernel.write_text(original_kernel)
            (self.example/'partition_c.c').unlink(missing_ok=True)
            self.compile()

    def test_protocol_start_stop_and_unsupported(self):
        p=subprocess.Popen(CLI+['serve']+self.args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.assertEqual(json.loads(p.stdout.readline())['event'],'backend_ready')
        def command(name, ident):
            p.stdin.write(json.dumps(dict(schema_version=1,id=ident,command=name))+'\n'); p.stdin.flush()
            while True:
                e=json.loads(p.stdout.readline())
                if e['event']=='command_result' and e['id']==ident: return e
        try:
            self.assertFalse(command('pause',1)['ok'])
            self.assertFalse(command('step',2)['ok'])
            self.assertTrue(command('start',3)['ok'])
            self.assertTrue(command('stop',4)['ok'])
            self.assertFalse(command('status',5)['running'])
            self.assertTrue(command('start',6)['ok'])
            self.assertTrue(command('shutdown',7)['ok'])
            self.assertEqual(p.wait(timeout=5),0)
        finally:
            if p.poll() is None: p.kill(); p.wait()
            p.stdin.close(); p.stdout.close(); p.stderr.close()

if __name__=='__main__': unittest.main(verbosity=2)
