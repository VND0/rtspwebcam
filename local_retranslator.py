import datetime
import logging
import subprocess
import time

import email_notifications
import logs
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
    logger.info("Stream started")
    while datetime.datetime.now() - started < settings.MAX_DURATION:
        if sender_process.poll() is not None:
            time.sleep(0.1)
            _, stderr = sender_process.communicate()
            logger.error("Streaming failed.")
            raise email_notifications.ProcessFuckedUpError(stderr.decode("utf-8"))
        time.sleep(0.1)
    logger.info(
        f"Max video duration ({round(settings.MAX_DURATION.total_seconds() / 60, 2)} min) reached. Restarting stream.")
    sender_process.terminate()
    logger.info("Stream stopped")


if __name__ == '__main__':
    logger = logs.setup_logger("local_retranslator.log", logging.DEBUG)

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
            if datetime.datetime.now() - last_time_sent > settings.TIME_BETWEEN_NOTIFICATIONS:
                logger.warning("Sending emails.")
                last_time_sent = email_notifications.send_email(last_time_sent, message)
        except KeyboardInterrupt as e:
            logger.info(f"{e}. Stopping streaming.")
            exit(0)
