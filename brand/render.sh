#!/bin/sh
# Render the brand assets (logo, app icon, phone screens, phone mockups) with headless Chrome.
set -e
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
shot() { # page width height scale out
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
    --default-background-color=00000000 --force-device-scale-factor="$4" --window-size="$2,$3" \
    --screenshot="out/$5" "file://$PWD/src/$1" >/dev/null 2>&1
}
shot logo.html 560 124 3 logo-dark.png
shot logo-light.html 560 124 3 logo-light.png
shot icon.html 512 512 2 icon.png
for n in inbox video calendar; do shot "$n.html" 390 844 3 "screen-$n.png"; done
for n in inbox video calendar; do shot "phone-$n.html" 720 1280 1.5 "phone-$n.png"; done
ls -la out
