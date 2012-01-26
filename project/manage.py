#!/usr/bin/env python

import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path = [PROJECT_ROOT+'/..', PROJECT_ROOT+'/../lib/python2.6'] + sys.path

from django.core.management import execute_manager
from project import settings # Assumed to be in the same directory.

if __name__ == "__main__":
    execute_manager(settings)
