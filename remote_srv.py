import logging
import os

import cv2
from flask import Flask, request, Response
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

import settings
import logs

app = Flask(__name__)
logger = logs.setup_logger("remote_server.log", logging.INFO)
app.config["MAX_CONTENT_LENGTH"] = settings.REMOTE_MAX_SIZE


def cleanup_storage() -> None:
    total_size = 0
    files = []
    for filename in os.listdir(settings.VIDEO_FOLDER):
        filepath = os.path.join(settings.VIDEO_FOLDER, filename)
        if os.path.isfile(filepath):
            files.append(filepath)
            total_size += os.path.getsize(filepath)
    files.sort(key=lambda x: os.path.getmtime(x))

    while total_size > settings.REMOTE_MAX_SIZE and files:
        logger.warning(f"Too much space taken: {round(total_size / 1024 / 1024, 2)}MB")
        oldest_file = files.pop(0)
        total_size -= os.path.getsize(oldest_file)
        os.remove(oldest_file)
        logger.warning(f"{oldest_file} removed.")


def compare_video_duration(filepath: str) -> bool:
    video = cv2.VideoCapture(filepath)
    return video.get(cv2.CAP_PROP_POS_MSEC) <= (settings.MAX_DURATION.total_seconds() + 1) * 1000


@app.route("/upload", methods=["POST"])
def handle_upload() -> Response:
    logger.info(f"Got request from {request.remote_addr}.")
    if "file" not in request.files:
        logger.critical(f"File not found from {request.remote_addr}.")
        return Response("File not found", 400)

    file_obj = request.files["file"]
    if not file_obj.filename.endswith(settings.VIDEOS_EXTENSION):
        logger.critical(f"Wrong file extension found in {file_obj.filename}")
        return Response("Wrong file extension", 400)

    where = f"{settings.VIDEO_FOLDER}/{secure_filename(file_obj.filename)}"
    try:
        file_obj.save(where)
    except RequestEntityTooLarge:
        logger.critical(f"File {file_obj.filename} too large.")
        return Response("File too large", 413)
    logger.info(f"Saved {where}")

    if not compare_video_duration(where):
        logger.critical(f"File {file_obj.filename} is too long.")
        os.remove(where)
        return Response("File too long", 400)

    cleanup_storage()
    return Response("Saved file successfully", 200)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=settings.REMOTE_PORT)
