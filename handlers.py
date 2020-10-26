import datetime
from api import *
from tools import *


# Function for getting a current actual temperature from a thermostat item or thermostat group.
# As thermostat groups are item groups, we are attempting to locate and parse the
# Actual temperature reading.
def current_temperature(event):
    item = getItem(event['payload']['appliance']['applianceId'])
    if not item:
        return generate_error(event, "No current temperature data found")
    # if a group is detected, build a thermostat item out of them
    if item['type'] == "Group":
        items = generate_thermostat(item['members'])
        item = items['currentTemperature']
    try:
        number = float(item['state'])
    except ValueError:
        return generate_error(event, "Temperature data invalid")  # String cannot be parsed
    return {
        'header': generate_response(event, "Response"),
        'payload': {
            "temperatureReading": {
                "value": convert_to_c(number) if is_fahrenheit(event) else number
            },
            "applianceResponseTimestamp": datetime.datetime.now().isoformat()
        }
    }


# Handles items that require a percentage to be set - such as blinds, stereos, etc
def percentage_request(event):
    # This handles exact percentage requests - that do not require
    # the existing percentages to be read.
    name = event['payload']['appliance']['applianceId']
    if event['header']['name'] == 'SetPercentageRequest':
        return {'header': generate_response(event, "Confirmation"), 'payload': {}} if postCommand(
            name, str(event['payload']['percentageState']['value'])) else generate_error(event)

    # A "PercentageRequest" requires the existing percentage to be read
    # And then modified in some way.
    elif 'PercentageRequest' in event['header']['name']:
        # gets the percentage value item such that we may read its current state
        item = getItem(name)
        # parse the delta percentage requested into a float
        value = float(event['payload']['deltaPercentage']['value'])
        if not item:
            # Item not found - device has probably been removed
            return generate_error(event)
        try:
            number = float(item['state'])
        except ValueError:
            return generate_error(event, "No existing percentage")
        # Set values for increment and decrement
        values = {
            'IncrementPercentageRequest': number + value,
            'DecrementPercentageRequest': number - value
        }
        # Set which we are actually doing
        value = values[event['header']['name']]
        value = 100 if value > 100 else 0 if value < 0 else value  # Prevents wrap-around
        return {
            'header': generate_response(event, "Confirmation"),
            'payload': {}
        } if postCommand(name, str(
            value)) else generate_error(event)


# Gets target temperature for a thermostat.
# This locates and parses the value of OpenHAB's "setpoint" item in the thermostat group..
def target_temperature(event):
    item = getItem(event['payload']['appliance']['applianceId'])
    # Item must both exist and be a "Group", as a setpoint can't exist on its own.
    if not (item and item['type'] == "Group"):
        return generate_error(event, "No target temperature data found")
    # A thermostat in OpenHAB consists of several items - temp monitor, setpoint etc
    items = generate_thermostat(item['members'])
    try:
        # Get current target temperature
        number = float(items['targetTemperature']['state'])
    except ValueError:
        return generate_error(event, "Temperature data invalid")
    # Generate response payload containing new target Temperature
    # We don't invoke the standard response function here as more detail is required.
    ret = {
        'header': generate_response(event, "Response"),
        'payload': {
            "targetTemperature": {
                "value": convert_to_c(number) if is_fahrenheit(event) else number  # OpenHAB always expects Celsius
            },
            "applianceResponseTimestamp": datetime.datetime.now().isoformat(),
            "temperatureMode": {
                # Read heating and cooling mode - if not set, just reply "CUSTOM"
                "value": thermo_to_string(
                    items['heatingCoolingMode']['state']) if 'heatingCoolingMode' in items else "CUSTOM"
            }
        }
    }
    # No friendly name for undefined temperature state
    if ret['payload']['temperatureMode']['value'] == "CUSTOM":
        ret['payload']['temperatureMode']['friendlyName'] = ""
    return ret


def colour_request(event):
    # RGB lighting is set using HSB values.
    # Parse values to string after rounding.
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
    } if postCommand(event['payload']['appliance']['applianceId'], command) \
        else generate_error(event)


# Sets a temperature for a thermostat
# Can either be an absolute temperature, or a delta temperature
# of the existing setpoint
def temperature_request(event):
    # Get thermostat group
    item = getItem(event['payload']['appliance']['applianceId'])

    # A setpoint cannot exist independently, so the item must be a group
    if not (item and item['type'] == "Group"):
        return generate_error(event, "No thermostat found")

    # Create composite thermostat device
    items = generate_thermostat(item['members'])

    # A delta cannot be requested if there is no existing temperature.
    if 'targetTemperature' not in items:
        return generate_error(event, "No target temperature")

    # Parse current temperature to integer
    try:
        value = int(items['targetTemperature']['state'])
    except ValueError:
        return generate_error(event, "Temperature data invalid")
    fahren = is_fahrenheit(event)

    # Determines correct values for 3 scenarios - absolute temperature, delta reduction, delta increase
    values = {
        "SetTargetTemperatureRequest": convert_to_f(event['payload']['targetTemperature']['value']) if fahren else
        event['payload']['targetTemperature']['value'],
        "IncrementTargetTemperatureRequest": value + event['payload']['deltaTemperature']['value'],
        "DecrementTargetTemperatureRequest": value - event['payload']['deltaTemperature']['value']
    }
    setval = values[event['header']['name']]

    # Set a heat/cool mode if there's an item for it, else just set AUTO
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


# Handles basic switch events - on/off etc
def switch_request(event):
    return {
        'header': generate_response(event, "Confirmation"),
        'payload': {}
    } if postCommand(
        event['payload']['appliance']['applianceId'],
        "ON" if 'On' in event['header']['name'] else "OFF") else generate_error(event)
