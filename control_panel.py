import sys
import re
import websocket
from PySide6.QtCore import (
    Qt,
    QObject,
    QRunnable,
    QThreadPool,
    Signal,
    Slot,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QRadioButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)


class WorkerSignals(QObject):
    open = Signal()
    error = Signal(str)
    close = Signal(tuple)
    message = Signal(str)


class WebsocketWorker(QRunnable):
    def __init__(self, address):
        super().__init__()
        self.signals = (WorkerSignals())
        self.address = address
        self.is_killed = False
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(f'ws://{self.address}',
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

    @Slot()
    def run(self):
        self.ws.run_forever()
        if self.is_killed:
            return

    def kill(self):
        self.ws.close()
        self.ws = None
        self.is_killed = True

    def on_message(self, ws, message):
        print(message)
        self.signals.message.emit(str(message))

    def on_error(self, ws, error):
        print(error)
        self.signals.error.emit(f'{error}')

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")
        self.signals.close.emit((close_status_code, close_msg))

    def on_open(self, ws):
        print("Opened connection")
        self.signals.open.emit()

    def prev_track(self):
        self.ws.send('prev_track')

    def next_track(self):
        self.ws.send('next_track')

    def toggle_play_pauses(self):
        self.ws.send('toggle_play_pause')

    def set_shuffled(self, shuffled):
        self.ws.send(f'set_shuffled {shuffled}')

    def set_repeat_state(self, state):
        self.ws.send(f'set_repeat_state {state}')

    def set_volume(self, volume):
        self.ws.send(f'set_volume {volume}')

    def get_volume(self):
        self.ws.send(f'get_volume')

    def get_shuffled(self):
        self.ws.send(f'get_shuffled')
    
    def get_repeat_state(self):
        self.ws.send(f'get_repeat_state')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Control Panel")

        self.main_vbox_layout = QVBoxLayout()
        self.main_vbox_layout.setContentsMargins(15,15,15,15)
        self.set_row0_components()
        self.set_row1_components()
        self.set_row2_components()
        self.components_enabled(False)

        vbox_widget = QWidget()
        vbox_widget.setLayout(self.main_vbox_layout)
        self.setCentralWidget(vbox_widget)

        self.threadpool = QThreadPool()

    def closeEvent(self, event):
        print('>>> window close')
        self.threadpool.start(self.ws_worker_kill)


    ##
    # UI
    ##
    def set_row0_components(self):
        ws_label = QLabel("ws://")
        self.ws_address = QLineEdit()
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_button_clicked)

        layout = QHBoxLayout()
        layout.addWidget(ws_label)
        layout.addWidget(self.ws_address)
        layout.addWidget(self.connect_button)
        layout.setContentsMargins(0,0,0,0)

        self.main_vbox_layout.addLayout(layout)

    def set_row1_components(self):
        self.prev_button = QPushButton("Prev track")
        self.prev_button.clicked.connect(self.prev_button_clicked)
        self.play_pause_button = QPushButton("Play / Pause")
        self.play_pause_button.clicked.connect(self.play_pause_button_clicked)
        self.next_button = QPushButton("Next track")
        self.next_button.clicked.connect(self.next_button_clicked)

        layout = QHBoxLayout()
        layout.addWidget(self.prev_button)
        layout.addWidget(self.play_pause_button)
        layout.addWidget(self.next_button)
        layout.setContentsMargins(0,0,0,0)

        self.main_vbox_layout.addLayout(layout)

    def set_row2_components(self):
        self.shuffle_checkbox = QCheckBox("Shuffled")
        self.shuffle_checkbox.setTristate(False)
        self.shuffle_checkbox.stateChanged.connect(self.shuffle_state_changed)

        repeat_label = QLabel("Repeat:")
        self.off_radiobutton = QRadioButton("Off")
        self.off_radiobutton.clicked.connect(self.repeat_radiobutton_clicked)
        self.one_radiobutton = QRadioButton("One")
        self.one_radiobutton.clicked.connect(self.repeat_radiobutton_clicked)
        self.all_radiobutton = QRadioButton("All")
        self.all_radiobutton.clicked.connect(self.repeat_radiobutton_clicked)

        sub_layout1 = QHBoxLayout()
        sub_layout1.addWidget(repeat_label)
        sub_layout1.addWidget(self.off_radiobutton)
        sub_layout1.addWidget(self.one_radiobutton)
        sub_layout1.addWidget(self.all_radiobutton)
        sub_layout1.setContentsMargins(20,0,20,0)

        volume_label = QLabel("Volume:")
        self.volume_spinbox = QSpinBox()
        self.volume_spinbox.setRange(0,100)
        self.volume_spinbox.valueChanged.connect(self.volume_changed)

        sub_layout2 = QHBoxLayout()
        sub_layout2.addWidget(volume_label)
        sub_layout2.addWidget(self.volume_spinbox)
       
        layout = QHBoxLayout()
        layout.addWidget(self.shuffle_checkbox)
        layout.addLayout(sub_layout1)
        layout.addLayout(sub_layout2)
        layout.setContentsMargins(0,0,0,0)

        self.main_vbox_layout.addLayout(layout)

    def components_enabled(self, enabled):
        self.connect_button.setEnabled(not enabled)
        self.prev_button.setEnabled(enabled)
        self.play_pause_button.setEnabled(enabled)
        self.next_button.setEnabled(enabled)
        self.shuffle_checkbox.setEnabled(enabled)
        self.off_radiobutton.setEnabled(enabled)
        self.one_radiobutton.setEnabled(enabled)
        self.all_radiobutton.setEnabled(enabled)
        self.volume_spinbox.setEnabled(enabled)

        if enabled:
            self.connect_button.setText('Connected')
        else:
            self.connect_button.setText('Connect')

    def show_dialog(self, title, text):
        if self.isVisible():
            dialog = QMessageBox(self)
            dialog.setWindowTitle(title)
            dialog.setText(text)
            button = dialog.exec()
            if button == QMessageBox.Ok:
                print("OK!")


    ##
    # Clicked
    ##
    def connect_button_clicked(self):
        print('connect_button_clicked')
        address = self.ws_address.text().strip().strip('\r').strip('\n')
        print(f'connect to {address}')
        self.connect_button.setEnabled(False)
        self.connect_button.setText('Connecting...')
        self.ws_worker = WebsocketWorker(address)
        self.ws_worker.signals.open.connect(self.ws_on_open)
        self.ws_worker.signals.close.connect(self.ws_on_close)
        self.ws_worker.signals.error.connect(self.ws_on_error)
        self.ws_worker.signals.message.connect(self.ws_on_message)
        self.threadpool.start(self.ws_worker)

    def prev_button_clicked(self):
        print('prev_button_clicked')
        self.threadpool.start(self.prev_track)
    
    def play_pause_button_clicked(self):
        print('play_pause_button_clicked')
        self.threadpool.start(self.toggle_play_pauses)

    def next_button_clicked(self):
        print('next_button_clicked')
        self.threadpool.start(self.next_track)

    def shuffle_state_changed(self):
        if self.shuffle_checkbox.checkState() == Qt.Checked:
            print('Qt.Checked')
            self.shuffled = True
        elif self.shuffle_checkbox.checkState() == Qt.Unchecked:
            print('Qt.Unchecked')
            self.shuffled = False
        else:
            self.shuffled = False
        self.threadpool.start(self.set_shuffled)

    def repeat_radiobutton_clicked(self):
        print('repeat_radiobutton_clicked')
        if self.off_radiobutton.isChecked() == True:
            print('=> off_radiobutton')
            self.repeat_state = 'off'
        elif self.one_radiobutton.isChecked() == True:
            print('=> one_radiobutton')
            self.repeat_state = 'one'
        elif self.all_radiobutton.isChecked() == True:
            print('=> all_radiobutton')
            self.repeat_state = 'all'
        else:
            self.repeat_state = 'off'
        self.threadpool.start(self.set_repeat_state)

    def volume_changed(self, v):
        print(f'volume: {v}')
        self.volume = v
        self.threadpool.start(self.set_volume)


    ##
    # websocket
    ##
    def ws_on_message(self, message):
        print('>>> print message:')
        print(message)
        event, value = self.analyze_message(message)
        match event:
            case 'volume':
                self.volume_spinbox.setValue(int(value))
            case 'shuffled':
                if value == 'true':
                    self.shuffle_checkbox.setCheckState(Qt.Checked)
                else:
                    self.shuffle_checkbox.setCheckState(Qt.Unchecked)
            case 'repeat_state':
                if value == 'off':
                    self.off_radiobutton.setChecked(True)
                elif value == 'one':
                    self.one_radiobutton.setChecked(True)
                elif value == 'all':
                    self.all_radiobutton.setChecked(True)


    def ws_on_error(self, error):
        print(error)
        self.show_dialog('Error', error)

    def ws_on_close(self, t):
        print(t)
        self.components_enabled(False)
        self.ws_worker = None
        self.show_dialog('Alert', 'WebSocket connection closed.')

    def ws_on_open(self):
        self.threadpool.start(self.set_current_state)
        self.components_enabled(True)

    def analyze_message(self, message):
        m = re.match("\[(?P<event>.+?)\]\((?P<value>.*?)\)", message)
        try:
            event = m.group('event')
        except:
            event = ''
        try:
            value = m.group('value')
        except:
            value = ''

        return (event, value)


    ##
    # Command
    ##
    @Slot()
    def ws_worker_kill(self):
        self.ws_worker.kill()

    @Slot()
    def prev_track(self):
        self.ws_worker.prev_track()

    @Slot()
    def toggle_play_pauses(self):
        self.ws_worker.toggle_play_pauses()
    
    @Slot()
    def next_track(self):
        self.ws_worker.next_track()

    @Slot()
    def set_shuffled(self):
        self.ws_worker.set_shuffled(self.shuffled)

    @Slot()
    def set_repeat_state(self):
        self.ws_worker.set_repeat_state(self.repeat_state)

    @Slot()
    def set_volume(self):
        self.ws_worker.set_volume(self.volume)

    @Slot()
    def set_current_state(self):
        self.ws_worker.get_volume()
        self.ws_worker.get_shuffled()
        self.ws_worker.get_repeat_state()




app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
