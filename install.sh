#!/bin/bash
echo "Deploiment du module LDAP"
echo "La position determinera l'ordre d'execution des backends (comme dans init.d)"
read -p "Numero de demarrage du module (2 positions):" NUM
echo "installation dans backends/${NUM}openldap"
INSTALL=../../backends/${NUM}openldap
if [  -d ../../backends/${NUM}openldap ];then
   echo "Repertoire deja existant choisissez un autre numéro"
   exit 1
else
   mkdir ../../backends/${NUM}openldap
fi
echo "Copie des fichiers dans ${INSTALL}"
mkdir $INSTALL/etc
cp  ./etc/* $INSTALL/etc
mkdir $INSTALL/bin
cp ./bin/* $INSTALL/bin
chmod 700 $INSTALL/bin/*
mkdir $INSTALL/lib
PWD=`pwd`
cp ./lib/__init__.py $INSTALL/lib
ln -s $PWD/lib/backend_ldap_utils.py $INSTALL/lib/backend_ldap_utils.py
cp config.yml $INSTALL

echo "Le backend a été installé dans $INSTALL"
echo "Configuration"
read -p "Url du serveur ldap (ldap[s]://FDQN:PORT : " HOST
read -p "Dn d'authentification (doit avoir les droits d'ecriture) : " DN
read -s -p "Mot de passe : " PASSWORD
read -p "Base ldap : " BASE
read -p "Branche pour les utilisateurs ex: ou=peoples : " USERBASE
read -p "Attribut pour le Rdn : "  RDN
echo "Génération du fichier de configuration"
CONFFILE=${INSTALL}/etc/config.conf
echo "host=${HOST}" > ${CONFFILE}
echo "dn=${DN}" >> ${CONFFILE}
echo "password=${PASSWORD}" >> ${CONFFILE}
echo "base=${BASE}" >> ${CONFFILE}
echo "userbase=${USERBASE},${BASE}" >> ${CONFFILE}
echo "rdnattribute=${RDN}" >> ${CONFFILE}
echo "backendFor=etd,adm,esn" >> ${CONFFILE}
chmod 600 ${CONFFILE}
systemctl restart sesame-daemon
echo "Vous pouvez completer le fichier de configuration avec les parametres optionnels (voir README.md)"
echo "Merci "
