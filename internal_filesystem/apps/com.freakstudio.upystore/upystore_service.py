import logging

from mpos import Service

logger = logging.getLogger(__name__)

try:
    from upystore_core import UPyStoreUpdateManager
except ImportError as e:
    UPyStoreUpdateManager = None
    logger.error('appstore_core unavailable: %s', e)


class UPyStoreService(Service):

    def onStart(self, intent):
        if UPyStoreUpdateManager is None:
            return
        UPyStoreUpdateManager.get_instance().start()

    def onDestroy(self):
        if UPyStoreUpdateManager is None:
            return
        UPyStoreUpdateManager.get_instance().stop()
