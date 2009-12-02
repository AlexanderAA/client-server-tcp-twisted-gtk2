import os

#set PYTONPATH
dir_name = os.path.dirname(os.path.abspath(__file__))
os.system('export PYTHONPATH=$PYTHONPATH:' + dir_name +';')

#run twistd server
os.system('twistd -l vt_server.log vt_server')

#run client
os.system('python vt_client/vt_client.py')
