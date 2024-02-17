#!/bin/bash
set -euo pipefail

cd "$( dirname -- "$0" )/.."

MC_VERSION='1.20.4'
API_BASE='https://api.papermc.io/v2/projects/paper'

LATEST_BUILD_INFO=$(curl -s "$API_BASE/versions/$MC_VERSION/builds/" | jq '.builds[-1]')
BUILD_NUMBER=$(echo "$LATEST_BUILD_INFO" | jq -r '.build')

echo "Build #: $BUILD_NUMBER"

if [ -z "$BUILD_NUMBER" ]; then
  echo "No Paper build found for Minecraft $MC_VERSION"
  exit 1
fi

DOWNLOAD_URL="$API_BASE/versions/$MC_VERSION/builds/$BUILD_NUMBER/downloads/paper-$MC_VERSION-$BUILD_NUMBER.jar"

echo "Downloading Paper build #$BUILD_NUMBER"
curl -o paper.new.jar "$DOWNLOAD_URL"

NEW_MD5=$(md5sum 'paper.new.jar' | awk '{ print $1 }')
OLD_MD5=$(md5sum 'paper.jar' | awk '{ print $1 }')

if [[ "$NEW_MD5" == "$OLD_MD5" ]]; then
  echo "Paper build #$BUILD_NUMBER is already installed"
  rm paper.new.jar
  exit 0
fi

echo "Installing Paper build #$BUILD_NUMBER"
mv paper.jar paper.old.jar
mv paper.new.jar paper.jar

echo 'Giving players notice of restart...'
tmux send-keys -t minecraft 'say Restarting to update server in 15 seconds...' Enter
sleep 15

echo 'Restarting the server...'
sudo /usr/bin/systemctl restart minecraft
