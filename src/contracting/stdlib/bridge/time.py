from datetime import datetime as dt
from datetime import timedelta as td
from types import ModuleType


# Redefine a controlled datetime object that feels like a regular Python datetime object but is restricted so that we
# can regulate the user interaction with it to prevent security attack vectors. It may seem redundant, but it guarantees
# security.
SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = 86400
SECONDS_IN_WEEK = 604800


def get_raw_seconds(weeks, days, hours, minutes, seconds):
    m_sec = minutes * SECONDS_IN_MINUTE
    h_sec = hours * SECONDS_IN_HOUR
    d_sec = days * SECONDS_IN_DAY
    w_sec = weeks * SECONDS_IN_WEEK

    raw_seconds = seconds + m_sec + h_sec + d_sec + w_sec

    return raw_seconds


class Datetime:
    def __init__(self, year, month, day, hour=0, minute=0, second=0, microsecond=0):
        self._datetime = dt(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond
        )

        self.year = self._datetime.year
        self.month = self._datetime.month
        self.day = self._datetime.day
        self.hour = self._datetime.hour
        self.minute = self._datetime.minute
        self.second = self._datetime.second
        self.microsecond = self._datetime.microsecond

    def __lt__(self, other):
        if type(other) != Datetime:
            raise TypeError(f'{type(other)} is not a Datetime!')
        return self._datetime < other._datetime

    def __le__(self, other):
        if type(other) != Datetime:
            raise TypeError(f'{type(other)} is not a Datetime!')
        return self._datetime <= other._datetime

    def __eq__(self, other):
        if type(other) != Datetime:
            raise TypeError(f'{type(other)} is not a Datetime!')
        return self._datetime == other._datetime

    def __ge__(self, other):
        if type(other) != Datetime:
            raise TypeError(f'{type(other)} is not a Datetime!')
        return self._datetime >= other._datetime

    def __gt__(self, other):
        if type(other) != Datetime:
            raise TypeError(f'{type(other)} is not a Datetime!')
        return self._datetime > other._datetime

    def __ne__(self, other):
        if type(other) != Datetime:
            raise TypeError(f'{type(other)} is not a Datetime!')
        return self._datetime != other._datetime

    def __sub__(self, other):
        if isinstance(other, Datetime):
            delta = self._datetime - other._datetime
            return Timedelta(days=delta.days, seconds=delta.seconds)
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, Timedelta):
            return Datetime._from_datetime(self._datetime + other._timedelta)
        return NotImplemented

    def __str__(self):
        return str(self._datetime)

    def __repr__(self):
        return self.__str__()

    @classmethod
    def _from_datetime(cls, d: dt):
        return cls(year=d.year,
                   month=d.month,
                   day=d.day,
                   hour=d.hour,
                   minute=d.minute,
                   second=d.second,
                   microsecond=d.microsecond)
    
    @classmethod
    def strptime(cls, date_string, format):
        d = dt.strptime(date_string, format)
        return cls._from_datetime(d)

class Timedelta:
    def __init__(self, weeks=0,
                       days=0,
                       hours=0,
                       minutes=0,
                       seconds=0):

        self._timedelta = td(
            weeks=int(weeks), days=int(days), hours=int(hours), minutes=int(minutes), seconds=int(seconds)
        )

        # For fast access to how many hours are in a timedelta.
        self.__raw_seconds = get_raw_seconds(
            weeks=int(weeks), days=int(days), hours=int(hours), minutes=int(minutes), seconds=int(seconds)
        )

    def __lt__(self, other):
        if type(other) != Timedelta:
            raise TypeError(f'{type(other)} is not a Timedelta!')
        return self._timedelta < other._timedelta

    def __le__(self, other):
        if type(other) != Timedelta:
            raise TypeError(f'{type(other)} is not a Timedelta!')
        return self._timedelta <= other._timedelta

    def __eq__(self, other):
        if type(other) != Timedelta:
            raise TypeError(f'{type(other)} is not a Timedelta!')
        return self._timedelta == other._timedelta

    def __ge__(self, other):
        if type(other) != Timedelta:
            raise TypeError(f'{type(other)} is not a Timedelta!')
        return self._timedelta >= other._timedelta

    def __gt__(self, other):
        if type(other) != Timedelta:
            raise TypeError(f'{type(other)} is not a Timedelta!')
        return self._timedelta > other._timedelta

    def __ne__(self, other):
        if type(other) != Timedelta:
            raise TypeError(f'{type(other)} is not a Timedelta!')
        return self._timedelta != other._timedelta

    # Operator implementations inspired by CPython implementations
    def __add__(self, other):
        if isinstance(other, Timedelta):
            return Timedelta(days=self._timedelta.days + other._timedelta.days,
                             seconds=self._timedelta.seconds + other._timedelta.seconds)

        if isinstance(other, Datetime):
            d = other._datetime + self._timedelta
            return Datetime._from_datetime(d)

        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Timedelta):
            return Timedelta(days=self._timedelta.days - other._timedelta.days,
                             seconds=self._timedelta.seconds - other._timedelta.seconds,)

        if isinstance(other, Datetime):
            d = other._datetime - self._timedelta
            return Datetime._from_datetime(d)

        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, Timedelta):
            return Timedelta(days=self._timedelta.days * other._timedelta.days,
                             seconds=self._timedelta.seconds * other._timedelta.seconds)
        elif isinstance(other, int):
            return Timedelta(days=self._timedelta.days * other,
                             seconds=self._timedelta.seconds * other)

        return NotImplemented

    def __str__(self):
        return str(self._timedelta)

    def __repr__(self):
        return self.__str__()

    # Accesses raw seconds and does a simple modulo to get the number of the component in the total seconds
    @property
    def seconds(self):
        return self.__raw_seconds

    @property
    def minutes(self):
        return self.__raw_seconds // SECONDS_IN_MINUTE

    @property
    def hours(self):
        return self.__raw_seconds // SECONDS_IN_HOUR

    @property
    def days(self):
        return self.__raw_seconds // SECONDS_IN_DAY

    @property
    def weeks(self):
        return self.__raw_seconds // SECONDS_IN_WEEK


WEEKS = Timedelta(weeks=1)
DAYS = Timedelta(days=1)
HOURS = Timedelta(hours=1)
MINUTES = Timedelta(minutes=1)
SECONDS = Timedelta(seconds=1)

datetime_module = ModuleType('datetime')
datetime_module.datetime = Datetime
datetime_module.timedelta = Timedelta
datetime_module.WEEKS = WEEKS
datetime_module.DAYS = DAYS
datetime_module.HOURS = HOURS
datetime_module.MINUTES = MINUTES
datetime_module.SECONDS = SECONDS

exports = {
    'datetime': datetime_module
}
