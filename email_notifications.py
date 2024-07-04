import datetime
import smtplib
import logging
import time

import settings
import logs


class ProcessFuckedUpError(Exception):
    pass


def send_email(last_time_sent: datetime.datetime, msg: str) -> datetime.datetime:
    now = datetime.datetime.now()
    if now - last_time_sent < settings.TIME_BETWEEN_NOTIFICATIONS:
        return last_time_sent

    smtp_obj = smtplib.SMTP(settings.SERVER, 587)
    smtp_obj.starttls()
    smtp_obj.login(user=settings.EMAIL, password=settings.PASSWD)
    logger.info("Logged in to email account successfully")

    for to in settings.TO:
        try:
            smtp_obj.sendmail(settings.FROM, to, msg)
            logger.info(f"Mail was sent to {to}")
        except Exception as e:
            logger.critical(f"Couldn't send email. Exception {e}")
    return now


# def send_email(*args, **kwargs):  # Debugging
#     print("FUCK")
#     time.sleep(2)
#     return datetime.datetime.now()
