#!/usr/bin/env bash
# Local build on Ubuntu / WSL2. Result: ./bin/*.apk
set -e
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv \
  autoconf automake libtool pkg-config zlib1g-dev libncurses-dev cmake \
  libffi-dev libssl-dev build-essential
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip buildozer "cython<3" virtualenv
buildozer android debug
echo "Done. APK is in ./bin"
