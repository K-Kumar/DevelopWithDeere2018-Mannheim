# Copyright (c) 2018 Deere & Company
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from _common_setup import *
from _demo_helper import DemoHelper

#############################################################################
# Modify the params below to customize your demo
DEMO_PARAMS = {

    # This is the location of the map layer - put in your favorite address
    'asset_location' : "Mannheim, Germany",

    # See asset documentation - https://developer.deere.com/#!documentation&doc=.%2Fmyjohndeere%2FiotDeviceSupportOverview.htm
    'asset_details': {

        'category'              : 'DEVICE',
        'type'                  : 'SENSOR',
        'sub_type'              : 'OTHER',
        'text'                  : "My IoT Device",

        'measurement_1_name'    : "[Value #1](https://developer.deere.com/#!documentation&doc=.%2Fmyjohndeere%2FiotDeviceSupportOverview.htm)", # supports link markup!
        'measurement_1_value'   : "1.234",
        'measurement_1_unit'    : "liters",

        'measurement_2_name'    : "[Value #2](https://developer.deere.com/#!documentation&doc=.%2Fmyjohndeere%2FiotDeviceSupportOverview.htm)", # supports link markup!
        'measurement_2_value'   : "302.5",
        'measurement_2_unit'    : "rpm",

        'measurement_3_name'    : "[Value #3](https://developer.deere.com/#!documentation&doc=.%2Fmyjohndeere%2FiotDeviceSupportOverview.htm)", # supports link markup!
        'measurement_3_value'   : "25365",
        'measurement_3_unit'    : "ha",
    }
}


#############################################################################
# Lambda entry/invocation point

demo_helper = DemoHelper()

def lambda_handler(event, context):

    demo_helper.setup(event['serialNumber'])
    event_type = event['clickType']
    demo_helper.logger.info("{} - {} press event received".format(demo_helper.iot_button_serial_number, event_type))

    asset_title = demo_helper.iot_button_serial_number
    asset_location = DEMO_PARAMS['asset_location']
    asset_details = DEMO_PARAMS['asset_details']

    # Upon a SINGLE press - create an asset if it doesn't already exist and update its location
    if 'SINGLE' == event_type:
        asset_uri = create_asset(asset_title, asset_details)
        update_asset(asset_title, asset_uri, asset_location, asset_details)
        notification_text = 'Asset Updated'

    # Upon a DOUBLE press - remove the asset completely
    elif 'DOUBLE' == event_type:
        delete_asset(asset_title)
        notification_text = 'Asset Deleted'

    elif 'LONG' == event_type:
        print "Nothing to do - no action defined for LONG event..."

    # Post a notification to alert the user that a map layer has been created
    field_name = demo_helper.iot_button_serial_number
    field_uri = demo_helper.create_field(field_name)
    notification_title = "{} - {} - {} - {}".format(demo_helper.iot_button_serial_number, notification_text, asset_details['category'], asset_details['type'])
    demo_helper.contribute_notification(field_uri, notification_title, {'severity' : 'LOW', 'type' : 'ANNOUNCEMENT', 'text' : notification_text})

    return 'SUCCESS'

#############################################################################
def get_asset(asset_name):

    asset_uri = ''

    # Get this list of assets for this org
    demo_org_uri = demo_helper.get_demo_org_uri()
    assets_uri = demo_helper.get_relationship_uri(demo_org_uri, 'assets')
    http_response = demo_helper.process_http_oauth_get_request(assets_uri  + ';count=100', "Asset list retrieved")
    json_response = http_response.json()

    # Check if the asset exist and return it if it does
    if json_response['total'] > 0:
        asset_list = json_response['values']
        for asset in asset_list:
            if asset['title'] == asset_name:
                if asset['links'] > 0:
                    link_list = asset['links']
                    for link in link_list:
                        if link['rel'] == "self":
                            asset_uri = link['uri']
                            break

    return asset_uri

#############################################################################
def create_asset(asset_title, asset_details):

    # First check to see if the asset already exists
    asset_uri = get_asset(asset_title)

    # If the asset doesn't exist - create it...
    if asset_uri == '':

        # Prep the contribution uris
        contribution_definitions_uri = demo_helper.get_relationship_uri(BASE_URI, "contributionDefinitions")
        notification_contribution_definition_uri = "{}/{}".format(contribution_definitions_uri, ASSET_CONTRIBUTION_DEFINITION)

        body = {
            "title": asset_title,
            "text": asset_details['text'],
            "assetCategory": asset_details['category'],
            "assetType": asset_details['type'],
            "assetSubType": asset_details['sub_type'],
            "links": [
                {
                    "@type": "Link",
                    "rel": "contributionDefinition",
                    "uri": notification_contribution_definition_uri
                }
            ]
        }

        # Post the asset - retrieve the asset guid from the response header
        demo_org_uri = demo_helper.get_demo_org_uri()
        assets_uri = demo_helper.get_relationship_uri(demo_org_uri, 'assets')
        http_response = demo_helper.process_http_oauth_post_request(assets_uri, body, "New asset created")
        asset_uri =  http_response.headers['Location']

    return asset_uri

#############################################################################
def update_asset(asset_title, asset_uri, asset_location, asset_details):

    #############################################################################
    # Determine GPS Coordinates for location
    # Determine the GPS coordinates for the address specified by MAP_LAYER_LOCATION
    gps = demo_helper.determine_gps_coordinates(asset_location)

    # For the purpose of this demo, randomly alter the location of the asset to make it appear that has
    # changed location in OpsCenter
    latitude = str(float(gps['lat']) + random.uniform(-0.1,0.1))
    longitude = str(float(gps['lon']) + random.uniform(-0.1,0.1))

    #############################################################################
    # Update the asset location and associated measurement

    body = [{
        "@type": "ContributedAssetLocation",
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "geometry": "{\"type\": \"Feature\",\"geometry\": {\"geometries\": [{\"coordinates\": [" + longitude + "," + latitude + "],\"type\": \"Point\"}],\"type\": \"GeometryCollection\"}}",
        "measurementData": [{
            "@type": "BasicMeasurement",
            "name": asset_details['measurement_1_name'],
            "value":asset_details['measurement_1_value'],
            "unit": asset_details['measurement_1_unit'],
        }, {
            "@type": "BasicMeasurement",
            "name": asset_details['measurement_2_name'],
            "value": asset_details['measurement_2_value'],
            "unit": asset_details['measurement_2_unit'],
        }, {
            "@type": "BasicMeasurement",
            "name": asset_details['measurement_3_name'],
            "value": asset_details['measurement_3_value'],
            "unit": asset_details['measurement_3_unit'],
        }]

    }]

    # Post an update to the asset's location
    asset_locations_uri = demo_helper.get_relationship_uri(asset_uri, "locations")
    http_response = demo_helper.process_http_oauth_post_request(asset_locations_uri, body, "Asset location updated")

#############################################################################
def delete_asset(asset_title):

    asset_to_delete_uri = get_asset(asset_title)

    if asset_to_delete_uri:
        demo_helper.process_http_oauth_delete_request(asset_to_delete_uri, "Asset deleted")

#############################################################################
# Test Code

# def lambda_test():
#     event = {
#         'serialNumber': 'G030MD0000000000',
#         'batteryVoltage': 'xxmV',
#         'clickType': 'SINGLE'
#     }
#
#     lambda_handler(event, "")
#
#
# lambda_test()
