#!/system/bin/sh
# PF1007L boot fixes; preserve the existing recovery and deferred Wi-Fi hooks.
CONF=/data/local/frame-boot.conf
[ -r $CONF ] && . $CONF
B=/system/bin

$B/sh $B/frame-maintenance-boot.sh &
[ "$POWER_FIX" = 1 ] && $B/sh $B/frame-powerfix.sh &
if [ "$WIFI_DEFER" = 1 ] && [ -n "$WIFI_DRIVER" ] && [ -e "$WIFI_DRIVER" ]; then
    : > /data/local/frame-empty.ko
    mount -o bind /data/local/frame-empty.ko "$WIFI_DRIVER"
fi
$B/sh $B/frame-wifidefer.sh &
$B/sh $B/frame-timesync.sh &
$B/sh $B/frame-bird-display.sh &
exec $B/sh $B/frame-fixmac.sh
