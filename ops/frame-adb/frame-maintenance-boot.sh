#!/system/bin/sh
# USB stays available during boot; never persist an unguarded TCP port.
umask 077
exec >>/data/local/tmp/frame-maintenance.log 2>&1
chmod 600 /data/local/tmp/frame-maintenance.log
export PATH=/system/bin:/system/xbin:/sbin
export ANDROID_ROOT=/system ANDROID_DATA=/data
export CLASSPATH=/system/bin/frame-maintenance.jar

deny() {
    iptables -N AVIAN_ADB 2>/dev/null || true
    # DROP is built-in and works before optional REJECT extensions load.
    iptables -I AVIAN_ADB 1 -p tcp --dport 5555 -j DROP || return 1
    iptables -C INPUT -p tcp --dport 5555 -j AVIAN_ADB 2>/dev/null ||
        iptables -I INPUT -p tcp --dport 5555 -j AVIAN_ADB || return 1
    ip6tables -C INPUT -p tcp --dport 5555 -j DROP 2>/dev/null ||
        ip6tables -I INPUT -p tcp --dport 5555 -j DROP || return 1
    iptables -F AVIAN_ADB || return 1
    iptables -A AVIAN_ADB -p tcp --dport 5555 -j DROP || return 1
}

setprop persist.adb.tcp.port -1
until [ "$(getprop sys.boot_completed)" = 1 ]; do sleep 1; done
# Netd and the vendor scripts can still be settling after boot_completed.
sleep 5
while :; do
    if deny; then
        setprop service.adb.tcp.port 5555
        stop adbd
        start adbd
        app_process /system/bin com.avianvisitors.maintenance.MaintenanceGuard
        echo "Guard exited; blocking TCP and retrying"
    else
        echo "Firewall unavailable; TCP remains disabled"
    fi
    # No exception or process exit may leave a stale authorized peer behind.
    deny
    setprop service.adb.tcp.port -1
    stop adbd
    start adbd
    sleep 3
done
