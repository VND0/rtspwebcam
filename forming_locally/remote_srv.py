import logging
import os

from flask import Flask, request, Response

import settings
import logs

app = Flask(__name__)
logger = logs.setup_logger("remote_server.log", logging.INFO)


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


@app.route("/upload", methods=["POST"])
def handle_upload() -> Response:
    logger.info(f"Got request from {request.remote_addr}.")
    if "file" not in request.files:
        logger.critical(f"File not found from {request.remote_addr}.")
        return Response("File not found", 400)

    file_obj = request.files["file"]
    where = f"{settings.VIDEO_FOLDER}/{file_obj.filename}"
    file_obj.save(where)
    logger.info(f"Saved {where}")

    cleanup_storage()
    return Response("Saved file successfully", 200)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=settings.REMOTE_PORT)
