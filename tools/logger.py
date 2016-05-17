import sys
import time
import threading
from flask import Flask
from flask_socketio import SocketIO

import brillogreader

counter = 0

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@socketio.on('message')
def handle_message(message):
    socketio.send('got message. yay. ' + message)


@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))


def broadcast_test():
    print("in broadcast")
    global counter
    socketio.send(str(counter))
    counter += 1
    counter = counter % 16


def work1():
    while True:
        broadcast_test()
        try:
            time.sleep(4)
        except KeyboardInterrupt:
            sys.exit(1)



def work2():
    reader = brillogreader.LogReader(
        '/var/log/rcms/lumipro/Logs_lumipro.xml', True, None, None, 'best', None,
        False, True, interval=4)
    for l in reader.logs():
        socketio.send(l)


if __name__ == '__main__':
    try:
        t = threading.Thread(target=work2)
        t.start()
        socketio.run(app, '0.0.0.0')
        t.join()
    except KeyboardInterrupt:
        sys.exit(1)
