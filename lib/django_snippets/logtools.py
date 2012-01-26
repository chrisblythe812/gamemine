import logging
from logging.handlers import RotatingFileHandler
import sys
import traceback

__all__ = ['setup', 'uninstall', 'ExceptionsLoggerMiddleware']

LOGFILE_MAX_SIZE = 1024*1024*3
LOGFILE_BACKUP_COUNT = 3


def setup(debug, logging_opts):
    if '__logger_setup_complete' in globals():
        return
    globals()['__logger_setup_complete'] = True
    
    if 'file' in logging_opts:
        logger_handler = RotatingFileHandler(logging_opts['file'], 
                                             maxBytes=LOGFILE_MAX_SIZE, 
                                             backupCount=LOGFILE_BACKUP_COUNT)
    else:
        logger_handler = logging.StreamHandler(sys.stdout)
    
    globals()['__logger_handler'] = logger_handler
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging_opts.get('level', logging.WARNING))
    logger_handler.setFormatter(logging.Formatter(
        logging_opts.get('format', '[%(asctime)s] %(levelname)s %(message)s'), 
        logging_opts.get('datefmt', '%d/%b/%Y %H:%M:%S')))
    logger.addHandler(logger_handler)


def uninstall():
    logger_handler = globals().get('__logger_handler')
    if logger_handler:
        logger = logging.getLogger()
        logger.removeHandler(logger_handler)


class ExceptionsLoggerMiddleware:
    def process_exception(self, request, exception):
        logging.error(traceback.format_exc())
