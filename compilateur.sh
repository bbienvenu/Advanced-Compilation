#!/bin/sh
# chmod +x compilateur.sh

python_file=exp_nanoc.py
out_file=exp_test.asm
object_file=exp_test.o  # This must be the out_file with a .O extanesion
python3 $python_file > $out_file
nasm -felf64 $out_file
gcc -no-pie $object_file