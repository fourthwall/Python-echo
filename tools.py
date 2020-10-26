# Heating/Cooling modes are expressed as numbers in OpenHAB but the response is textual JSON.
# The "heat-cool" tag is there because if an OpenHAB user has configured their setup to work with HomeKit tags
# This will harmlessly ignore the heat/cooling mode by passing the generic "AUTO" tag.

def thermo_to_string(mode):
    mode = str(mode)
    modes = {
        "0": "OFF",
        "1": "HEAT",
        "2": "COOL",
        "3": "AUTO",
        "heat-cool": "AUTO"
    }
    # If the mode isn't expressed here, return what we received but capitalized.
    return modes[mode] if mode in modes else mode.upper()


# Reads tag and returns true if the Alexa is set to give and receive responses in Fahrenheit.
def is_fahrenheit(event):
    return 'temperatureFormat' in event['payload']['appliance']['additionalApplianceDetails'] and \
           event['payload']['appliance']['additionalApplianceDetails']['temperatureFormat'] == 'fahrenheit'


# Generates generic error for when more info isn't available
def generate_error(event, error="OpenHAB error"):
    return {'header': {
        "namespace": "Alexa.ConnectedHome.Control",
        "name": "DependentServiceUnavailableError",
        "payloadVersion": "2",
        "messageID": event['header']['messageId']
    },
        'payload': {
            "dependentServiceName": error
        }
    }


# Gathers a group of OpenHAB items (temp setpoint, current temp, mode)
# and creates a single device out of them for Alexa
# Arguments - group - item tag group from OpenHAB.
def generate_thermostat(group):
    # Thermostat object we are building
    thermo = {}
    # Thermostats are up to three items. Setpoint, Target temperature, and mode.
    # The "homekit" tag there is simply for compatibility with Apple's homekit technology.
    tags = {
        "CurrentTemperature": "currentTemperature",
        "TargetTemperature": "targetTemperature",
        "homekit:HeatingCoolingMode": "heatingCoolingMode"
    }
    for item in group:
        for tag in item['tags']:
            if tag in tags:
                thermo[tags[tag]] = item
    return thermo


# This method generates the boilerplate JSON for responses and is invoked
# to give a successful response.
# Arguments: event - incoming payload, along with the response - name
# Generates response to received payload.
def generate_response(event, name):
    header = event['header']
    ret = {
        "name": header['name'].replace("Request", name),
        "namespace": header['namespace'],
        "payloadVersion": "2"
    }
    # if the response contains a message, add it to the payload.
    if "messageId" in header:
        ret['messageId'] = header['messageId']
    return ret


# Does what it says on the tin.
def convert_to_c(number):
    return (number - 32) * 5.0 / 9.0


def convert_to_f(number):
    return 9.0 / 5.0 * number + 32
