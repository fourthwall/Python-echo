from smarthome import handle_control, handle_discovery
from tools import generate_response


# This is the primary entrypoint for the function when invoked by AWS.
# Handles different queries from the Amazon Echo.
# The primary payload is received here - serialized JSON data that will describe
# an action for a relevant device, or will be a system command such as a request to enumerate devices
# or check the health of the system and that it is responding.

def lambda_handler(event, _):
    # The namespace is the primary driver of events. It describes the type of command received.
    namespace = event['header']['namespace']
    # Discover event. Dispatch handler to enumerate devices
    if namespace == 'Alexa.ConnectedHome.Discovery':
        return handle_discovery(event)

    # Control event - dispatch handler to perform requested action.
    elif namespace in ('Alexa.ConnectedHome.Control', 'Alexa.ConnectedHome.Query'):
        return handle_control(event)

    # System health check - not a user command
    elif namespace == 'Alexa.ConnectedHome.System' and event['header']['name'] == "HealthCheckRequest":
        return {
            "header": generate_response(event, "Response"), "payload": {
                "description": "The system is currently healthy",
                "isHealthy": True}
        }

    # Return error for unknown request, along with offending payload
    return {
        'header': {
            "namespace": "Alexa.ConnectedHome.Control",
            "name": "UnexpectedInformationReceivedError",
            "payloadVersion": event['header']['payloadVersion'],
            "messageId": event['header']['messageId']
        },
        'payload': {"faultingParameter": event['header']['namespace']}
    }
