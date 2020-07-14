import logging
import traceback

from spyders import EGRNApplication
from schemas import Application, ApplicationStatus
from types import FunctionType

import services


def _mark_application_as_error(application_id):
    application = services.get_application(application_id)
    application.state = ApplicationStatus.error
    application = services.update_application(application.id,
                                              dict(application))
    return application


def _run_application_with_exception(function: FunctionType, application_id: int):
    try:
        function(application_id)
    except Exception:
        _mark_application_as_error(application_id)
        logging.error('spyder exception %s', traceback.format_exc())
    except BaseException:
        _mark_application_as_error(application_id)
        logging.error('stopped by worker %s', traceback.format_exc())


def order_application(application: Application):
    '''Order application on rosreestr.ru'''
    logging.info('application added: %s' % str(application))
    spyder = EGRNApplication()
    _run_application_with_exception(spyder.order_application, application.id)
    spyder.close()


def update_application_data(application: Application):
    '''Update application data (status, result) for rosreestr.ru'''
    logging.info('updating application data: %s' % str(application))
    spyder = EGRNApplication()
    _run_application_with_exception(spyder.update_application_state, application.id)
    spyder.close()
