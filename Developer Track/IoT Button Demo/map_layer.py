# Copyright (c) 2018 Deere & Company
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from _common_setup import *
from _demo_helper import DemoHelper

#############################################################################
# Modify the params below to customize your demo
DEMO_PARAMS = {

    # Set this to true if you want to clear out any existing map layer summaries/layers
    'delete_existing_map_layers' : False,

    # A button press can be either SINGLE, DOUBLE, or LONG
    'button_event' : {
        'SINGLE': {
            'map_layer_details' :
            {
                'map_layer_location' : "Mannheim, Germany", # This is the location of the map layer - put in your favorite address
                'map_layer_title' : "Elevation",
                'date' : "2018-10-17",
                'map_layer_image_uri'  : 'https://s3-us-west-2.amazonaws.com/dwd-demo/elevation.png',
                'map_layer_summary_content' : {
                    'value_title_1': "Elevation Average",
                    'value_content_1': "186.35 M",
                    'value_title_2': "Notes",
                    'value_content_2': "Static values/text details can go here...",
                }
            }
        },
        'DOUBLE': {
            'map_layer_details':
            {
                'map_layer_location': "Berlin, Germany",  # This is the location of the map layer - put in your favorite address
                'map_layer_title': "Thermal",
                'date' : "2018-11-05",
                'map_layer_image_uri'  : 'https://s3-us-west-2.amazonaws.com/dwd-demo/thermal.png',
                'map_layer_summary_content': {
                    'value_title_1': "Average Temperature",
                    'value_content_1': "23.4 C",
                    'value_title_2': "Notes",
                    'value_content_2': "Static values/text details can go here...",
                }
            }
        },
        'LONG': {
            'map_layer_details':
            {
                'map_layer_location': "Munich, Germany",  # This is the location of the map layer - put in your favorite address
                'map_layer_title': "SPFH",
                'date' : "2018-08-14",
                'map_layer_image_uri': 'https://www.deere.com/assets/images/region-4/products/hay-and-forage/hay-and-forage-harvesting-equipment/self-propelled-forage-harvesters/8800/8800_sp_harvester_r4d076164_rrd_large_ea6d6176a0bac645a6ad75b3af6cf81b4897b711.jpg',
                'map_layer_summary_content': {
                    'value_title_1': "John Deere Model",
                    'value_content_1': "8800",
                    'value_title_2': "Notes",
                    'value_content_2': "Static values/text details can go here...",
                }
            }
        }
    }
}

#############################################################################
# Lambda entry/invocation point

demo_helper = DemoHelper()

def lambda_handler(event, context):

    demo_helper.setup(event['serialNumber'])
    event_type = event['clickType']
    demo_helper.logger.info("{} - {} press event received".format(demo_helper.iot_button_serial_number, event_type))

    map_layer_details = DEMO_PARAMS['button_event'][event_type]['map_layer_details']

    # Create a field to assign a map layer to (if it doesn't already exist)
    # Use the serial number of the IoT button for the field name to uniquely distinguish your field
    field_name = demo_helper.iot_button_serial_number
    field_uri= demo_helper.create_field(field_name)

    # Delete any previous Map Layer Summaries and underlying Map Layers / File Resources assigned to the field
    if DEMO_PARAMS['delete_existing_map_layers']:
        delete_map_layer_summaries(field_uri)

    # Contribute a map layer for your field with a given image
    contribute_map_layer(field_uri, map_layer_details)

    # Post a notification to alert the user that a map layer has been created
    notification_title = "{} - Map Layer Contributed - {}".format(demo_helper.iot_button_serial_number, map_layer_details['map_layer_title'])
    demo_helper.contribute_notification(field_uri, notification_title, {'severity' : 'LOW', 'type' : 'ANNOUNCEMENT', 'text' : "Map layer contributed!"})

    return 'SUCCESS'

#################################################################################
def contribute_map_layer(field_uri, map_layer_details):

    map_layer_location = map_layer_details['map_layer_location']
    map_layer_title = map_layer_details['map_layer_title']
    map_layer_image_uri = map_layer_details['map_layer_image_uri']

    # Create a Map Layer Summary for your field
    map_layer_summary_uri = create_map_layer_summary(field_uri, map_layer_details)

    # Determine the GPS coordinates for the map layer location specified in DEMO_PARAMS
    gps = demo_helper.determine_gps_coordinates(map_layer_location)

    # Create a Map Layer for the Map Layer Summary
    map_layer_uri = create_map_layer(map_layer_summary_uri, map_layer_title, float(gps['lat']), float(gps['lon']))

    # Create a File Resource for the Map Layer
    file_resource_uri = create_map_layer_file_resource(map_layer_uri, map_layer_title)

    # Upload content to the Map Layer File Resource
    upload_map_layer_file_resource(file_resource_uri, map_layer_image_uri)

