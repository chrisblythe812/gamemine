from django.core.urlresolvers import reverse


class AddItemTestCase(object):
    def add_item_to_rentlist(self, item):
        item_pk = str(item.pk)

        url = reverse("rent:add", kwargs={"id": item_pk})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.failUnlessEqual(response.status_code, 200)
