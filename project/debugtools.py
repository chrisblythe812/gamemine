from logging import debug #@UnusedImport

from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings


class DebugEmailBackend(EmailBackend):
    def _send(self, email_message):
        email_message.bcc = []
        to = []
        for recipient in email_message.to:
            for debug_recipient in settings.DEBUG_EMAIL_RECIPIENTS:
                if recipient.find(debug_recipient) != -1:
                    to.append(recipient)
        if not to:
            debug('Skip sending of message to %s', ', '.join(email_message.to))
            return
        email_message.to = to
        return super(DebugEmailBackend, self)._send(email_message)
