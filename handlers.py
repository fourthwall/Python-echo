import datetime
from api import *
from tools import *


def current_temperature(event):
    item = getItem(event['payload']['appliance']['applianceId'])
    if not item:
        return generate_error(event, "No current temperature data found")
    if item['type'] == "Group":
        items = generate_thermostat(item['members'])
        item = items['currentTemperature']
    try:
        number = float(item['state'])
    except:
        return generate_error(event, "Temperature data invalid")
    return {
        'header': generate_response(event, "Response"),
        'payload': {
            "temperatureReading": {
                "value": convert_to_c(number) if is_fahrenheit(event) else number
            },
            "applianceResponseTimestamp": datetime.datetime.now().isoformat()
        }
    }


def percentage_request(event):
    name = event['payload']['appliance']['applianceId']
    if event['header']['name'] == 'SetPercentageRequest':
        return {'header': generate_response(event, "Confirmation"), 'payload': {}} if postCommand(name, str(
            event['payload']['percentageState']['value'])) else generate_error(event)
    elif 'PercentageRequest' in event['header']['name']:
        item = getItem(name)
        value = float(event['payload']['deltaPercentage']['value'])
        if not item:
            return generate_error(event)
        try:
            number = float(item['state'])
        except:
            return generate_error(event, "No existing percentage")
        values = {
            'IncrementPercentageRequest': number + value,
            'DecrementPercentageRequest': number - value
        }
        value = values[event['header']['name']]
        value = 100 if value > 100 else 0 if value < 0 else value
        return {
            'header': generate_response(event, "Confirmation"),
            'payload': {}
        } if postCommand(name, str(
            value)) else generate_error(event)


def target_temperature(event):
    item = getItem(event['payload']['appliance']['applianceId'])
    if not (item and item['type'] == "Group"):
        return generate_error(event, "No target temperature data found")
    items = generate_thermostat(item['members'])
    try:
        number = float(items['targetTemperature']['state'])
    except:
        return generate_error(event, "Temperature data invalid")

    ret = {
        'header': generate_response(event, "Response"),
        'payload': {
            "targetTemperature": {
                "value": convert_to_c(number) if is_fahrenheit(event) else number
            },
            "applianceResponseTimestamp": datetime.datetime.now().isoformat(),
            "temperatureMode": {
                "value": thermo_to_string(items['heatingCoolingMode']['state']) if 'heatingCoolingMode' in items else "CUSTOM"
            }
        }
    }
    if ret['payload']['temperatureMode']['value'] == "CUSTOM":
        ret['payload']['temperatureMode']['friendlyName'] = ""
    return ret


def colour_request(event):
    h = str(event['payload']['color']['hue'])
    s = str(round(event['payload']['color']['saturation'] * 100))
    b = str(round(event['payload']['color']['brightness'] * 100))
    command = h + ',' + s + ',' + b
    return {
        'header': generate_response(event, "Confirmation"),
        'payload': {
            "achievedState": {
                "color": event['payload']['color']
            }
        }
    } if postCommand(event['payload']['appliance']['applianceId'], command) else generate_error(event)


def temperature_request(event):
    item = getItem(event['payload']['appliance']['applianceId'])
    if not (item and item['type'] == "Group"):
        return generate_error(event, "No thermostat found")
    items = generate_thermostat(item['members'])
    if 'targetTemperature' not in items:
        return generate_error(event, "No target temperature")
    try:
        value = int(items['targetTemperature']['state'])
    except:
        return generate_error(event, "Temperature data invalid")
    fahren = is_fahrenheit(event)
    values = {
        "SetTargetTemperatureRequest": convert_to_f(event['payload']['targetTemperature']['value']) if fahren else event['payload']['targetTemperature']['value'],
        "IncrementTargetTemperatureRequest": value + event['payload']['deltaTemperature']['value'],
        "DecrementTargetTemperatureRequest": value - event['payload']['deltaTemperature']['value']
    }
    setval = values[event['header']['name']]
    mode = thermo_to_string(items['heatingCoolingMode']['state']) if 'heatingCoolingMode' in items else "AUTO"
    return {
        'header': generate_response(event, "Confirmation"),
        'payload': {
            "targetTemperature": {
                "value": convert_to_c(setval) if fahren else setval
            },
            "temperatureMode": {
                "value": mode
            },
            "previousState": {
                "targetTemperature": {
                    "value": convert_to_c(value) if fahren else value
                },
                "mode": {
                    "value": mode
                }
            }
        }
    } if postCommand(items['targetTemperature'], str(setval)) else generate_error(event)


def switch_request(event):
    return {
        'header': generate_response(event, "Confirmation"),
        'payload': {}
    } if postCommand(
        event['payload']['appliance']['applianceId'], "ON" if 'On' in event['header']['name'] else "OFF") else generate_error(event)
