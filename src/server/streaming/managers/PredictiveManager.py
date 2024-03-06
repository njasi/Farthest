from BasicManager import BasicManager

class PredictiveManager(BasicManager):
    """
    Manager class that predicts what should be queued based on a channel's history
    rather than any outside control

    probably have it keep X hrs of videos populated by checking length every
    getnext call

    ignore some actions on this manager, like add action
    """