#!/usr/bin/sh

# https://forum.endeavouros.com/t/clear-kde-clipboard-klipper-n-seconds-after-something-was-last-added-to-it/13535
qdbus org.kde.klipper /klipper org.kde.klipper.klipper.clearClipboardHistory
