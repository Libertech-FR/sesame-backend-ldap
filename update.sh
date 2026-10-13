#!/bin/bash
echo "update du module LDAP"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_BACKENDS_DIR="$(cd -- "${SCRIPT_DIR}/../../backends" 2>/dev/null && pwd || true)"
RUNTIME_BACKENDS_DIR="/var/lib/sesame-daemon/backends"

INSTALLDIR="${DEFAULT_BACKENDS_DIR}"
if [[ -d "${RUNTIME_BACKENDS_DIR}" ]]; then
  INSTALLDIR="${RUNTIME_BACKENDS_DIR}"
fi

echo "dir : ${INSTALLDIR}"

MODULE_DIR="${SCRIPT_DIR}"

shopt -s nullglob
for DIR in "${INSTALLDIR}"/*; do
  [[ -d "${DIR}" ]] || continue
  [[ -f "${DIR}/config.yml" ]] || continue

  TYPE="$(
    grep -m1 -E "^[[:space:]]*name:" "${DIR}/config.yml" \
      | cut -f2- -d':' \
      | sed -e "s/^[[:space:]]*//" -e "s/[[:space:]]*$//" -e "s/'//g"
  )"

  if [[ "${TYPE}" == "openldap" ]]; then
    echo "${DIR} is openldap"
    # maj config.yml
    mkdir -p "${DIR}/lib" "${DIR}/bin" "${DIR}/lifecycle"

    for I in "${MODULE_DIR}"/lib/*; do
      [[ -e "${I}" ]] || continue
      [[ "$(basename -- "${I}")" == "__pycache__" ]] && continue
      [[ -f "${I}" ]] || continue
      ln -sf "${I}" "${DIR}/lib/"
    done
    for I in "${MODULE_DIR}"/bin/*; do
      [[ -e "${I}" ]] || continue
      [[ "$(basename -- "${I}")" == "__pycache__" ]] && continue
      [[ -f "${I}" ]] || continue
      ln -sf "${I}" "${DIR}/bin/"
    done
    # update config.yml
    grep 'IDENTITY_LIFECYCLE_CHANGED:' ${DIR}/config.yml >/dev/null
    OK=$?
    if [ $OK -eq 1 ];then
      echo "Update for lifecycle"
      echo -e "  IDENTITY_LIFECYCLE_CHANGED:\n    script: 'lifecycle.py'\n     onError: 'stop'" >>${DIR}/config.yml
    fi
    grep 'GROUP_CREATE:' ${DIR}/config.yml >/dev/null
    OK=$?
    if [ $OK -eq 1 ];then
      echo "Update for groups"
      echo -e "  GROUP_CREATE:\n    script: 'groups.py'\n    onError: 'continue'" >>${DIR}/config.yml
      echo -e "  GROUP_UPDATE:\n    script: 'groups.py'\n    onError: 'continue'" >>${DIR}/config.yml
      echo -e "  GROUP_DELETE:\n    script: 'groups_del.py'\n    onError: 'continue'" >>${DIR}/config.yml
    fi
  fi
done
