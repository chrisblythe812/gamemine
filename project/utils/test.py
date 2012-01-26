from django.conf import settings

from django_nose import NoseTestSuiteRunner


def dev(test):
    test.tags = ['dev']
    return test


class SmartDjangoTestSuiteRunner(NoseTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        settings.TESTS = True
        super(SmartDjangoTestSuiteRunner, self).setup_test_environment(**kwargs)
