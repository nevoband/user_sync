import json
import urllib3
import requests
from requests_ntlm import HttpNtlmAuth


class Sharepoint:
    auth = None
    form_digest = None
    subsite_url = None
    site_collection_url = None
    subsite = None

    def __init__(self, domain, username, password, site_collection_url):
        urllib3.disable_warnings()
        self.auth(domain, username, password)
        self.site_collection_url = site_collection_url

    def auth(self, domain, username, password):
        self.domain = domain
        self.username = username
        self.password = password
        self.auth = HttpNtlmAuth(self.domain + '\\' + self.username, self.password)

    def form_digest(self, subsite):
        r = requests.post(
            self.site_collection_url + "/" + subsite + '/_api/contextinfo',
            verify=False,
            auth=self.auth,
            headers={
                'Accept': "application/json",
            },
        )
        self.form_digest = r.json().get('FormDigestValue')

    def add_item(self, items, list_name, subsite):
        if self.subsite != subsite:
            self.form_digest(self.site_collection_url + "/" + subsite)
            self.subsite = subsite
        try:
            r = requests.post(
                self.site_collection_url + "/" + self.subsite + "/_api/Web/lists/getbytitle('" + list_name + "')/Items",
                verify=False,
                auth=self.auth,
                data=json.dumps(self.add_metadata_items(list_name, items)),
                headers={
                    'X-RequestDigest': self.form_digest,
                    'Accept': "application/json;odata=verbose",
                    'content-Type': 'application/json;odata=verbose'
                },
            )
        except Exception as e:
            raise

        return r

    def add_metadata_items(self, list_name, items):
        metadata = {
            '__metadata': {
                'type': 'SP.Data.' + list_name + 'ListItem'
            }
        }
        metadata = self.merge_two_dicts(metadata, items)
        return metadata

    @staticmethod
    def merge_two_dicts(x, y):
        z = x.copy()  # start with x's keys and values
        z.update(y)  # modifies z with y's keys and values & returns None
        return z
