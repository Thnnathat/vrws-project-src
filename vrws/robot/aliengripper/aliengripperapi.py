import websocket
from websocket import WebSocketApp
import json
import time
from threading import Thread, Lock
import queue

class AlienGripperCommunication:
    def __init__(self, ip: str, port: str, protocal: str):
        ws_url = f"{protocal}://{ip}:{port}"  # เปลี่ยนเป็น IP ของ ESP32

        self.message_queue = queue.LifoQueue() # Lifo queue
        self.message_json = None

        self.t_ws = Thread(target=self.__start,daemon=True, args=(ws_url,))
        self.t_ws.start()

        self.lock = Lock()

        self.ws: WebSocketApp = None

        self.flag = True

    def __start(self, ws_url):
        websocket_app = websocket.WebSocketApp(ws_url,
                                    on_open=self.__on_open,
                                    on_message=self.__on_message,
                                    on_error=self.__on_error,
                                    on_close=self.__on_close)
        websocket_app.run_forever()

    def send(self, messageJson):
        if self.ws is not None: 
            self.ws.send(messageJson)  # ส่งข้อมูล JSON ไปยัง ESP32
            # print(f"Sent: {messageJson}")
        else:
            print("WebSocketApp connection is not established.")

    def stop(self):
        self.ws.close()
        self.flag = False

    def __on_message(self, ws: WebSocketApp, message):
        # print(f"Received: {message}")
        try:
            message_json = json.loads(message)
            if message_json["id"] == "gripper":
                self.lock.acquire()
                self.message_json = message_json
                self.lock.release()
        except Exception as error:
            print("Error: ", error)

    def __on_error(self, ws: WebSocketApp, error):
        print(f"Error: {error}")

    def __on_close(self, ws: WebSocketApp, close_status_code, close_msg):
        print("Connection closed. Trying to reconnect...")
        # สร้าง Thread ใหม่เพื่อเชื่อมต่อใหม่
        if self.flag:
            self.__reconnect(ws)

    def __on_open(self, ws: WebSocketApp):
        print("Connection opened")
        self.ws = ws # เอาไปใช้

    def __reconnect(self, ws: WebSocketApp):
        while self.flag:
            try:
                time.sleep(5)  # รอ 5 วินาทีก่อนเชื่อมต่อใหม่
                ws.run_forever()  # พยายามเชื่อมต่อใหม่
                break
            except Exception as e:
                print(f"Reconnect failed: {e}. Retrying...")

class AlienGripper:
    def __init__(self, ip, port, protocal):
        self.alieansock: AlienGripperCommunication = None

        self.setup(ip, port, protocal)

    def setup(self, ip, port, protocal):
        aliensock = AlienGripperCommunication(ip, port, protocal)
        self.setSocket(aliensock)

    def disable(self):
        self.__send("disable")

    def stop(self):
        self.alieansock.stop()

    def setSocket(self, alieansock: AlienGripperCommunication):
        self.alieansock = alieansock

    def __send(self, command: str):
        message = {"id": "arm", "commands": command}
        message_string = json.dumps(message)
        if self.alieansock is not None:
            self.alieansock.send(message_string)

    def hold(self):
        self.__send("hold")

    def release(self):
        self.__send("release")

    def getData(self):
        self.alieansock.lock.acquire()
        message_json = self.alieansock.message_json
        self.alieansock.lock.release()
        return message_json

