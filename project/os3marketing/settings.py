from django.conf import settings
TRACKING_IMAGE = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAAAXNSR0IArs4c6QAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9kKEwwvINGR5lYAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC'
#MEDIA_URL = getattr(settings, 'NEWSLETTER_MEDIA_URL', '/edn/')
UNSUBSCRIPTION_URL = getattr(settings, 'OS3MARKETING_UNSUBSCRIPTION_URL','{% url os3marketing_mailinglist_unsubscribe slug=newsletter.slug,uidb36=uidb36,token=token %}')
