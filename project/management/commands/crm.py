from datetime import datetime

from django.core.management.base import LabelCommand

from project.crm.models import FeedbackifyFeedback


class Command(LabelCommand):
    args = '[test_data]'
    help = 'Working with catalog'
    label = 'command'

    def handle_label(self, label, **options):
        if label == 'test_data':
            self.do_test_data()

    def do_test_data(self):
        print 'Create test feedbacks...'
        for i in xrange(10):
            FeedbackifyFeedback(timestamp=datetime.now(),
                                form_id=1,
                                item_id=1,
                                score=10,
                                category='category',
                                subcategory='subcategory',
                                feedback='Feedback %s' % i,
                                email='roman@bravetstudio.com'
                                ).save()
