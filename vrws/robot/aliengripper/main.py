import time
from aliengripperapi import AlienGripper
import sys
import signal

flag = True

def task(alien: AlienGripper):
    while flag:
        # commandInput(alien)
        test(alien)


def handle_exit(sig, frame):
    print("กำลังปิดโปรแกรม...")
    alien.disable()
    flag = False
    alien.stop()
    print("โปรแกรมถูกปิดเรียบร้อย")
    sys.exit(0)

def commandInput(alien: AlienGripper):
    command = input("Enter command: ")
    if command == "hold":
        alien.hold()
    elif command == "release":
        alien.release()
    elif command == "disable":
        alien.disable()


def test(alien):
    alien.hold()
    time.sleep(0.01)
    alien.release()
    time.sleep(0.01)
    alien.disable()
    time.sleep(0.01)
    data = alien.getData()
    print(f"id: {data['id']}, Sensors: {data['sensors']}")


signal.signal(signal.SIGINT, handle_exit)

if __name__ == "__main__":
    alien = AlienGripper("192.168.1.10", "81", "ws")
    task(alien)