#############################################################################
def get_map_layer_summary_list(field_uri):

    # Prep the map layer summaries uri for the given field
    map_layer_summaries_uri = demo_helper.get_relationship_uri(field_uri, "mapLayerSummaries")

    # Request the map summary list
    http_response = demo_helper.process_http_oauth_get_request(map_layer_summaries_uri + ';count=100', "Existing map layer summary list retrieved")
    json_response = http_response.json()

    if json_response['total'] > 0:
        map_layer_summary_list = json_response['values']
    else:
        map_layer_summary_list = []

    return map_layer_summary_list

#############################################################################
def delete_map_layer_summaries(field_uri):

    map_layer_summary_list = get_map_layer_summary_list(field_uri)

    # Loop through all map layer summaries
    for map_layer_summary in map_layer_summary_list:

        map_layer_summary_to_delete_uri = ""

        # Delete any underlying map layers for this map layer summary if they exist
        if map_layer_summary['links'] > 0:
            link_list = map_layer_summary['links']
            for link in link_list:
                if link['rel'] == "self":
                    map_layer_summary_to_delete_uri = link['uri']
                    break

        # If we found a map layer summary - first delete all of its underlying map layer before deleting the summary itself
        if map_layer_summary_to_delete_uri:
            delete_map_layers(map_layer_summary_to_delete_uri)
            demo_helper.process_http_oauth_delete_request(map_layer_summary_to_delete_uri, "Delete existing map layer summary")

#############################################################################
def create_map_layer_summary(field_uri, map_layer_details):

    map_layer_summary_date = map_layer_details['date']
    map_layer_summary_content = map_layer_details['map_layer_summary_content']

    # Prep the contribution definition uris
    contribution_definitions_uri = demo_helper.get_relationship_uri(BASE_URI, "contributionDefinitions")
    map_layer_contribution_definition_uri = "{}/{}".format(contribution_definitions_uri, MAP_LAYER_CONTRIBUTION_DEFINITION)

    body = {
        "links": [
            {
                "rel": "owningOrganization",
                "uri": demo_helper.get_demo_org_uri()
            },
            {
                "rel": "contributionDefinition",
                "uri": map_layer_contribution_definition_uri
            }
        ],
        "title": "DwD Conference",
        "text": "[DwD Conference  - Map Layer Summary](https://developer.deere.com/#!documentation&doc=.%2Fmyjohndeere%2FmapLayerOverview.htm)", # supports link markup!
        "metadata": [
            {
                "name": map_layer_summary_content['value_title_1'],
                "value": map_layer_summary_content['value_content_1'],
            },
            {
                "name": map_layer_summary_content['value_title_2'],
                "value": map_layer_summary_content['value_content_2'],
            }
        ],
        #"dateCreated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        "dateCreated": "{}T00:00:00.000Z".format(map_layer_summary_date)
    }

    # Prep the map layer summaries uri for a given field
    map_layer_summaries_uri = demo_helper.get_relationship_uri(field_uri, "mapLayerSummaries")

    # Post a new map layer summary - pull the new map layer summary uri from the response header
    http_response = demo_helper.process_http_oauth_post_request(map_layer_summaries_uri, body, "Map layer summary created")
    map_layer_summary_uri = http_response.headers['Location']

    return map_layer_summary_uri

#############################################################################
def get_map_layers_list(map_layer_summary_uri):

    map_layers_uri = demo_helper.get_relationship_uri(map_layer_summary_uri, "mapLayers")
    http_response = demo_helper.process_http_oauth_get_request(map_layers_uri + ';count=100', "Existing map layers retrieved")
    json_response = http_response.json()

    if json_response['total'] > 0:
        map_layer_list = json_response['values']
    else:
        map_layer_list = []

    return map_layer_list

