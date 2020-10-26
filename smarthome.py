from handlers import *


# This method handles discovery events.
# Discovery events arrive as a fixed JSON payload from the AWS cloud service, and wake up the handler.
# The handler dispatches this method in order to enumerate all devices on OpenHAB's restful interface,
# and translate them into a format that can be understood as a native set of Alexa compatible devices
# by returning a JSON payload describing their functions and features in a way that the Echo can understand.


# All JSON payloads are passed as "event" to handler functions.
def handle_discovery(event):
    # get ALL items from the RESTful API, as we are enumerating them.
    items = getItem("")
    # Sanity test for catastrophe. Throw a generic error if we get a malformed payload as there shouldn't be NO items.
    if not items:
        return generate_error(event)
    # Thermostats require special enumeration as they don't exist as a singular item in OpenHAB.
    # They are a group of three. A setpoint, a current temperature, and a heating/cooling mode string.
    # The amazon echo expects a single item, so we enumaerate these three and generate a composite.
    # All three are "tagged" as a thermostat in OpenHAB, so we store those in an array to serialize as a single
    # object later.

    thermostats = [item for item in items if
                   item['type'] == 'Group' and 'Thermostat' in item['tags']]
    # This stores the devices returned in the JSON payload.
    devices = []
    # This code defines the actions available to the Echo for a given type in OpenHAB.
    for item in items:
        # "tags", in OpenHAB's nomenclature, define the capabilties of an item.
        # For instance, "Lighting", or "Switchable", which are bulbs and switches in OpenHAB's device list.
        # These tags translate into different actions to expose to the Echo - so we map them here.
        for tag in item['tags']:
            actions = None
            # Switches and Lights have the same two features to an Echo - they can both be turned on and off.
            if tag in ('Lighting', 'Switchable'):
                actionsdict = {
                    "Switch": [
                        "turnOn",
                        "turnOff"
                    ],
                    # Dimmers require the handling of percentage events as they are variable.
                    "Dimmer": [
                        "incrementPercentage",
                        "decrementPercentage",
                        "setPercentage",
                        "turnOn",
                        "turnOff"
                    ],
                    # Color devices (usually RGB bulbs) require percentages, switching capabilitiy,
                    # and the ability to set Colour
                    "Color": [
                        "incrementPercentage",
                        "decrementPercentage",
                        "setPercentage",
                        "turnOn",
                        "turnOff",
                        "setColor"
                    ],
                    # Rollershutters are percentage devices only.
                    "Rollershutter": [
                        "setPercentage",
                        "incrementPercentage",
                        "decrementPercentage"
                    ]
                }
                # set actions for either a group of items of the same type, or a single item.
                action = item['type']
                # Set of actions for an item
                if action in actionsdict:
                    actions = actionsdict[action]
                # Set actions for a group
                elif action == 'Group' and 'groupType' in item and item['groupType'] in actionsdict:
                    actions = actionsdict[item['groupType']]
                # No actions available
                else:
                    actions = None
            # Temperature sensors can also exist outside
            # of a thermostat group. This allows them to work as individual devices
            # too.
            elif tag == 'CurrentTemperature':
                if len([x for x in thermostats if x in item['groupNames']]) == 0:
                    # if this is not part of a
                    # Thermostat group, make it available individually
                    # and define its action.
                    actions = [
                        "getTemperatureReading"
                    ]
            elif tag == 'Thermostat' and item['type'] == 'Group':
                # actions available for a thermostat group - a
                # collection of items that function together as a thermostat.
                actions = [
                    "incrementTargetTemperature",
                    "decrementTargetTemperature",
                    "setTargetTemperature",
                    "getTargetTemperature",
                    "getTemperatureReading"
                ]
                # if no actions, there are no items - so don't send a malformed payload
            if actions:
                additional_appliance_details = {
                    "itemType": item['type'],
                    "itemTag": tag,
                    "openhabVersion": "2"
                }
                # Check temperature format
                if tag in ('Thermostat', 'CurrentTemperature'):
                    additional_appliance_details["temperatureFormat"] = "fahrenheit" if "Fahrenheit" in item[
                        'tags'] or "fahrenheit" in item['tags'] else "celsius"
                    # To form a complete payload we need to add descriptive information and other such things
                    # So we add generic "via OpenHAB" descriptions along with the names pulled from OpenHAB
                devices.append({
                    "actions": actions,
                    "applianceId": item['name'],
                    "manufacturerName": "openHAB",
                    "modelName": tag,
                    "version": "2",
                    "friendlyName": item['label'],
                    "friendlyDescription": item['type'] + " " + item['name'] + " " + tag + " via openHAB",
                    "isReachable": True,
                    "additionalApplianceDetails": additional_appliance_details
                })

    # Return the payload as serialized JSON enumerating the devices
    return {
        'header': generate_response(event, "Response"),
        'payload': {
            "discoveredAppliances": devices
        }
    }


# Dispatcher for control events - runs relevant function for payload request
def handle_control(event):
    name = event['header']['name']
    singletons = {
        "GetTemperatureReadingRequest": current_temperature,
        "GetTargetTemperatureRequest": target_temperature,
        "SetColorRequest": colour_request
    }
    return switch_request(event) if name in ('TurnOnRequest', 'TurnOffRequest') else singletons[
        name](event) if name in singletons else percentage_request(
        event) if "PercentageRequest" in name else temperature_request(
        event) if "TargetTemperatureRequest" in name else generate_error(event)
