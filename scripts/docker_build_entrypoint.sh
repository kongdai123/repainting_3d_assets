#!/usr/bin/env bash
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

USER_ID=$(stat -c %u ${ROOT_CODE})
GROUP_ID=$(stat -c %g ${ROOT_CODE})

groupadd -g $GROUP_ID usergroup
useradd -m -l -u $USER_ID -g usergroup user

chown -R user:usergroup ${HF_HOME}

if [ ! -z "${DEBUG}" ]; then
    env
    whoami
    groups
    ls -l /dev/nvidia*
    gosu user env
    gosu user whoami
    gosu user groups
    gosu user ls -l /dev/nvidia*
fi

exec gosu user "$@"
