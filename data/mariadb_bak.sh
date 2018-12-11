   mysqldump --databases evcloud --ignore-table=evcloud.django_session --hex-blob > ./evcloud.sql;
   mysqldump  evcloud django_session --no-data >> ./evcloud.sql;

