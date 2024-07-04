import datetime
import smtplib

import settings


class ProcessFuckedUpError(Exception):
    pass


def send_email(last_time_sent: datetime.datetime, msg: str) -> datetime.datetime:
    now = datetime.datetime.now()
    if now - last_time_sent < settings.TIME_BETWEEN_NOTIFICATIONS:
        return last_time_sent

    smtp_obj = smtplib.SMTP(settings.SERVER, 587)
    smtp_obj.starttls()
    smtp_obj.login(user=settings.EMAIL, password=settings.PASSWD)

    for to in settings.TO:
        try:
            smtp_obj.sendmail(settings.FROM, to, msg)
        except:
            pass
    return now
