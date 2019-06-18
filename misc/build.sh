#!/bin/bash

if [ $# -lt 2 ]
then
    echo "Need more params"
    exit 1
fi

gitroot=$(git rev-parse --show-toplevel)
backgroundjs="clients/chrome/js/background.js"
manifest="clients/chrome/manifest.json"
api=$1
pem=$2

sed -i "s/http:\/\/localhost:5000/https:\/\/$api/g" $gitroot/$backgroundjs
sed -i "s/http:\/\/localhost/https:\/\/$api/g" $gitroot/$manifest

chromium-browser --pack-extension="$gitroot/clients/chrome/" --pack-extension-key="$pem"
