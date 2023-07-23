#!/bin/sh

rm -frR dist/

#docker build --no-cache -t animus .

python3 -m  build
