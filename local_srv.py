import datetime
import logging
import os
import subprocess
import threading
import time

import requests

import logs
import settings

logger = logs.setup_logger("local_server.log", loglevel=logging.INFO)


def send_video_file(filepath: str) -> None:
    filename = filepath.split("/")[-1]  # WARNING: may not work on Windows, only UNIX-like systems are supported
    with open(filepath, "rb") as f:
        files = {"file": (filename, f)}
        r = requests.post(settings.REMOTE_URL, files=files)

        if r.status_code != 200:
            logger.critical(f"{r.status_code}. Failed to send {filename}. {r.text}")
        else:
            logger.info(f"200. Sent {filename} successfully.")
    cleanup_storage()


def cleanup_storage() -> None:
    total_size = 0
    files = []
    for filename in os.listdir(settings.VIDEO_FOLDER):
        filepath = os.path.join(settings.VIDEO_FOLDER, filename)
        if os.path.isfile(filepath):
            files.append(filepath)
            total_size += os.path.getsize(filepath)
    files.sort(key=lambda x: os.path.getmtime(x))

    while total_size > settings.LOCAL_MAX_SIZE and files:
        logger.warning(f"Too much space taken: {round(total_size / 1024 / 1024, 2)}MB")
        oldest_file = files.pop(0)
        total_size -= os.path.getsize(oldest_file)
        os.remove(oldest_file)
        logger.warning(f"{oldest_file} removed.")


def get_video_path_and_name() -> str:
    return f"{settings.VIDEO_FOLDER}/{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}{settings.VIDEOS_EXTENSION}"


def get_ffmpeg_proc(filename: str) -> subprocess.Popen:
    return subprocess.Popen(["ffmpeg", "-rtsp_transport", "tcp",
                             "-i", settings.RTSP_URL,
                             "-c:v", "copy", "-c:a", "copy",
                             "-loglevel", "error", filename], stderr=subprocess.PIPE, stdout=subprocess.PIPE)


def main() -> None:
    while True:
        filename = get_video_path_and_name()
        now = datetime.datetime.now()

        logger.info("Stream handling started.")
        with get_ffmpeg_proc(filename) as proc:
            while True:
                while datetime.datetime.now() - now < settings.MAX_DURATION:
                    if proc.poll() is not None:
                        _, stderr = proc.communicate()
                        logger.critical(f"Problems with handling. {stderr}")
                    time.sleep(0.1)

                threading.Thread(target=send_video_file, args=(filename,)).start()

                filename = get_video_path_and_name()
                logger.info("Changing file.")
                proc.terminate()
                proc = get_ffmpeg_proc(filename)
                now = datetime.datetime.now()


if __name__ == '__main__':
    if not os.path.exists(settings.VIDEO_FOLDER):
        os.makedirs(settings.VIDEO_FOLDER)
    logger.info("Server started.")
    try:
        main()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt. Stopping server.")
    logger.info("Server stopped.")
