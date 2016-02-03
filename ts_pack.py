#!/usr/bin/env python3

#TOPSEE camera firmware packer with encryption support
# Usage: ts_pack header.img kernel.img rootfs.img

# @Topsee: Your firmware is a total mess... Bugs and security holes throughout.
# Command line injection, instant root access with default password, outdated TI SDK.
# Stop encrypting it -- nobody is going to steal such a mess and if
# somebody tries, they'll go out of business after they stop laughing.
# original is here: https://gist.github.com/qoq/8af44386accf4ee43d8e

import sys
import crcmod
from struct import pack
from Crypto.Cipher import DES

path = sys.argv[1];
filename = sys.argv[2];

encrypt = True
# 64-bit DES keys are hardcoded into /lib/libtpsutil.so
# Your keys might be different -- extract yours or bruteforce (ECB makes it trivial)
hdr_key = b'mj549888'
krnl_key = b'u7k41888'
rootfs_key = b'VjohnnyV'

def des_encrypt(data, des_key):
    iv =b'\x00\x00\x00\x00\x00\x00\x00\x00'
    dh = DES.new(des_key, DES.MODE_ECB, iv)
    cryplen = len(data) - (len(data) % 8)
    return dh.encrypt(bytes(data[:cryplen])) + data[cryplen:]

crc32 = crcmod.predefined.mkPredefinedCrcFun('crc-32')

with open(path+"/header.img", "rb") as fd:
    header = bytearray(memoryview(fd.read()))
with open(path+"/kernel.img", "rb") as fd:
    kernel = memoryview(fd.read())
with open(path+"/rootfs.img", "rb") as fd:
    rootfs = bytearray(memoryview(fd.read()))

header[20:24] = pack("<I", len(header))
header[24:28] = pack("<I", len(kernel))
header[28:32] = pack("<I", crc32(kernel))

header[0x120:0x124] = pack("<I", len(header) + len(kernel))
header[0x124:0x128] = pack("<I", len(rootfs))
header[0x228:0x22C] = pack("<I", crc32(rootfs))

total_len = len(header) + len(kernel) + len(rootfs)
header[12:16] = pack("<I", total_len)

header[8:12] = b'\x00\x00\x00\x00'
header[8:12] = pack("<I", crc32(header))

print("Saving image")
with open(filename, "wb") as fd:
    if encrypt:
        header = des_encrypt(header, hdr_key)
        kernel = des_encrypt(kernel[:0x1000], krnl_key) + kernel[0x1000:]
        rootfs = des_encrypt(rootfs[:0x1000], rootfs_key) + rootfs[0x1000:]
    fd.write(header)
    fd.write(kernel)
    fd.write(rootfs)
