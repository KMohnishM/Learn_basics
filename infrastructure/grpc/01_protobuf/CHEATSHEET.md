# Protobuf v3 Cheatsheet

## Scalar Types & Wire Types

| Type | Wire Type | Typical Use Case | Characteristics |
|------|-----------|------------------|-----------------|
| `double` | 1 (64-bit) | Precision math | Fixed 8 bytes. |
| `float` | 5 (32-bit) | Graphics, general math | Fixed 4 bytes. |
| `int32` | 0 (Varint) | Standard ints | 1-5 bytes. Inefficient for negatives. |
| `int64` | 0 (Varint) | Large ints | 1-10 bytes. Inefficient for negatives. |
| `uint32` | 0 (Varint) | Unsigned standard | 1-5 bytes. |
| `uint64` | 0 (Varint) | Unsigned large | 1-10 bytes. |
| `sint32` | 0 (Varint) | Negative ints | Zigzag encoding. Highly efficient. |
| `sint64` | 0 (Varint) | Negative large ints| Zigzag encoding. Highly efficient. |
| `fixed32` | 5 (32-bit) | Big numbers > 2^28 | Always exactly 4 bytes. |
| `fixed64` | 1 (64-bit) | Big numbers > 2^56 | Always exactly 8 bytes. |
| `sfixed32`| 5 (32-bit) | Signed fixed | Always exactly 4 bytes. |
| `sfixed64`| 1 (64-bit) | Signed fixed | Always exactly 8 bytes. |
| `bool` | 0 (Varint) | Flags | True/False. Always 1 byte. |
| `string` | 2 (Length-delim)| Text | Must be UTF-8 or 7-bit ASCII. |
| `bytes` | 2 (Length-delim)| Binary data | Images, files, crypto payloads. |

---

## Wire Format Architecture (ASCII)

**Formula for Tag:** `(field_number << 3) | wire_type`

```text
Message Example:
{ "id": 150 } (where id is field_number 1, type int32)

[  TAG BYTE  ]  [   VARINT VALUE BYTE 1   ]  [   VARINT VALUE BYTE 2   ]
  0 0 0 0 1 0 0 0    1 0 0 1 0 1 1 0            0 0 0 0 0 0 0 1
  |___| |___|      | |___________|            | |___________|
    |     |        |      |                   |       |
  Field Wire     Cont.  Lower 7 bits        Cont.   Next 7 bits
 Num=1 Type=0   Bit=1  (0010110)           Bit=0   (0000001)

Tag = (1 << 3) | 0 = 8 (Binary: 00001000)
Value = Little Endian Varint decoding:
        (0000001 << 7) | 0010110 = 10000000 | 0010110 = 10010110 (Decimal: 150)
```

---

## Schema Evolution Checklist

- [ ] **Rule 1:** NEVER change an existing field number.
- [ ] **Rule 2:** NEVER change an existing field type.
- [ ] **Rule 3:** NEVER reuse a field number or name. ALWAYS use `reserved`.
- [ ] **Rule 4:** ALWAYS default values logically. (Remember proto3 sets
default to `0`, `""`, `false`).
- [ ] **Rule 5:** Field numbers `1-15` take 1 byte. Use them for high-
frequency fields.
- [ ] **Rule 6:** Add `optional` to primitive types only if you explicitly
need to track null/missing presence.

```protobuf
// Example of Safe Deletion
message Profile {
  reserved 3, 5 to 7;
  reserved "old_email", "legacy_token";

  string id = 1;
  string username = 2;
}
```

---

## CLI Commands Reference

### Python Compilation (grpcio-tools)
```bash
python -m grpc_tools.protoc \
    -I=./protos \
    --python_out=./out \
    --pyi_out=./out \
    --grpc_python_out=./out \
    ./protos/service.proto
```

### Go Compilation (protoc-gen-go)
```bash
protoc \
    --proto_path=./protos \
    --go_out=./out --go_opt=paths=source_relative \
    --go-grpc_out=./out --go-grpc_opt=paths=source_relative \
    ./protos/service.proto
```

### Buf Toolchain
```bash
buf lint                          # Enforce style guidelines
buf generate                      # Generate code based on buf.gen.yaml
buf format -w                     # Auto-format proto files
buf breaking --against .git#branch=main  # Prevent backward-incompatible changes
```