#############################################################################
def delete_map_layers (map_layer_summary_uri):

    map_layer_list = get_map_layers_list(map_layer_summary_uri)

    for map_layer in map_layer_list:

        map_layer_to_delete_uri = ""

        # Delete any underlying map layers for this map layer summary if they exist
        if map_layer['links'] > 0:
            link_list = map_layer['links']
            for link in link_list:
                if link['rel'] == "self":
                    map_layer_to_delete_uri = link['uri']
                    break

        # If we found a map layer delete its underlying file resource before deleting the map layer itself
        if map_layer_to_delete_uri:
            delete_map_layer_file_resource(map_layer_to_delete_uri)
            demo_helper.process_http_oauth_delete_request(map_layer_to_delete_uri, "Map layer deleted")

#############################################################################
def create_map_layer(map_layer_summary_uri, map_layer_title, latitude, longitude):

    body = {
       "links": [
          {
             "rel": "owningOrganization",
             "uri": demo_helper.get_demo_org_uri()
          }
       ],
       "title": map_layer_title,
       "extent": {
           "minimumLatitude": latitude,
           "maximumLatitude": latitude + 0.005,  # For this demo - arbitrarily adjust by a small amount to define the extend of the layer
           "minimumLongitude": longitude,
           "maximumLongitude": longitude + 0.01  # For this demo - arbitrarily adjust by a small amount to define the extend of the layer
       },
       "sortName": "02",
       "legends": {
          "unitId": "seeds1ha-1",
          "ranges": [
             {
                #"label": "Custom Range 1",
                "minimum": 0,
                "maximum": 99,
                "hexColor": "#0BA74A",
                "percent": 0.25
             },
             {
                  #"label": "Custom Range 2",
                  "minimum": 100,
                  "maximum": 199,
                  "hexColor": "#00BFFF",
                  "percent": 0.40
            },
            {
                  #"label": " Custom Range 3",
                  "minimum": 200,
                  "maximum": 299,
                  "hexColor": "#DC143C",
                  "percent": 0.15
            },
            {
                  #"label": "Custom Range 4",
                  "minimum": 300,
                  "maximum": 399,
                  "hexColor": "#FFFFFF",
                  "percent": 0.2
            }
          ]
       }
    }

    # Create a new map layer
    map_layers_uri = demo_helper.get_relationship_uri(map_layer_summary_uri, "mapLayers")
    http_response = demo_helper.process_http_oauth_post_request(map_layers_uri, body, "Map layer created")
    map_layer_uri = http_response.headers['Location']

    return map_layer_uri

#############################################################################
def get_map_layer_file_resource(map_layer_uri):

    file_resources_uri = demo_helper.get_relationship_uri(map_layer_uri, "fileResources")
    http_response = demo_helper.process_http_oauth_get_request(file_resources_uri, "Map layer file resource retrieved")
    json_response = http_response.json()

    file_resource_uri = ""

    if 'links' in json_response:
        link_list = json_response['links']
        for link in link_list:
            if link['rel'] == "self":
                file_resource_uri = link['uri']
                break

    return file_resource_uri

#############################################################################
def delete_map_layer_file_resource(map_layer_uri):

    file_resource_uri = get_map_layer_file_resource(map_layer_uri)

    if file_resource_uri:
        demo_helper.process_http_oauth_delete_request(file_resource_uri, "Map layer file resource deleted")

#############################################################################
def create_map_layer_file_resource(map_layer_uri, map_layer_file_resource_title):

    body = {
       "links": [
          {
             "rel": "owningOrganization",
             "uri": demo_helper.get_demo_org_uri()
          }
       ],
       "mimeType": "image/png",
       "metadata": [
          {
             "name": map_layer_file_resource_title,
             "value": map_layer_file_resource_title + ".png"
          }
       ]
    }

    # Create file resource
    file_resource_uri = demo_helper.get_relationship_uri(map_layer_uri, "fileResources")
    http_response = demo_helper.process_http_oauth_post_request(file_resource_uri, body, "File resource created")
    file_resource_uri = http_response.headers['Location']

    return file_resource_uri

#############################################################################
def upload_map_layer_file_resource(file_resource_uri, map_layer_image_uri):

    # Retrieve the demo  image
    http_response = demo_helper.process_http_request(requests.get(map_layer_image_uri), "Demo image retrieved", 200)

    # Upload the demo image to the file resource for the map layer
    demo_helper.process_http_oauth_put_request(file_resource_uri, http_response.content, "File resource uploaded", 204)

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