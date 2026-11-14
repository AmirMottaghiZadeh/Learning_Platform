#!/bin/sh
# The password is a runtime secret, never a build argument or process argument.
set -eu
password="${REDIS_PASSWORD:-}"
case "$password" in
    ''|*[!A-Za-z0-9_-]*)
        echo 'Set REDIS_PASSWORD to a random 32-128 character alphanumeric/underscore/hyphen secret.' >&2
        exit 1 ;;
esac
if [ "${#password}" -lt 32 ] || [ "${#password}" -gt 128 ]; then
    echo 'Invalid REDIS_PASSWORD length.' >&2
    exit 1
fi
umask 077
config_path="$(mktemp /tmp/pharmenta-redis.XXXXXX)"
printf '%s\n' 'bind 0.0.0.0' 'port 6379' 'protected-mode yes' \
    'dir /data' 'appendonly yes' 'appendfsync everysec' \
    'maxmemory 512mb' 'maxmemory-policy noeviction' "requirepass $password" > "$config_path"
if [ "$(id -u)" = 0 ]; then
    chown redis:redis "$config_path"
fi
unset password
exec /usr/local/bin/docker-entrypoint.sh redis-server "$config_path"
