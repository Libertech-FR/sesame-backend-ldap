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

    mkdir -p "${DIR}/lib" "${DIR}/bin"

    for I in "${MODULE_DIR}"/lib/*; do
      ln -sf "${I}" "${DIR}/lib/"
    done
    for I in "${MODULE_DIR}"/bin/*; do
      ln -sf "${I}" "${DIR}/bin/"
    done
  fi
done
