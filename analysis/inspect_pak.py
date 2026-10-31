"""Read-only inspector for this supplied unencrypted Unreal v11 pak.

Only handles the observed zlib/uncompressed compact-entry layout. It writes
inventories and string evidence, never extracted executable content.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import zlib


class Reader:
    def __init__(self, data, pos=0):
        self.data, self.pos = data, pos

    def read(self, fmt):
        result = struct.unpack_from('<' + fmt, self.data, self.pos)
        self.pos += struct.calcsize('<' + fmt)
        return result[0] if len(result) == 1 else result

    def string(self):
        size = self.read('i')
        assert 0 < size < 100000
        value = self.data[self.pos:self.pos + size - 1].decode('utf-8')
        self.pos += size
        return value


class Pak:
    def __init__(self, path):
        self.data = Path(path).read_bytes()
        footer = self.data.rfind(bytes.fromhex('e1126f5a'))
        magic, self.version, index, size = struct.unpack_from('<IIqq', self.data, footer)
        assert self.version == 11
        r = Reader(self.data, index)
        self.mount = r.string()
        self.count = r.read('i')
        r.read('Q')
        assert r.read('I') == 1
        r.read('qq')
        r.pos += 20
        assert r.read('I') == 1
        directory_offset, directory_size = r.read('qq')
        r.pos += 20
        encoded_size = r.read('i')
        self.encoded = self.data[r.pos:r.pos + encoded_size]
        r = Reader(self.data, directory_offset)
        self.files = {}
        for _ in range(r.read('i')):
            directory = r.string()
            for _ in range(r.read('i')):
                name, entry = r.string(), r.read('i')
                self.files[directory + name] = entry
        assert len(self.files) == self.count

    def content(self, name):
        r = Reader(self.encoded, self.files[name])
        bits = r.read('I')
        offset = r.read('I' if bits & (1 << 31) else 'Q')
        raw_size = r.read('I' if bits & (1 << 30) else 'Q')
        method = (bits >> 23) & 0x3f
        stored_size = raw_size if method == 0 else r.read('I' if bits & (1 << 29) else 'Q')
        assert not bits & (1 << 22), 'encrypted member unsupported'
        block_count = (bits >> 6) & 0xffff
        # Read the full on-disk member header for exact block positions.
        full = Reader(self.data, offset)
        header_offset, header_stored_size, header_raw_size, header_method = full.read('qqqI')
        assert (header_stored_size, header_raw_size, header_method) == (stored_size, raw_size, method)
        expected_hash = self.data[full.pos:full.pos + 20]
        full.pos += 20
        blocks = []
        if method:
            assert full.read('i') == block_count
            blocks = [full.read('qq') for _ in range(block_count)]
        flags, block_size = full.read('BI')
        assert not flags & 1
        if not method:
            result = self.data[full.pos:full.pos + raw_size]
            stored = result
        else:
            assert method == 1, 'only observed zlib supported'
            chunks = [self.data[offset + start:offset + end] for start, end in blocks]
            stored = b''.join(chunks)
            result = b''.join(zlib.decompress(chunk) for chunk in chunks)
        assert hashlib.sha1(stored).digest() == expected_hash
        assert len(result) == raw_size
        return result


def strings(data):
    ascii_values = [x.decode('ascii') for x in re.findall(rb'[ -~]{5,}', data)]
    wide_values = [x.decode('utf-16le') for x in re.findall(rb'(?:[ -~]\x00){5,}', data)]
    return sorted(set(ascii_values + wide_values))


def defaults(pak, asset, actor_nodes=False):
    """Decode tagged class-default-object scalar properties for this build.

    This does not execute or decompile Blueprint bytecode; inherited defaults
    absent from a child asset remain unknown.
    """
    data = pak.content(asset)
    assert data[:8] == bytes.fromhex('c1832a9ef9ffffff')
    assert data[28:37] == b'\x05\x00\x00\x00None\x00'
    name_count, name_offset = struct.unpack_from('<ii', data, 41)
    names = []
    r = Reader(data, name_offset)
    for _ in range(name_count):
        names.append(r.string())
        r.pos += 4
    export_count, export_offset = struct.unpack_from('<ii', data, 57)
    export_data = pak.content(asset.rsplit('.', 1)[0] + '.uexp')
    export_names = [names[struct.unpack_from('<i', data, export_offset + i * 104 + 16)[0]] for i in range(export_count)]
    result = {}
    for i in range(export_count):
        position = export_offset + i * 104
        name = names[struct.unpack_from('<i', data, position + 16)[0]]
        if not name.startswith('Node' if actor_nodes else 'Default__'):
            continue
        size, offset = struct.unpack_from('<qq', data, position + 28)
        body = export_data[offset - len(data):offset - len(data) + size]
        r = Reader(body)
        props = {}
        while r.pos < len(body):
            name_index, number = r.read('ii')
            prop_name = names[name_index]
            if prop_name == 'None':
                break
            type_index, type_number = r.read('ii')
            prop_type = names[type_index]
            value_size, array_index = r.read('ii')
            record = {'type': prop_type, 'body_offset': r.pos - 24}
            if prop_type == 'StructProperty':
                type_name, _ = r.read('ii')
                record['struct'] = names[type_name]
                r.pos += 16
            if prop_type in ('ArrayProperty', 'ByteProperty', 'EnumProperty'):
                inner_name, _ = r.read('ii')
                record['inner_type'] = names[inner_name]
            if prop_type == 'BoolProperty':
                record['value'] = bool(r.read('B'))
            assert r.read('B') == 0, 'property GUID unsupported'
            raw = body[r.pos:r.pos + value_size]
            r.pos += value_size
            if prop_type == 'FloatProperty' and value_size == 4:
                record['value'] = struct.unpack('<f', raw)[0]
            elif prop_type in ('IntProperty', 'ObjectProperty') and value_size == 4:
                record['value'] = struct.unpack('<i', raw)[0]
            elif prop_type == 'ArrayProperty' and record['inner_type'] == 'IntProperty':
                count = struct.unpack_from('<i', raw)[0]
                assert len(raw) == 4 + count * 4
                record['value'] = list(struct.unpack_from('<' + 'i' * count, raw, 4))
            elif prop_type == 'ArrayProperty' and record['inner_type'] == 'ObjectProperty':
                count = struct.unpack_from('<i', raw)[0]
                assert len(raw) == 4 + count * 4
                refs = struct.unpack_from('<' + 'i' * count, raw, 4)
                record['value'] = [export_names[x - 1] if x > 0 else {'import_or_null_index': x} for x in refs]
            elif prop_type == 'StrProperty':
                record['value'] = Reader(raw).string()
            elif prop_type != 'BoolProperty':
                record['raw_hex'] = raw.hex()
            props[prop_name] = record
        result[name] = props
    return result


if __name__ == '__main__':
    root = Path(__file__).resolve().parent.parent
    source = root / 'LOOP ARCHER/GMTK2025/Content/Paks/GMTK2025-WindowsNoEditor.pak'
    pak = Pak(source)
    out = root / 'analysis'
    (out / 'pak_inventory.json').write_text(json.dumps({'source': str(source), 'sha256': hashlib.sha256(pak.data).hexdigest(), 'version': pak.version, 'files': pak.files}, indent=2), encoding='utf-8')
    evidence = {}
    for name in pak.files:
        if name.startswith('GMTK2025/') and (name.endswith('.ini') or name.endswith(('.uasset', '.uexp'))):
            data = pak.content(name)
            evidence[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'strings': strings(data)}
    (out / 'gameplay_strings.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    decoded = {}
    for name in pak.files:
        if name.endswith('.uasset') and any(x in name for x in ('/Nodes/NodeBase.', '/Nodes/Nodes/', '/Player/BP/Player.', '/Player/BP/MyGameInstance.', '/Arrow/Arrow.', '/WaveManager/', '/Enemies/BP/')):
            try:
                decoded[name] = defaults(pak, name)
            except (AssertionError, IndexError, struct.error) as error:
                decoded[name] = {'unresolved': str(error)}
    (out / 'gameplay_defaults.json').write_text(json.dumps(decoded, indent=2), encoding='utf-8')
    nodes = defaults(pak, 'GMTK2025/Content/Maps/SkillTreeMap.umap', actor_nodes=True)
    (out / 'skill_tree_defaults.json').write_text(json.dumps(nodes, indent=2), encoding='utf-8')
    print(f'Inventoried {len(pak.files)} files; decoded strings from {len(evidence)} project config/asset files.')
    for name in evidence:
        if name.endswith('DefaultInput.ini') or ('Nodes/Nodes/' in name and name.endswith('.uexp')) or ('Tutorial' in name and name.endswith('.uexp')):
            print('\n' + name)
            print('\n'.join(evidence[name]['strings']))
