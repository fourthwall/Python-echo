from handlers import *


def handleDiscovery(event):
    items = getItem("")  # get ALL items from the RESTful API
    if not items:  # horrifying error
        return generate_error(event)
    thermostats = [item for item in items if
                   item['type'] == 'Group' and 'Thermostat' in item['tags']]  # get thermostat group items
    devices = []
    # This code defines the actions available to the Echo for a given type in OpenHAB.
    for item in items:
        for tag in item['tags']:
            actions = None
            if tag in ('Lighting', 'Switchable'):
                actionsdict = {
                    "Switch": [
                        "turnOn",
                        "turnOff"
                    ],
                    "Dimmer": [
                        "incrementPercentage",
                        "decrementPercentage",
                        "setPercentage",
                        "turnOn",
                        "turnOff"
                    ],
                    "Color": [
                        "incrementPercentage",
                        "decrementPercentage",
                        "setPercentage",
                        "turnOn",
                        "turnOff",
                        "setColor"
                    ],
                    "Rollershutter": [
                        "setPercentage",
                        "incrementPercentage",
                        "decrementPercentage"
                    ]
                }

                actions = actionsdict[item['type']] if item['type'] in actionsdict else actionsdict[item[
                    'groupType']] if item['type'] == 'Group' and 'groupType' in item and item['groupType'] in actionsdict else None  # set actions for either a group of items of the same type, or a single item.

            elif tag == 'CurrentTemperature':
                if len([x for x in thermostats if x in item['groupNames']]) == 0:  # if this is not part of a Thermostat group, make it available individually
                    actions = [
                        "getTemperatureReading"
                    ]
            elif tag == 'Thermostat' and item['type'] == 'Group':  # actions available for a thermostat group - a collection of items that function together as a thermostat.
                actions = [
                    "incrementTargetTemperature",
                    "decrementTargetTemperature",
                    "setTargetTemperature",
                    "getTargetTemperature",
                    "getTemperatureReading"
                ]
            if actions:
                additional_appliance_details = {
                    "itemType": item['type'],
                    "itemTag": tag,
                    "openhabVersion": "2"
                }
                if tag in ('Thermostat', 'CurrentTemperature'):
                    additional_appliance_details["temperatureFormat"] = "fahrenheit" if "Fahrenheit" in item[
                        'tags'] or "fahrenheit" in item[
                        'tags'] else "celsius"  # set the temperature tag but ONLY on temperature objects
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

    return {
        'header': generate_response(event, "Response"),
        'payload': {
            "discoveredAppliances": devices
        }
    }


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
