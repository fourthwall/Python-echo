from smarthome import *
from tools import generate_response


def lambda_handler(event, _):
    namespace = event['header']['namespace']
    if namespace == 'Alexa.ConnectedHome.Discovery':
        return handleDiscovery(event)

    elif namespace in ('Alexa.ConnectedHome.Control', 'Alexa.ConnectedHome.Query'):
        return handle_control(event)

    elif namespace == 'Alexa.ConnectedHome.System' and event[
            'header']['name'] == "HealthCheckRequest":  # system health check
        return {"header": generate_response(event, "Response"), "payload": {
            "description": "The system is currently healthy",
            "isHealthy": True}}

    return {'header': {
        "namespace": "Alexa.ConnectedHome.Control",
        "name": "UnexpectedInformationReceivedError",
        "payloadVersion": event['header']['payloadVersion'],
        "messageId": event['header']['messageId']
    },
        'payload': {"faultingParameter": event['header']['namespace']}}
