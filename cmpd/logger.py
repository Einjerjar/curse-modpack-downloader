import logging
import sys

from enum import Enum


class FilterRestrictions(Enum):
    BELOW = -2
    BELOW_AND_EXACT = -1
    EXACT = 0
    ABOVE_AND_EXACT = 1
    ABOVE = 2
    EXCLUDE = 3
    RANGE_EXC = 4
    RANGE_INC = 5


class LogFilter(object):
    def __init__(self, lvl, restrict=FilterRestrictions.EXACT):
        self.restrict = restrict
        self.lvl = lvl

        f = FilterRestrictions

        # TODO : Kinda naive implementation ?? no better ideas atm
        # ps : holy nuts, actually works well, specially the range one, lol
        self.filters = {
            f.BELOW: self.below,
            f.BELOW_AND_EXACT: self.below_e,
            f.EXACT: self.exact,
            f.ABOVE_AND_EXACT: self.above_e,
            f.ABOVE: self.above,
            f.EXCLUDE: self.exclude,
            f.RANGE_EXC: self.range_exc,
            f.RANGE_INC: self.range_inc
        }
        self.m_filter = self.filters[self.restrict]

    def below(self, lvl: int):
        return lvl < self.lvl

    def below_e(self, lvl: int):
        return lvl <= self.lvl

    def exact(self, lvl: int):
        return lvl == self.lvl

    def above_e(self, lvl: int):
        return lvl >= self.lvl

    def above(self, lvl: int):
        return lvl > self.lvl

    def exclude(self, lvl: int):
        return lvl != self.lvl

    def range_exc(self, lvl: int):
        return self.lvl[1] > lvl > self.lvl[0]

    def range_inc(self, lvl: int):
        return self.lvl[1] >= lvl >= self.lvl[0]

    def filter(self, log: logging.LogRecord):
        return self.m_filter(log.levelno)


# -----------------------------------------------
# https://stackoverflow.com/a/13638084
HIDDEN_EXCEPTION = 60


def h_except(self, message, *args, **kwargs):
    if self.isEnabledFor(HIDDEN_EXCEPTION):
        self._log(HIDDEN_EXCEPTION, message, args, **kwargs)


logging.addLevelName(HIDDEN_EXCEPTION, 'H_EXCEPT')
logging.Logger.h_except = h_except

logging.HIDDEN_EXCEPTION = HIDDEN_EXCEPTION
# https://stackoverflow.com/a/13638084
# -----------------------------------------------

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_fmt = logging.Formatter('%(asctime)s :: %(filename)12s:%(lineno)-4s :: %(levelname)-7s :: %(message)s',
                            '%Y-%m-%d %I:%M:%S %p')

# INFO and DEBUG
log_ich = logging.StreamHandler(sys.stdout)
log_ich.setLevel(logging.DEBUG)
log_ich.setFormatter(log_fmt)
log_ich.addFilter(LogFilter(logging.INFO, FilterRestrictions.BELOW_AND_EXACT))

# WARNING TILL CRITICAL (NO H_EXCEPT)
log_ech = logging.StreamHandler(sys.stderr)
log_ech.setLevel(logging.DEBUG)
log_ech.setFormatter(log_fmt)
log_ech.addFilter(LogFilter([logging.WARNING, logging.CRITICAL], FilterRestrictions.RANGE_INC))

log_fh = logging.FileHandler('cmpd2.log', 'w')
log_fh.setLevel(logging.DEBUG)
log_fh.setFormatter(log_fmt)

logger.addHandler(log_ich)
logger.addHandler(log_ech)
logger.addHandler(log_fh)
