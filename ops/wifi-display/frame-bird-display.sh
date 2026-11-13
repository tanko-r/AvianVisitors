#!/system/bin/sh
# PF1007L: start after vendor boot initialization, which suppresses ordinary
# third-party boot receivers and resets accessibility_enabled on this frame.
t=0
until [ "$(getprop sys.boot_completed)" = 1 ] || [ "$t" -ge 180 ]; do
    sleep 1
    t=$((t + 1))
done
[ "$(getprop sys.boot_completed)" = 1 ] || exit 0
sleep 12
# Keep an explicit pause effective across boots.
grep -q 'name="enabled" value="true"' /data/data/com.avianvisitors.display/shared_prefs/display.xml || exit 0
# Launch the exported native activity first. This vendor build does not start
# this app reliably through BOOT_COMPLETED or a root am startservice call.
am start -n com.avianvisitors.display/.MainActivity
sleep 2
SERVICE=com.avianvisitors.display/com.avianvisitors.display.ViewerNavigation
SERVICES=$(settings get secure enabled_accessibility_services)
[ "$SERVICES" = null ] && SERVICES=
case ":$SERVICES:" in
    *":$SERVICE:"*) ;;
    *) SERVICES="${SERVICES:+$SERVICES:}$SERVICE" ;;
esac
settings put secure enabled_accessibility_services "$SERVICES"
settings put secure accessibility_enabled 1
sleep 2
am start -n com.avianvisitors.display/.MainActivity --ez autostart true
log -t frame-bird-display "Display startup requested after vendor initialization"
