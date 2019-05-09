#!/usr/bin/env bash

_log_stdin() {
    level=$1; shift
    echo -n "[${level}] " && cat -
}

_log() {
    level=$1; shift
    echo "[${level}] $1"
}

_tunnel_wrap() { eval "$*" 1>"${LOGS}/stdout" 2>"${LOGS}/stderr"; }


_tunnel_do() {
    local LOGS;
    LOGS=$(mktemp -d -t tunnel.XXXXXX)

    local CODE;
    while read -r CMD ; do
        echo "---${TUNNEL_COMMAND_DELIM}"
        _log COMMAND "${CMD}"
        _tunnel_wrap "${CMD}" 
        CODE="${PIPESTATUS[0]}"
        sed -i -e '$a\' "${LOGS}/stdout"
        sed -i -e '$a\' "${LOGS}/stderr"

        while IFS= read -r -t .1 STDOUT ; do
            _log INFO "${STDOUT}"
        done < "${LOGS}/stdout"

        while IFS= read -r -t .1 STDERR ; do
            _log ERROR "${STDERR}"
        done < "${LOGS}/stderr"

        _log STATUS "${CODE}"
    done
    rm -fr "${LOGS}"
}

_tunnel_do
