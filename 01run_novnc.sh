ps aux | grep "0.0.0.0:84 --daemon" | grep -v grep | awk '{print "kill -9 " $2}' | sh;websockify 0.0.0.0:84 --daemon --web=/var/www/novnc --token-plugin=TokenMysql --token-source='mysql'
