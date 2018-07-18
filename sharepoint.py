import json
import urllib3
import requests
from requests_ntlm import HttpNtlmAuth


class Sharepoint:
    auth = None
    form_digest = None
    subsite_url = None

    def __init__(self, domain, username, password, subsite_url):
        urllib3.disable_warnings()
        self.auth(domain, username, password)
        self.subsite_url = subsite_url
        self.form_digest()

    def auth(self, domain, username, password):
        self.auth = HttpNtlmAuth(domain + '\\' + username, password)

    def form_digest(self):
        r = requests.post(
            self.subsite_url + '/_api/contextinfo',
            verify=False,
            auth=self.auth,
            headers={
                'Accept': "application/json",
            },
        )
        self.form_digest = r.json().get('FormDigestValue')

    def add_item(self, list_name, items):
        r = requests.post(
            self.subsite_url + "/_api/Web/lists/getbytitle('" + list_name + "')/Items",
            verify=False,
            auth=self.auth,
            data=json.dumps(self.add_metadata_items(list_name, items)),
            headers={
                'X-RequestDigest': self.form_digest,
                'Accept': "application/json;odata=verbose",
                'content-Type': 'application/json;odata=verbose'
            },
        )
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
