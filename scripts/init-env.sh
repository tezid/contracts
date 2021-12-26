#!/bin/bash
./scripts/install-smartpy.sh --prefix bin
virtualenv .
cd bin && ln -sf SmartPy.sh spy && cd ..
