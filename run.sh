#run.sh
#!/bin/sh
#PORT=9003
#EMQTT_CLUSTER_URL=http://192.168.30.243:31425
#EMQTT_AUTH_USER=admin
#EMQTT_AUTH_PASS=public
sed -i "s/{PORT}/$PORT/g" ./emqtt-export.py
sed -i "s/{EMQTT_CLUSTER_URL}/$EMQTT_CLUSTER_URL/g" ./emqtt-export.py
sed -i "s/{EMQTT_AUTH_USER}/$EMQTT_AUTH_USER/g" ./emqtt-export.py
sed -i "s/{EMQTT_AUTH_PASS}/$EMQTT_AUTH_PASS/g" ./emqtt-export.py
python3 emqtt-export.py 