#!/bin/sh
# Run as root once on the Pi before enabling the suggestion form.
set -eu
[ ! -L /var/lib/avian-visitors/suggestions ] || {
    echo 'Refusing a symlinked suggestion directory' >&2
    exit 1
}
install -d -o caddy -g caddy -m 0750 /var/lib/avian-visitors/suggestions
