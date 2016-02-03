dir=${1?Please give path to a directory with unpacked firmware}
nfw=${2?Please give name for a newly packed firmware}
if [ ! -e $dir ]; then
    echo "Directory not exists: $dir"
    exit 1
fi
if [ -e $nfw ]; then
    echo "Firmware already exists: $nfw"
    exit 1
fi
# repack rootfs
echo "Repacking rootfs"
if [ -e $dir/rootfs.img ]; then
    if [ ! -e $dir/rootfs.img.bak ]; then
        mv $dir/rootfs.img $dir/rootfs.img.bak 2>/dev/null
    fi
    fakeroot -i $dir/.fakeroot mkcramfs $dir/root/ $dir/rootfs.img
elif [ -e $dir/squashfs.img -o -e $dir/squashfs.img.bak ]; then
    if [ ! -e $dir/squashfs.img.bak ]; then
        mv $dir/squashfs.img $dir/squashfs.img.bak 2>/dev/null
    fi
    rm $dir/squashfs.img 2>/dev/null
    fakeroot -i $dir/.fakeroot mksquashfs $dir/root/ $dir/rootfs.img -no-xattrs -all-root -comp xz
else
    echo "Unknown root fs type"
fi

# ckeck kernel size
kernsize=$(stat -c %s $dir/kernel.img)
if [ $kernsize -ge 2097152 ]; then
	echo "WARN: size of kernel is more than 0x200000. FW probably will not flash"
fi

# check fs size
if [ $(stat -c %s $dir/rootfs.img) -lt 8388608 ]; then
    echo "WARN: size of filesystem is less than 0x800000."
fi
if [ $(stat -c %s $dir/rootfs.img) -ge 15728640 ]; then
    echo "WARN: size of filesystem is more than 0xF00000."
fi

python3 ts_pack.py $dir $nfw

if [ ! -f $nfw ]; then
    echo "Something goes wrong."
    exit 1
fi
echo "Done"
