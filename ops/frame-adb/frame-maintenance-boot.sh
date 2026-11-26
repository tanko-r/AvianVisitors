#!/system/bin/sh
# Called by the existing root boot hook. Never persist an unguarded TCP port.
set -eu
iptables -N AVIAN_ADB 2>/dev/null || true
# Install the deny before replacing any prior allow rules.
iptables -I AVIAN_ADB 1 -p tcp --dport 5555 -j REJECT
iptables -C INPUT -p tcp --dport 5555 -j AVIAN_ADB 2>/dev/null || iptables -I INPUT -p tcp --dport 5555 -j AVIAN_ADB
ip6tables -C INPUT -p tcp --dport 5555 -j REJECT 2>/dev/null || ip6tables -I INPUT -p tcp --dport 5555 -j REJECT
iptables -F AVIAN_ADB
iptables -A AVIAN_ADB -p tcp --dport 5555 -j REJECT
setprop persist.adb.tcp.port -1
setprop service.adb.tcp.port 5555
stop adbd
start adbd
export CLASSPATH=/system/bin/frame-maintenance.jar
while :; do
    app_process /system/bin com.avianvisitors.maintenance.MaintenanceGuard || true
    iptables -F AVIAN_ADB
    iptables -A AVIAN_ADB -p tcp --dport 5555 -j REJECT
    sleep 2
done
