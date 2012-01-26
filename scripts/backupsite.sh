#!/bin/sh
FILENAME="backup_site_"`/bin/date +%Y%m%d`".tar.gz"
tar -zcvf /var/www/gamemine/backup/$FILENAME /var/www/gamemine/gamemine/project/ /var/www/gamemine/gamemine/templates/ /var/www/gamemine/gamemine/js/ /var/www/gamemine/gamemine/styles/ /var/www/gamemine/gamemine/lib/python2.6/

