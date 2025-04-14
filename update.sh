#!/bin/bash
echo "update du module LDAP"
INSTALLDIR=../../backends
echo "dir : " $INSTALLDIR
BACKEND=openldap
PWD=`pwd`
for DIR in $INSTALLDIR/* ;do
        TYPE=`grep "name:" $DIR/config.yml|cut -f2 -d ' '|sed s/\'//g`
	if [ $TYPE = "openldap" ];then
		echo $DIR is openldap
                for I in $PWD/lib/*;do
                   ln -s $I $DIR/lib
                done
                for I in $PWD/bin/*;do
                   ln -s $I $DIR/bin
                done

        fi
done
