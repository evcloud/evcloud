#!/bin/sh
kill -HUP `cat uwsgi.pid` 

sudo uwsgi -M -p 8 -x conf/vmmanager.xml --plugin python --pidfile uwsgi.pid