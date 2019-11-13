#!/usr/bin/env python3

#TOPSEE camera firmware unpacker with encrypted ROM support

# @Topsee: Your firmware is a total mess... Bugs and security holes throughout.
# Command line injection, instant root access with default password, outdated TI SDK.
# Stop encrypting it -- nobody is going to steal such a mess and if
# somebody tries, they'll go out of business after they stop laughing.
# original is here: https://gist.github.com/qoq/8af44386accf4ee43d8e

import sys
import crcmod
from struct import unpack
from collections import namedtuple
from Crypto.Cipher import DES

# 64-bit DES keys are hardcoded into /lib/libtpsutil.so
# Your keys might be different -- extract yours or bruteforce
hdr_key = b'mj549888'
krnl_key = b'u7k41888'
rootfs_key = b'VjohnnyV'

def to_hex(data):
    return ''.join('%02x' % x for x in data)

def to_str(data):
    try:
        return bytes(data).decode().strip('\x00')
    except:
        return data

def des_decrypt(data, des_key):
    #iv =b'\x00\x00\x00\x00\x00\x00\x00\x00'
    #dh = DES.new(des_key, DES.MODE_ECB, iv)
    dh = DES.new(des_key, DES.MODE_ECB)
    cryplen = len(data) - (len(data) % 8)
    return dh.decrypt(bytes(data[:cryplen])) + data[cryplen:]

crc32 = crcmod.predefined.mkPredefinedCrcFun('crc-32')
Header = namedtuple("Header", "magic crc length")
Kernel = namedtuple("Kernel", "unk1 offset length crc name")
Rootfs = namedtuple("Rootfs", "offset length name crc")

encrypted = False
filename = sys.argv[1];
path = filename+".unpack/";
with open(filename, "rb") as fd:
    data = memoryview(fd.read())

try:
    header_data = bytearray(data[:1556])
    header = Header(*unpack("<8s2I", header_data[:16]))
    if header.magic != b'FIRMWARE':
        encrypted = True
        header_data = des_decrypt(header_data, hdr_key)
        header = Header(*unpack("<8s2I", header_data[:16]))
    if header.magic != b'FIRMWARE':
        raise Exception("Magic not found or invalid DES key")
    print("          Magic:", header.magic)
    print("Header Checksum:", hex(header.crc))
    print("    File Length:", header.length)
    print("      Encrypted:", encrypted)
except Exception as e:
    print("Not a topsee rom: %s" % str(e))
    exit(1)

header_data_c = bytearray(header_data)
header_data_c[8:12] = b'\x00\x00\x00\x00'
header_crc = crc32(header_data_c)
if header.crc != header_crc:
    print("Header crc mismatch, expected: %s got %s" % (hex(header.crc), hex(header_crc)))
print()

kernel = Kernel(*unpack("<4I256s", header_data[16:0x120]))

print("       Kernel:", to_str(kernel.name))
print("      Unknown:", hex(kernel.unk1))
print("Kernel Offset:", kernel.offset)
print("  Kernel Size:", kernel.length)
print("     Checksum:", hex(kernel.crc))
kernel_data = data[kernel.offset:][:kernel.length]
if encrypted:
    kernel_data = des_decrypt(kernel_data[:0x1000], krnl_key) + kernel_data[0x1000:]
kernel_crc = crc32(kernel_data)
if kernel_crc != kernel.crc:
    print("Kernel crc mismatch, expected: %s got %s" % (hex(kernel.crc), hex(kernel_crc)))
print()


rootfs = Rootfs(*unpack("<2I256sI", header_data[0x120:0x22C]))

print("       Rootfs:", to_str(rootfs.name))
print("Rootfs Offset:", rootfs.offset)
print("  Rootfs Size:", rootfs.length)
print("     Checksum:", hex(rootfs.crc))
rootfs_data = data[rootfs.offset:][:rootfs.length]
if encrypted:
    rootfs_data = des_decrypt(rootfs_data[:0x1000], rootfs_key) + rootfs_data[0x1000:]
rootfs_crc = crc32(rootfs_data)
if rootfs_crc != rootfs.crc:
    print("Rootfs crc mismatch, expected: %s got %s" % (hex(rootfs.crc), hex(rootfs_crc)))
print()

print("Saving header")
with open(path+"header.img", "wb") as fd:
    fd.write(header_data)

print("Saving kernel")
with open(path+"kernel.img", "wb") as fd:
    fd.write(kernel_data)

print("Saving rootfs")
with open(path+"rootfs.img", "wb") as fd:
    fd.write(rootfs_data)
