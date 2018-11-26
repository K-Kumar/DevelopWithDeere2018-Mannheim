# Copyright (c) 2018 Deere & Company
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from _common_setup import *
from _demo_helper import DemoHelper

#############################################################################
# Modify the params below to customize your demo
DEMO_PARAMS = {

    # A button press can be either SINGLE, DOUBLE, or LONG
    # See notification documentation - https://developer.deere.com/#!documentation&doc=myjohndeere%2Fnotifications.htm
    'button_event' : {
        'SINGLE': {
            'notification_details' : {
                'severity'  : 'LOW',
                'type'      : 'ANNOUNCEMENT',
                'text'      : "Map layer contributed",
            }
        },
        'DOUBLE': {
            'notification_details': {
                'severity'  : 'MEDIUM',
                'type'      : 'ORGANIZATION',
                'text'      : "John added as org staff member",
            }
        },
        'LONG': {
            'notification_details': {
                'severity'  : 'HIGH',
                'type'      : 'MACHINE_INSIGHTS',
                'text'      : "Tractor needs service!",
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

    notification_details = DEMO_PARAMS['button_event'][event_type]['notification_details']
    notification_title = "{} - {} - {}".format(demo_helper.iot_button_serial_number, notification_details['severity'], notification_details['type'])

    # Notifications are assigned to a target resource - create a field to be used as our target resource (if it doesn't already exist)
    # Use the serial number of the IoT button for the field name to uniquely distinguish your field
    field_name = demo_helper.iot_button_serial_number
    field_uri = demo_helper.create_field(field_name)

    # Post a notification with specified parameters for the given button press type
    demo_helper.contribute_notification(field_uri, notification_title, notification_details)

    return 'SUCCESS'


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