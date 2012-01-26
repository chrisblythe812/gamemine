class MemberRentalPlanBuilder(object):
    """
    Helps to build ``MemberRentalPlan`` model
    """

    def __init__(self, **kwargs):
        """
        Arguments:
        - `**kwargs`: validated kwargs from form
        """
        self.data = kwargs
