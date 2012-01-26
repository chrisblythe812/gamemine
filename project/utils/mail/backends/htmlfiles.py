"""
Email backend that writes messages' bodies to a html files.
"""
import os
import datetime

from django.core.mail.backends.filebased import EmailBackend as FileEmailBackend


class EmailBackend(FileEmailBackend):
    def send_messages(self, email_messages):
        """Write all messages to the stream in a thread-safe way."""
        if not email_messages:
            return
        self._lock.acquire()
        try:
            # The try-except is nested to allow for
            # Python 2.4 support (Refs #12147)
            try:
                stream_created = self.open()
                for message in email_messages:
                    self.stream.write(message.body.encode("utf-8"))
                    self.stream.flush()  # flush after each message
                if stream_created:
                    self.close()
            except:
                if not self.fail_silently:
                    raise
        finally:
            self._lock.release()
        return len(email_messages)

    def _get_filename(self):
        """Return a unique file name."""
        if self._fname is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            fname = "%s-%s.html" % (timestamp, abs(id(self)))
            self._fname = os.path.join(self.file_path, fname)
        return self._fname
