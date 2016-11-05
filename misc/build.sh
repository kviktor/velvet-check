#!/bin/bash

if [ $# -lt 2 ]
then
    echo "Need more params"
    exit 1
fi

gitroot=$(git rev-parse --show-toplevel)
magicjs="clients/chrome/js/magic.js"
manifest="clients/chrome/manifest.json"
api=$1
pem=$2

sed -i "s/localhost:5000/$api/g" $gitroot/$magicjs
sed -i "s/localhost/$api/g" $gitroot/$manifest

chromium-browser --pack-extension="$gitroot/clients/chrome/" --pack-extension-key="$pem"
