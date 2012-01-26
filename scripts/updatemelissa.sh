#!/bin/sh

#VARIABLES
MELISSA="/var/www/gamemine/data/melissa"
MELISSA_OLD="/var/www/gamemine/data/melissa_old"
MELISSA_NEW="/var/www/gamemine/data/melissa_new"
MELISSAOLDLIB="/var/www/gamemine/lib/melissaold"
MELISSALIB="/var/www/gamemine/lib/melissa"

#getting file from melissa
echo "getting melissa data from melissa website"
FILENAME="dqs_"`/bin/date +%Y%m`".zip"
DOWNLOAD="http://www.melissadata.com/service/product_download.aspx?p=7740&u=9RGgost2m3Rc%3d"
wget -c $DOWNLOAD -O $FILENAME

#creating a new directory for new melissa data
echo "creating a temporary directory for new melissa data"
mkdir $MELISSA_NEW
unzip $FILENAME -d $MELISSA_NEW 

#removing zip file
echo "removing melissa zip file"
rm -rf $FILENAME

#removing old melissa library if it exists
if [ -d "$MELISSAOLDLIB" ]; then
    echo "removing old melissa library"
    rm -rf $MELISSAOLDLIB
fi

#backup melissa lib
echo "backup melissa lib"
cp -r $MELISSALIB $MELISSAOLDLIB

#updating libraries
cp $MELISSA_NEW/name/linux/gcc34_64bit/libmdName.so $MELISSALIB
cp $MELISSA_NEW/phone/linux/gcc34_64bit/libmdPhone.so $MELISSALIB
cp $MELISSA_NEW/address/linux/gcc34_64bit/libmdAddr.so $MELISSALIB

#removing old melissa data if it exists
if [ -d "$MELISSA_OLD" ]; then
    echo "removing old melissa data"
    rm -rf $MELISSA_OLD
fi
#backup current melissa data
echo "backup current melissa data"
mv $MELISSA $MELISSA_OLD
#updating melissa data
echo "updating melissa data"
mv $MELISSA_NEW $MELISSA
echo "Melissa has been updated successfully"



