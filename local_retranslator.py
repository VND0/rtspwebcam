import datetime
import subprocess
import time

import email_notifications
import settings

last_time_sent = datetime.datetime(2000, 1, 1)

ffmpeg_cmd = [
    'ffmpeg',
    '-i', settings.RTSP_URL,
    '-c:v', 'copy',
    '-c:a', 'copy',
    '-f', 'matroska',
    "-loglevel", "error",
    f'tcp://{settings.LOCALHOST}:{settings.PORT}'
]


def start_stream() -> None:
    sender_process = subprocess.Popen(ffmpeg_cmd, stderr=subprocess.PIPE)
    started = datetime.datetime.now()
    while datetime.datetime.now() - started < settings.MAX_DURATION:
        if sender_process.poll() is not None:
            time.sleep(0.1)
            _, stderr = sender_process.communicate()
            raise email_notifications.ProcessFuckedUpError(stderr.decode("utf-8"))
        time.sleep(0.1)
    sender_process.terminate()


if __name__ == '__main__':
    while True:
        try:
            start_stream()
        except email_notifications.ProcessFuckedUpError as e:
            message = f"""\
From: {settings.FROM}
Subject: Problems with local server

An error on local server occurred.
{type(e)}:
{str(e)}

If the problem isn't fixed, this message will be sent automatically every 30 minutes.
"""
            email_notifications.send_email(last_time_sent, message)
