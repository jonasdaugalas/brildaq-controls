import time
import threading
import flask
import flask_socketio as sio
# from flask_socketio import SocketIO


app = flask.Flask(__name__)
socketio = sio.SocketIO(app)

sessions = {}


class LogSender(threading.Thread):
    def __init__(self, sid, config):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sid = sid
        self.config = config
        self.need_to_stop = False

    def stop(self):
        self.need_to_stop = True

    def run(self):
        print(self.config)
        counter = 0
        while not self.need_to_stop:
            socketio.send(
                'logging to {}. {}. config: {}'.format(
                    str(self.sid), counter, self.config),
                room=self.sid)
            counter += 1
            time.sleep(1)


@app.route('/logs')
def get_app():
    return flask.send_from_directory('../client', 'viewlog.html')


@socketio.on('disconnect')
def handle_disconnect():
    print('disconnecting')
    stop_log_send(flask.request.sid)
    print('disconnected {}'.format(flask.request.sid))


@socketio.on('bringmelogs')
def handle_bringmelogs(json):
    print('bring me logs event! {} {}'.format(
        flask.request.sid, json))
    start_log_send(flask.request.sid, json)

@socketio.on('stopmylogs')
def handle_bringmelogs():
    print('asked to stop logs! {}'.format(flask.request.sid))
    stop_log_send(flask.request.sid)


def start_log_send(sid, config):
    if sid in sessions:
        stop_log_send(sid)
    sessions[sid] = {
        "job": LogSender(sid, config),
        "timestamp": time.time()
    }
    print('Starting {}'.format(sessions[sid]))
    sessions[sid]["job"].start()


def stop_log_send(sid):
    print('stopping {}'.format(sid))
    if sid in sessions:
        job = sessions[sid]["job"]
        print('before LogSender.stop()')
        job.stop()
        try:
            job.join()
        except RuntimeError as e:
            # don't know exactly why it fails to join in some cases
            if e.message != 'cannot join current thread':
                raise e
        return True
    print('sid not found')
    return False


if __name__ == '__main__':
    socketio.run(app, '0.0.0.0', port=5006)
