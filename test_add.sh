set -ex
arch=$1
./randbin.py --arch $arch test/$arch.bin
./bin2txt.py --arch $arch --defchar 0 test/$arch.bin test/$arch.txt
./test_misc.py
