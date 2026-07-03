#!/bin/bash
# Zotero Translation Server launcher with auto-sleep on inactivity.
# Installed by skills/zotero/scripts/install_add_identifier.sh.
# Starts the Node.js translation server on demand and manages its lifecycle.

set -euo pipefail

SERVER_DIR="/tmp/translation-server"
PID_FILE="/tmp/zotero-translation-server.pid"
ACTIVITY_FILE="/tmp/translation-server.last-active"
IDLE_TIMEOUT_MINUTES=30
PORT=1969

check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            if curl -s "http://127.0.0.1:$PORT" >/dev/null 2>&1; then
                return 0
            fi
        fi
    fi
    return 1
}

record_activity() {
    touch "$ACTIVITY_FILE"
}

start_watchdog() {
    (
        while true; do
            sleep 300
            if [ ! -f "$PID_FILE" ]; then
                exit 0
            fi
            if [ -f "$ACTIVITY_FILE" ]; then
                local last_active now idle_min
                last_active=$(stat -f %m "$ACTIVITY_FILE" 2>/dev/null || stat -c %Y "$ACTIVITY_FILE" 2>/dev/null || echo "0")
                now=$(date +%s)
                idle_min=$(( (now - last_active) / 60 ))
                if [ "$idle_min" -gt "$IDLE_TIMEOUT_MINUTES" ]; then
                    "$0" stop >/dev/null 2>&1
                    exit 0
                fi
            fi
        done
    ) &
    disown
}

start_server() {
    if check_running; then
        record_activity
        echo "Translation server already running on port $PORT"
        exit 0
    fi

    if [ ! -d "$SERVER_DIR" ]; then
        echo "Error: translation-server not found at $SERVER_DIR"
        echo "Run: skills/zotero/scripts/install_add_identifier.sh"
        exit 1
    fi

    cd "$SERVER_DIR"
    nohup node src/server.js > /tmp/translation-server.log 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"

    local attempts=0
    while [ $attempts -lt 30 ]; do
        if curl -s "http://127.0.0.1:$PORT" >/dev/null 2>&1; then
            record_activity
            start_watchdog
            echo "Translation server started on port $PORT (PID: $pid)"
            exit 0
        fi
        sleep 0.5
        attempts=$((attempts + 1))
    done

    echo "Error: Server failed to start within 15 seconds"
    cat /tmp/translation-server.log
    exit 1
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            rm -f "$PID_FILE" "$ACTIVITY_FILE"
            echo "Translation server stopped"
        else
            rm -f "$PID_FILE" "$ACTIVITY_FILE"
            echo "Translation server was not running"
        fi
    else
        echo "Translation server was not running"
    fi
}

status() {
    if check_running; then
        local pid
        pid=$(cat "$PID_FILE")
        local idle_info=""
        if [ -f "$ACTIVITY_FILE" ]; then
            local last_active now idle_min
            last_active=$(stat -f %m "$ACTIVITY_FILE" 2>/dev/null || stat -c %Y "$ACTIVITY_FILE" 2>/dev/null || echo "0")
            now=$(date +%s)
            idle_min=$(( (now - last_active) / 60 ))
            idle_info=" (idle ${idle_min}m, timeout ${IDLE_TIMEOUT_MINUTES}m)"
        fi
        echo "Translation server is running on port $PORT (PID: $pid)${idle_info}"
    else
        echo "Translation server is not running"
    fi
}

touch_activity() {
    record_activity
    echo "Activity recorded"
}

case "${1:-start}" in
    start)    start_server ;;
    stop)     stop_server ;;
    restart)  stop_server; sleep 1; start_server ;;
    status)   status ;;
    touch)    touch_activity ;;
    *)        echo "Usage: $0 {start|stop|restart|status|touch}"; exit 1 ;;
esac
