import datetime
import smtplib
import subprocess
import time

import email_part
import personal_data

RTSP_URL = 'rtsp://192.168.3.59:8080/h264_ulaw.sdp'
LOCALHOST = '127.0.0.1'
PORT = '5665'
MAX_DURATION = datetime.timedelta(seconds=10)

last_time_sent = datetime.datetime(2000, 1, 1)

ffmpeg_cmd = [
    'ffmpeg',
    '-i', RTSP_URL,
    '-c:v', 'copy',
    '-c:a', 'copy',
    '-f', 'matroska',
    "-loglevel", "error",
    f'tcp://{LOCALHOST}:{PORT}'
]


def make_notification(e: Exception) -> None:
    global last_time_sent
    now = datetime.datetime.now()
    if now - last_time_sent < email_part.TIME_BETWEEN_NOTIFICATIONS:
        return

    smtp_obj = smtplib.SMTP(personal_data.SERVER, 587)
    smtp_obj.starttls()
    smtp_obj.login(user=personal_data.EMAIL, password=personal_data.PASSWD)

    for to in personal_data.TO:
        smtp_obj.sendmail(personal_data.SENDER, to, f"""\
From: {personal_data.SENDER}
Subject: Problems with local server

An error on local server occurred.
{type(e)}:
{str(e)}

If the problem isn't fixed, this message will be sent automatically every 30 minutes.
""")

    print(f"Mails have sent to {personal_data.TO}")
    last_time_sent = now


def start_stream() -> None:
    sender_process = subprocess.Popen(ffmpeg_cmd, stderr=subprocess.PIPE)
    started = datetime.datetime.now()
    while datetime.datetime.now() - started < MAX_DURATION:
        if sender_process.poll() is not None:
            time.sleep(0.1)
            _, stderr = sender_process.communicate()
            raise email_part.ProcessFuckedUpError(stderr.decode("utf-8"))
        time.sleep(0.1)
    sender_process.terminate()


if __name__ == '__main__':
    while True:
        try:
            start_stream()
        except email_part.ProcessFuckedUpError as e:
            make_notification(e)
