from django.db.models import Q
from project.os3marketing.models import ContactMailingStatus,Newsletter

def get_openings(log, status ,total_contacts):
    total_openings = unique_openings = unique_openings_percent = 0
    if total_contacts > 0 :
        openings = log.filter(status=status)
        total_openings = openings.count()
        if total_openings:
            unique_openings = len(set(openings.values_list('contact', flat=True)))
            unique_openings_percent = float(unique_openings) / float(total_contacts) * 100
    return total_openings,unique_openings,unique_openings_percent

def get_opening_statistics(log,total_contacts):    
    #estatistica de email
    email_total_openings,email_unique_openings,email_unique_openings_percent = get_openings(log,ContactMailingStatus.OPENED,total_contacts)
    context = {'email_total_openings': email_total_openings,
               'email_unique_openings': email_unique_openings,
               'email_unique_openings_percent': email_unique_openings_percent}
    #estatistica de aberturas no site
    site_total_openings,site_unique_openings,site_unique_openings_percent = get_openings(log,ContactMailingStatus.OPENED_ON_SITE,total_contacts)
    context.update({'site_total_openings': site_total_openings,
               'site_unique_openings': site_unique_openings,
               'site_unique_openings_percent': site_unique_openings_percent})
    
    #somando tudo 
    context.update({'total_total_openings': email_total_openings + site_total_openings,})   
    return  context    

def get_clicked_link_statistics(log, total_contacts):
    clicked_links = unique_clicked_links = 0
    if total_contacts > 0:
        links = log.filter(status=ContactMailingStatus.LINK_OPENED) 
        clicked_links = links.count()
        unique_clicked_links = len(set(links.values_list('contact', flat=True)))

    return {'clicked_links': clicked_links,
            'unique_clicked_links': unique_clicked_links,}

def get_unsubscription_statistics(log, total_contacts):
    unsubscriptions = log.filter(status=ContactMailingStatus.UNSUBSCRIPTION)

    total_unsubscriptions = total_unsubscriptions_percent = 0
    if total_contacts > 0:
        total_unsubscriptions = unsubscriptions.count()
        total_unsubscriptions_percent = float(total_unsubscriptions) / float(total_contacts) * 100

    return {'total_unsubscriptions': total_unsubscriptions,
            'total_unsubscriptions_percent': total_unsubscriptions_percent}

def get_newsletter_top_links(log):
    """Retorna os links mais clicados"""
    links = {}
    clicked_links = log.filter(status=ContactMailingStatus.LINK_OPENED)
    
    for cl in clicked_links:
        links.setdefault(cl.link, 0)
        links[cl.link] += 1

    top_links = []
    for link, score in sorted(links.iteritems(), key=lambda (k,v): (v,k), reverse=True):
        unique_clicks = len(set(clicked_links.filter(link=link).values_list('contact', flat=True)))
        top_links.append({'link': link,
                          'total_clicks': score,
                          'unique_clicks': unique_clicks})
        
    return {'top_links': top_links}

def get_statistics(newsletter):
    all_status = ContactMailingStatus.objects.filter(newsletter=newsletter)
    post_sending_status = all_status.filter(creation_date__gte=newsletter.sending_date)
    post_sending_status = post_sending_status.exclude(contact__tester=True)    
    mails_sent = post_sending_status.filter(status__in=[ContactMailingStatus.SENT, ContactMailingStatus.INVALID]).count()

    if newsletter.status == Newsletter.SENT:
        total_contacts = mails_sent
    else:
        total_contacts = newsletter.get_contacts().exclude(tester=True).count()
    reimaining = total_contacts - mails_sent
    if reimaining < 0:
        reimaining = 0    
    statistics = {'tests_sent': all_status.filter(status=ContactMailingStatus.SENT_TEST).count(),
                  'mails_sent': mails_sent,
                  'mails_to_send': total_contacts,
                  'remaining_mails': reimaining,
                  'canceled': newsletter.status == Newsletter.CANCELED}

    statistics.update(get_opening_statistics(post_sending_status, total_contacts))
    statistics.update(get_clicked_link_statistics(post_sending_status, total_contacts))
    statistics.update(get_unsubscription_statistics(post_sending_status, total_contacts))
    statistics.update(get_newsletter_top_links(post_sending_status))
    return statistics


