#!/system/bin/sh
# PF1007L: keep the panel asleep nightly without powering down Android or Wi-Fi.
# The frame clock supplies local time.  Use explicit SLEEP/WAKEUP key events
# instead of POWER so a delayed invocation cannot accidentally toggle the panel.

TAG=frame-display-schedule
STATE=/data/local/tmp/frame-display-schedule.state

# A system boot wakes the panel but the previous state file can still say
# "asleep".  Forget it so the first pass always applies the correct state.
[ "$1" = --boot ] && rm -f "$STATE"

while :; do
    # Night is 22:30 inclusive through 05:29 inclusive.
    case "$(date +%H%M)" in
        0000|0001|0002|0003|0004|0005|0006|0007|0008|0009|00??|01??|02??|03??|04??|05[0-2]?) desired=asleep ;;
        223?|224?|225?|226?|227?|228?|229?|23??) desired=asleep ;;
        *) desired=awake ;;
    esac

    previous=$(cat "$STATE" 2>/dev/null)
    if [ "$desired" != "$previous" ]; then
        if [ "$desired" = asleep ]; then
            input keyevent 223  # KEYCODE_SLEEP
        else
            input keyevent 224  # KEYCODE_WAKEUP
        fi
        printf '%s\n' "$desired" > "$STATE"
        log -t "$TAG" "Panel set to $desired"
    fi
    sleep 20
done
