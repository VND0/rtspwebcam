import datetime
import os
import smtplib
import socket
import subprocess

import email_part
import personal_data

VIDEO_FOLDER = 'received_videos'
BUFFER_SIZE = 1024
MAX_SIZE = 30 * 1024 * 1024


def init_server_socket(ip: str, port: int) -> socket.socket:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip, port))
    server_socket.listen(1)
    return server_socket


def get_video_filename(client_addr: str) -> str:
    return f"{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_from_{client_addr[0]}:{client_addr[1]}.mkv"


def cleanup_storage() -> None:
    global cleanup_started
    cleanup_started = True

    total_size = 0
    files = []
    for filename in os.listdir(VIDEO_FOLDER):
        filepath = os.path.join(VIDEO_FOLDER, filename)
        if os.path.isfile(filepath):
            files.append(filepath)
            total_size += os.path.getsize(filepath)
    files.sort(key=lambda x: os.path.getmtime(x))

    while total_size > MAX_SIZE and files:
        oldest_file = files.pop(0)
        total_size -= os.path.getsize(oldest_file)
        os.remove(oldest_file)

    cleanup_started = False


def make_notification(e: Exception):
    global last_time_sent
    now = datetime.datetime.now()
    if now - last_time_sent < email_part.TIME_BETWEEN_NOTIFICATIONS:
        return

    smtp_obj = smtplib.SMTP(personal_data.SERVER, 587)
    smtp_obj.starttls()
    smtp_obj.login(user=personal_data.EMAIL, password=personal_data.PASSWD)

    smtp_obj.sendmail(personal_data.SENDER, personal_data.TO[0], f"""\
From: {personal_data.SENDER}
Subject: Problems with remote server

An error on remote server occured.
{type(e)}:
{str(e)}

If the problem isn't fixed, this message will be sent automatically every 30 minutes.
""")

    smtp_obj.sendmail(personal_data.SENDER, personal_data.TO[1], f"""\
From: {personal_data.SENDER}
Subject: Problems with remote server

An error on remote server occured.
{type(e)}:
{str(e)}

If the problem isn't fixed, this message will be sent automatically every 30 minutes.
""")

    print(f"Mail to {personal_data.TO} has sent.")
    last_time_sent = now


def check_integrity(path: str) -> bool:
    proc = subprocess.Popen(["ffmpeg",
                             "-v", "error",
                             "-i", path,
                             "-f", "null", "-"], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.wait()
    _, stderr = proc.communicate()

    return bool(stderr)


def save_file(client_socket, filename):
    with subprocess.Popen(['ffmpeg', '-i', 'pipe:0', '-c:v', 'copy', '-c:a', 'copy', filename],
                          stdin=subprocess.PIPE) as proc:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            elif proc.poll() is not None:
                raise email_part.ProcessFuckedUpError(proc.stderr.read())
            proc.stdin.write(data)
        print(f"Saved {filename}")


def get_stream(server_socket: socket.socket) -> None:
    print("Listening...")
    client_socket, client_address = server_socket.accept()
    print(f"Connection from {client_address}")

    filename = os.path.join(VIDEO_FOLDER, get_video_filename(client_address))
    try:
        save_file(client_socket, filename)
    except email_part.ProcessFuckedUpError as e:
        make_notification(e)
    finally:
        client_socket.close()
        if not check_integrity(filename) and os.path.exists(filename):
            os.remove(filename)
            print(f"{filename} is corrupted. Deleted.")
    cleanup_storage()


def main() -> None:
    server_socket = init_server_socket('127.0.0.1', 5665)
    try:
        while True:
            get_stream(server_socket)
    except KeyboardInterrupt:
        print("Stopping server")
    finally:
        server_socket.close()


if __name__ == '__main__':
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)
    cleanup_started = False
    last_time_sent = datetime.datetime(2000, 1, 1)

    main()
