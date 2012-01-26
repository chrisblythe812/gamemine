"""Command for sending the newsletter"""
from django.core.management.base import NoArgsCommand
from django.utils.encoding import force_unicode
from project.os3marketing.mailer import Mailer
from project.os3marketing.models import Newsletter

  
class Command(NoArgsCommand):
    """Send the newsletter in queue"""
    help = 'Send the newsletter in queue'

    def handle_noargs(self, **options):
        for newsletter in Newsletter.objects.exclude(status__in=[Newsletter.DRAFT,Newsletter.SENT,Newsletter.CANCELED]):
            mailer = Mailer(newsletter)
            if mailer.can_send:
                mailer.run()

        
    
