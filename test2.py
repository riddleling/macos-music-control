import websocket
import signal
import sys


def signal_handler(signum, frame):
    print('signal_handler: caught signal ' + str(signum))
    if signum == signal.SIGINT.value:
        ws.close()
        sys.exit(1)

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")


websocket.enableTrace(True)
signal.signal(signal.SIGINT, signal_handler)
ws = websocket.WebSocketApp("ws://127.0.0.1:9487",
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

ws.run_forever()
 