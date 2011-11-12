import json
import base64
import urllib2


# Left to be implemented
#
# http://docs.fiesta.cc/list-management-api.html#sending-messages
# http://docs.fiesta.cc/list-management-api.html#messages
# http://docs.fiesta.cc/list-management-api.html#removing-a-list-member
# http://docs.fiesta.cc/list-management-api.html#getting-group-user-information
# http://docs.fiesta.cc/list-management-api.html#getting-group-user-information



class FiestaAPI(object):
    """
    A Python wrapper to the Fiesta.cc API: http://docs.fiesta.cc/
    """
    BASE_URI = "https://api.fiesta.cc/%s"

    trusted_client = True # Will help later when abstracting this code to handle

    client_id = None
    client_secret = None
    domain = None               # For custom domain support
    default_address = None      # Fallback email address to use as owner of lists

    # Strore recent request and response information
    _last_request = None
    _last_response = None
    _last_response_str = None

    def __init__(self, client_id=None, client_secret=None, domain=None, default_address=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.domain = domain
        self.default_address = default_address

    def request(self, request_path, data=None, do_authentication=True, is_json=True):
        """
        Core "worker" for making requests and parsing JSON responses. Data should be a dictionary structured to match
        the fiesta docs.
        """
        uri = self.BASE_URI % request_path
        request = urllib2.Request(uri)

        # Build up the request
        if is_json:
            request.add_header("Content-Type", "application/json")
        if do_authentication:
            if self.client_id is None or self.client_secret is None:
                raise Exception(u"You need to supply a client_id and client_secret to perform an authetnicated requrest")
            basic_auth = base64.b64encode("%s:%s" % (self.client_id, self.client_secret))
            request.add_header("Authorization", "Basic %s" % basic_auth)
        if data is not None:
            request.add_data(json.dumps(data))

        response = self._make_request(request)
        return response

    def _make_request(self, request):
        # TODO: I'm sure all kinds of error checking needs to go here
        response_raw = urllib2.urlopen(request)
        response_str = response_raw.read()
        response = json.loads(response_str)
        self._last_request = request
        self._last_response = response_raw
        self._last_response_str = response_str
        return response

    def hello(self):
        """http://docs.fiesta.cc/index.html#getting-started"""
        path = 'hello'
        response = self.request(path, do_authentication=False)
        return response
    
    def create_group(self, **kwargs):
        """Helper function for creating groups"""
        return FiestaGroup.create(self, **kwargs)


class FiestaGroup(object):
    api = None

    # Fiesta supports each group member having a different address for the group. The name and display_name properties
    # are the defaults that the group will use if you don't choose to override them on a per-member basis.
    name = None
    display_name = None
    description = None
    id = None

    def __init__(self, api, id=None):
        if api is None:
            api = FiestaAPI()
        self.api = api

        self.id = id

    def __unicode__(self):
        return "%s: %s" % (self.name, self.description)

    @staticmethod
    def create(api, name=None, display_name=None, description=None, members=None):
        """
        http://docs.fiesta.cc/list-management-api.html#creating-a-group

        200 character max on the description.
        If the client is not trusted, address is required
        """
        path = 'group'

        data = {}
        # If trusted, these are the only arguments that are available
        if description:
            data['description'] = description
        if api.domain:
            data['domain'] = api.domain

        response = api.request(path, data=data)

        id = response['data']['group_id']
        group = FiestaGroup(api, id)
        group.name = name
        group.display_name = display_name

        # TODO: Allow members to be passed in and auto created using this function

        return group

    @staticmethod
    def by_id(api, id):
        pass

    def guess_name_from_first_user(self, user_id=None):
        """
        Since group names *may* be specified on a per-member basis, knowing the group ID doesn't give us the `name` or
        `display_name`. This method loads the `name` and `display_name` from the first user.

        If you specify a User ID to load it from, this method only requires one API request.
        If you do not specify a User ID, this method requires two API requests.
        """
        # TODO: Finish implementing this function
        if user_id is None:
            # TODO: get membership list
            pass

        # Load the group name

    def add_member(self, address, name=None, display_name=None, welcome_message=None):
        """
        Add a member to a group. http://docs.fiesta.cc/list-management-api.html#adding-members

        Since each member can access a group using their own name, you can override the `group_name` in this method.
        By default, the group will have the name specified on the class level `name` property.

        `welcome_message` should be a dictionary specified according to the docs. If you set it to False, no message
        will be sent. See http://docs.fiesta.cc/list-management-api.html#message for formatting details.
        """

        # TODO: Move this requirement to a decorator
        if self.id is None:
            raise Exception(u"Must specify a group ID when adding a member. Try calling FiestaGroup.by_id().")

        path = 'membership/%s' % self.id
        data = { 'address': address }

        group_name = name or self.name
        if group_name:
            data['group_name'] = group_name

        real_display_name = display_name or self.display_name
        if real_display_name:
            data['display_name'] = real_display_name

        if welcome_message:
            data['welcome_message'] = welcome_message
        elif welcome_message is False:
            data['welcome_message'] = 'false'  # Do not send a welcome message

        response = self.api.request(path, data)
        user_id = response['data']['user_id']
        user = FiestaUser(user_id,address=address,groups=[self])
        return user

class FiestaUser(object):
    id = None
    address = None      # Can't actually be retreived from the API, but can be stored here for your conveinence
    groups = None       # A python list of FiestaGroup objects

    def __init__(self, id, address=None, groups=None):
        self.id = id
        self.address = address
        self.groups = groups

    @staticmethod
    def by_id(api):
        pass



#def add_member_trusted(group_id, member_email, group_name):
#    add_member_uri = "https://api.fiesta.cc/membership/%s"
#
#    api_inputs = {'group_name': group_name,
#                  'address': member_email}
#
#    _create_and_send_request(add_member_uri % group_id, api_inputs)