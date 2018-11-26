# Copyright (c) 2018 Deere & Company
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from _common_setup import *

#############################################################################
# HTTPS Request Header constants

DEFAULT_GET_REQUEST_HEADERS = {
    'Accept': 'application/vnd.deere.axiom.v3+json',
}

DEFAULT_DELETE_REQUEST_HEADERS = {
    'Accept': 'application/vnd.deere.axiom.v3+json',
}

DEFAULT_POST_REQUEST_HEADERS = {
    'Accept': 'application/vnd.deere.axiom.v3+json',
    'Content-Type': 'application/vnd.deere.axiom.v3+json'
}

FILE_RESOURCE_PUT_HEADER = {
    'Accept': 'application/vnd.deere.axiom.v3+json',
    'Content-Type': 'application/octet-stream'
}

#############################################################################

class DemoHelper:

    #############################################################################
    def setup(self, iot_button_serial_number):

        # Setup the OAuth session
        self.oauth_session = OAuth1Session(CLIENT_KEY, client_secret=CLIENT_SECRET,
                                      resource_owner_key=OAUTH_TOKEN,
                                      resource_owner_secret=OAUTH_TOKEN_SECRET)

        # Setup the logger
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        self.iot_button_serial_number = iot_button_serial_number

        # For the purpose of this demo, avoid going through a proxy to avoid authentication requirements
        if 'https_proxy' in os.environ:
            os.environ.pop('https_proxy')

        self.link_dictionary = dict()

    #############################################################################
    # HTTPS GET Request Helper
    def process_http_oauth_get_request(self, url, custom_text, expected_status=200):
        return self.process_http_request(
                    self.oauth_session.get(url, headers=DEFAULT_GET_REQUEST_HEADERS),
                    custom_text,
                    expected_status)

    #############################################################################
    # HTTPS POST Request Helper
    def process_http_oauth_post_request(self, url, body, custom_text, expected_status=201):
        return self.process_http_request(
                    self.oauth_session.post(url, headers=DEFAULT_POST_REQUEST_HEADERS, data=json.dumps(body, indent=4)),
                    custom_text,
                    expected_status)

    #############################################################################
    # HTTPS PUT Request Helper
    def process_http_oauth_put_request(self, url, body, custom_text, expected_status=203):
        return self.process_http_request(
                    self.oauth_session.put(url, headers=FILE_RESOURCE_PUT_HEADER, data=body),
                    custom_text,
                    expected_status)

    #############################################################################
    # HTTPS DELETE Request Helper
    def process_http_oauth_delete_request(self, url, custom_text, expected_status=204):
        return self.process_http_request(
                    self.oauth_session.delete(url, headers=DEFAULT_DELETE_REQUEST_HEADERS),
                    custom_text,
                    expected_status)

    #############################################################################
    # Generic HTTPS Request Helper
    def process_http_request(self, http_response, custom_text, expected_status):

        result_string = "{}:{} - {} - {} - {}".format( \
            vars(http_response.request)['method'], \
            vars(http_response.request)['url'], \
            str(http_response.status_code), \
            http_response.reason, \
            custom_text)

        if expected_status == http_response.status_code:
            log_message = "{} - SUCCESS - {}".format(self.iot_button_serial_number, result_string)
            self.logger.info(log_message)
        else:
            log_message = "{} - ERROR   - {}".format(self.iot_button_serial_number, result_string)
            self.logger.info(log_message)
            exit(log_message)

        return http_response

    #############################################################################
    # For the purpose of this demo - lets just key off the first organization
    # Note - that you can override the org with the ORG_OVERRIDE constant
    def get_demo_org_uri(self):

        demo_org_link = ""
        organizations_uri = self.get_relationship_uri(BASE_URI, 'organizations')

        if "" == ORG_OVERRIDE:

            http_response = self.process_http_oauth_get_request(organizations_uri, "Getting list of orgs")
            json_response = http_response.json()

            # Return the first org found
            if json_response['total'] > 0:
                link_list = json_response['values'][0]['links']
                for link in link_list:
                    if link['rel'] == 'self':
                        demo_org_link = link['uri']
                        break
        else:
            demo_org_link = "{}/{}".format(organizations_uri, str(ORG_OVERRIDE))

        return demo_org_link

    #################################################, ############################
    def get_relationship_uri(self, resource_uri, relationship):

        relationship_link = ""

        # First check to see if we already have the relationship uri in cached in our dictionary
        if self.link_dictionary.has_key(resource_uri):
            if self.link_dictionary[resource_uri].has_key(relationship):
                relationship_link = self.link_dictionary[resource_uri][relationship]
        else:
            self.link_dictionary[resource_uri] = dict()

        # If we couldn't find a cached relationship link - go find it...
        if relationship_link == "":

            http_response = self.process_http_oauth_get_request(resource_uri, "Getting relationship links")
            json_response = http_response.json()

            if json_response['links'] > 0:
                link_list = json_response['links']
                for link in link_list:
                    if link['rel'] == relationship:
                        relationship_link = link['uri']
                        break

        if relationship_link != "":
            self.link_dictionary[resource_uri][relationship] = relationship_link
        else:
            log_message = "{} - ERROR   - Could not find relationship link for - {}:{}".format(self.iot_button_serial_number, resource_uri, relationship)
            self.logger.info(log_message)
            exit(log_message)

        return relationship_link

    #############################################################################
    def determine_gps_coordinates(self, location):

        url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}".format(location, GOOGLE_MAPS_KEY)
        http_response = self.process_http_request(requests.get(url), "GPS coordinates retrieved from GoogleMaps", 200)
        json_response = http_response.json()

        if len(json_response['results']) > 0 and \
                json_response['results'][0]['geometry']['location']['lat'] and \
                json_response['results'][0]['geometry']['location']['lng']:
            latitude = str(json_response['results'][0]['geometry']['location']['lat'])
            longitude = str(json_response['results'][0]['geometry']['location']['lng'])
        else:
            self.logger.info("{} - ERROR   - Could not lookup GPS coordinate for {} - using default location".format(iot_button.serial_number, location))
            location = "Default location"
            latitude = DEFAULT_LATITUDE
            longitude = DEFAULT_LONGITUDE
            print json.dumps(json_response, indent=4)

        #self.logger.info("{} - {} GPS Coordinates - {}, {}".format(self.iot_button_serial_number, location, latitude, longitude))

        return {"lat":latitude, "lon":longitude}

    #############################################################################
    def create_field(self, field_name):

        field_uri = ""
        expanded_field_name = "Field - {}".format(field_name)

        # Get the list of fields for this org
        fields_uri = self.get_relationship_uri(self.get_demo_org_uri(), "fields")
        http_response = self.process_http_oauth_get_request(fields_uri + ';count=100', "Field list retrieved")
        json_response = http_response.json()

        # Check to see if the field already exists
        if json_response['total'] > 0:
            field_list = json_response['values']
            for field in field_list:
                if field['name'] == expanded_field_name:
                    if field['links'] > 0:
                        link_list = field['links']
                        for link in link_list:
                            if link['rel'] == "self":
                                field_uri = link['uri']
                                break

        # If the field doesn't exist - create it
        if not field_uri:

            body = {
                "name": expanded_field_name,
                "farms": {
                    "farms": [
                        {
                            "name": "My Farm"
                        }
                    ]
                },
                "clients": {
                    "clients": [
                        {
                            "name": "My Client"
                        }
                    ]
                }
            }

            # Post the new field - retrieve the GUID from the header
            http_response = self.process_http_oauth_post_request(fields_uri, body, "Field created")
            field_uri = http_response.headers['Location']


        return field_uri

    #################################################################################
    def contribute_notification(self, field_uri, notification_title, notification_details):

        self.logger.info("Creating notification event - {}".format(notification_title))

        # Prep the contribution definition uris
        contribution_definitions_uri = self.get_relationship_uri(BASE_URI, "contributionDefinitions")
        notification_contribution_definition_uri = "{}/{}".format(contribution_definitions_uri, NOTIFICATION_CONTRIBUTION_DEFINITION)

        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=1)

        body = {
            "links": [
                {
                    "rel": "source",
                    "uri": notification_contribution_definition_uri
                }
            ],
            "eventAssociation": {
                "links": [
                    {
                        "rel": "targetResource",
                        "uri": field_uri
                    }
                ]
            },
            "title": notification_title,
            "text": notification_details['text'],
            "severity": notification_details['severity'],
            "eventType": notification_details['type'],
            "additionalDetails": [
                {
                    "name": "some details",
                    "value": "some value"
                }
            ],
            "timeRange": {
                "startDate": start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "endDate": end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            }
        }

        # Post the notification for the given field
        notification_events_uri = self.get_relationship_uri(BASE_URI, 'notificationEvents')
        self.process_http_oauth_post_request(notification_events_uri, body, "Notification created")

    #################################################################################
    def delete_notifications(self, notification_title):

        # Get the list of active notificaitons
        demo_org_uri = self.get_demo_org_uri()
        notifications_uri = self.get_relationship_uri(demo_org_uri, 'notifications')
        http_response = self.process_http_oauth_get_request(notifications_uri, "Existing notification events retrieved")
        json_response = http_response.json()

        # Look through all the active notifications and delete any that have the title we're looking for
        if json_response['total'] > 0:
            notification_list = json_response['values']
            for notification in notification_list:
                #if notification_title in notification['title']:
                notifications_events_uri = self.get_relationship_uri(BASE_URI, 'notificationEvents')
                notifications_to_delete_uri = "{}/{}".format(notifications_events_uri, notification['sourceEvent'])
                self.process_http_oauth_delete_request(notifications_to_delete_uri, "Notification deleted", 202)

    #################################################################################
