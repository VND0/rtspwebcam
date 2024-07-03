import datetime

TIME_BETWEEN_NOTIFICATIONS = datetime.timedelta(minutes=30)


class ProcessFuckedUpError(Exception):
    pass
