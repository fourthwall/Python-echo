def thermo_to_string(mode):
    mode = str(mode)
    modes = {
        "0": "OFF",
        "1": "HEAT",
        "2": "COOL",
        "3": "AUTO",
        "heat-cool": "AUTO"
    }
    return modes[mode] if mode in modes else mode.upper()


def is_fahrenheit(event):
    return 'temperatureFormat' in event['payload']['appliance']['additionalApplianceDetails'] and \
           event['payload']['appliance']['additionalApplianceDetails']['temperatureFormat'] == 'fahrenheit'


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


def generate_thermostat(group):
    thermo = {}
    for item in group:
        for tag in item['tags']:
            tags = {
                "CurrentTemperature": "currentTemperature",
                "TargetTemperature": "targetTemperature",
                "homekit:HeatingCoolingMode": "heatingCoolingMode"
            }
            if tag in tags:
                thermo[tags[tag]] = item
    return thermo


def generate_response(event, name):  # replace with either Response or Confirmation only!
    header = event['header']
    ret = {
        "name": header['name'].replace("Request", name),
        "namespace": header['namespace'],
        "payloadVersion": "2"
    }
    if "messageId" in header:
        ret['messageId'] = header['messageId']
    return ret


def convert_to_c(number):
    return (number - 32) * 5.0 / 9.0


def convert_to_f(number):
    return 9.0/5.0 * number + 32


