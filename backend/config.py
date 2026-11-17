"""Strict schema-1 loader and a653lib native configuration adapter."""
import json
import re
from pathlib import Path

PROFILE = 'a653lib-native-host-v1'

def obj(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError(f'Expected exactly fields: {keys}')

def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'Expected integer in {low}..{high}: {value!r}')

def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,24}', value):
        raise ValueError(f'Invalid identifier: {value!r}')

def load(path):
    path = Path(path).resolve()
    def read(file):
        target = (path.parent / file).resolve()
        if not target.is_relative_to(path.parent):
            raise ValueError('Configuration path escapes project directory')
        return json.loads(target.read_text())
    m = json.loads(path.read_text())
    obj(m, 'schema_version behavior_profile kernel partitions connections')
    if type(m['schema_version']) is not int or m['schema_version'] != 1 or m['behavior_profile'] != PROFILE:
        raise ValueError('Unsupported schema or behavior profile')
    k, parts, ports = read(m['kernel']), read(m['partitions']), read(m['connections'])
    obj(k, 'major_frame_ms windows limits')
    obj(k['limits'], 'max_partitions')
    integer(k['limits']['max_partitions'], 1, 10)
    integer(k['major_frame_ms'], 1, 10000)
    if not isinstance(parts, list) or not 1 <= len(parts) <= k['limits']['max_partitions']:
        raise ValueError('Invalid partition count')
    ids, targets = set(), set()
    for p in parts:
        obj(p, 'id name sources build_target entry_point address_space limits')
        for key in ('id', 'name', 'build_target', 'entry_point', 'address_space'):
            identifier(p[key])
        if p['id'] in ids or p['build_target'] in targets:
            raise ValueError('Duplicate partition ID or build target')
        ids.add(p['id']); targets.add(p['build_target'])
        obj(p['limits'], 'max_processes')
        # This profile exposes a single worker. It does not enforce arbitrary upstream limits.
        if p['limits']['max_processes'] != 1:
            raise ValueError('Profile requires one application worker per partition')
        if not p['sources'] or not isinstance(p['sources'], list):
            raise ValueError('Expected nonempty C source list')
        for source in p['sources']:
            resolved = (path.parent / source).resolve()
            if not resolved.is_relative_to(path.parent) or resolved.suffix != '.c' or not resolved.is_file():
                raise ValueError('Invalid C source path')
    if len({p['address_space'] for p in parts}) != len(parts):
        raise ValueError('Each partition requires its own logical address space')
    if not isinstance(k['windows'], list) or not k['windows']:
        raise ValueError('Expected execution windows')
    total = 0
    for w in k['windows']:
        obj(w, 'partition duration_ms')
        if w['partition'] not in ids: raise ValueError('Unknown window partition')
        integer(w['duration_ms'], 1, 10000); total += w['duration_ms']
    if total != k['major_frame_ms'] or {w['partition'] for w in k['windows']} != ids:
        raise ValueError('Windows must cover frame and every partition')
    obj(ports, 'ports channels')
    endpoints = {}
    counts = {p: 0 for p in ids}
    for port in ports['ports']:
        obj(port, 'partition name type direction')
        identifier(port['name'])
        key = (port['partition'], port['name'])
        if key in endpoints or port['partition'] not in ids: raise ValueError('Invalid port identity')
        if port['type'] != 'queuing' or port['direction'] not in ('source', 'destination'):
            raise ValueError('Only queuing source/destination ports supported')
        counts[port['partition']] += 1
        if counts[port['partition']] > 44: raise ValueError('Too many ports')
        endpoints[key] = port
    if not 1 <= len(ports['channels']) <= 59: raise ValueError('Invalid channel count')
    used, channel_ids = set(), set()
    for c in ports['channels']:
        obj(c, 'id source destination message_size queue_capacity')
        identifier(c['id'])
        if c['id'] in channel_ids: raise ValueError('Duplicate channel ID')
        channel_ids.add(c['id'])
        integer(c['message_size'], 1, 1500); integer(c['queue_capacity'], 1, 40)
        for side in ('source', 'destination'):
            e = c[side]; obj(e, 'partition port'); key = (e['partition'], e['port'])
            if key not in endpoints or key in used or endpoints[key]['direction'] != side:
                raise ValueError('Invalid channel connection')
            used.add(key)
        if c['source']['partition'] == c['destination']['partition']: raise ValueError('Expected inter-partition channel')
    if used != set(endpoints): raise ValueError('Every port must have one channel')
    return path.parent, k, parts, ports

def generate(project, build):
    root, kernel, parts, ports = load(project)
    build.mkdir(parents=True, exist_ok=True)
    q = json.dumps
    lines = ['#include "a653Init.h"', 'a653_global_config_t global_config = {.core_number=1, .partition_number=%d, .time_slice_size=1000000};' % len(parts)]
    channels = ports['channels']
    lines += ['a653_channel_config_t channel_config[MAX_CHANNEL] = {' + ','.join('{%d,2,%d}' % (i+1,c['message_size']) for i,c in enumerate(channels)) + '};']
    pc, capacities = [], []
    for p in parts:
        plist, caps = [], []
        for port in ports['ports']:
            if port['partition'] != p['id']: continue
            side = port['direction']; endpoint={'partition':p['id'],'port':port['name']}
            ci,c = next((i,c) for i,c in enumerate(channels) if c[side]==endpoint)
            plist.append('{%d,%s,2,%s}' % (ci+1, 'SOURCE' if side=='source' else 'DESTINATION',q(port['name'])))
            caps.append(str(c['queue_capacity']))
        pc.append('{%d,%s,{{0}},{%s}}' % (len(pc)+1,q(p['name']),','.join(plist)))
        capacities.append('{'+','.join(caps)+'}')
    lines += ['a653_partition_config_t partition_config[MAX_PARTITION] = {'+','.join(pc)+'};',
              'int port_capacity[MAX_PARTITION][MAX_Q_PORT] = {'+','.join(capacities)+'};',
              'const char *modules[] = {'+','.join(q(str(build / ('lib'+p['build_target']+'.so'))) for p in parts)+'};',
              'const char *entries[] = {'+','.join(q(p['entry_point']) for p in parts)+'};',
              'int window_partition[] = {'+','.join(str(next(i for i,p in enumerate(parts) if p['id']==w['partition'])) for w in kernel['windows'])+'};',
              'int window_ms[] = {'+','.join(str(w['duration_ms']) for w in kernel['windows'])+'};',
              'int window_count = %d;' % len(kernel['windows'])]
    (build/'config.c').write_text('\n'.join(lines)+'\n')
    cm = []
    for p in parts:
        # Quoted literal paths; reject CMake interpolation syntax in paths.
        sources = [str(root/s) for s in p['sources']]
        if any(any(x in s for x in (';', '$', '"', '\\', '\n')) for s in sources):
            raise ValueError('Path contains unsupported CMake characters')
        t = p['build_target']
        cm += [f'add_library({t} MODULE '+ ' '.join('"'+s+'"' for s in sources)+')', f'target_include_directories({t} PRIVATE "${{CMAKE_SOURCE_DIR}}/backend" "${{V}}/a653_inc")']
    (build/'partitions.cmake').write_text('\n'.join(cm)+'\n')
