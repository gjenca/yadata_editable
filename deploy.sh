#!/usr/bin/env bash
# vim: et ts=4 sw=4 ai

PROJECT=yadata_editable
#STATICDIR=/data/www/$PROJECT-static
CODEDIR=/usr/local/lib/$PROJECT


rm -r $CODEDIR
#rm -r $STATICDIR
mkdir -pv $CODEDIR
#mkdir -pv $STATICDIR/static
cp -rvf template $CODEDIR/template
cp -vf main.py $CODEDIR
cp -vf unicodemail.py $CODEDIR
cp -vf main.cgi $CODEDIR
chown -R www-data:www-data $CODEDIR
chmod -R u=rX,g=,o= $CODEDIR
find  $CODEDIR -type d -exec chmod -v u+w {} \;
#systemctl restart $PROJECT
#systemctl status $PROJECT
