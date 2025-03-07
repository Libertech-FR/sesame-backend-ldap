#!/bin/bash
echo "Deploiment du module LDAP"
echo "La position determinera l'ordre d'execution des backends (comme dans init.d)"
read -p "Numero de demarrage du module (2 positions):" NUM
echo "installation dans backends/${NUM}openldap"
INSTALL=../../backends/${NUM}openldap
BACKEND=openldap
if [  -d ../../backends/${NUM}${BACKEND} ];then
   read -p "Repertoire déjà existant voulez vous l'écraser ? (O/N)" -i "N" REPONSE
   if [ "$REPONSE" = "O" ];then
     rm -rf ../../backends/${NUM}${BACKEND}
   else
     exit 1
   fi
fi
mkdir ../../backends/${NUM}${BACKEND}
echo "Copie des fichiers dans ${INSTALL}"
mkdir $INSTALL/etc
cp  ./etc/* $INSTALL/etc

mkdir $INSTALL/bin
mkdir $INSTALL/lib
PWD=`pwd`
cp ./lib/__init__.py $INSTALL/lib
ln -s $PWD/lib/backend_ldap_utils.py $INSTALL/lib/backend_ldap_utils.py
ln -s $PWD/bin/changepwd.py $INSTALL/bin/changepwd.py
ln -s $PWD/bin/ping.py $INSTALL/bin/ping.py
ln -s $PWD/bin/resetpwd.py $INSTALL/bin/resetpwd.py
ln -s $PWD/bin/upsertidentity.py $INSTALL/bin/upsertidentity.py
ln -s $PWD/bin/delentity.py $INSTALL/bin/delentity.py
chmod 700 $INSTALL/bin/*
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
