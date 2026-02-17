import json
import os
import boto3

ssm = boto3.client("ssm")
PARAMETER_NAME = os.environ["SSM_PARAMETER_NAME"]


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "/")

    if method == "GET" and path == "/":
        return handle_get()
    elif method == "PUT" and path == "/string":
        return handle_put(event)
    else:
        return response(404, "text/plain", "Not Found")


def handle_get():
    result = ssm.get_parameter(Name=PARAMETER_NAME)
    value = result["Parameter"]["Value"]
    html = f"<h1>The saved string is {value}</h1>"
    return response(200, "text/html", html)


def handle_put(event):
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode("utf-8")

    payload = json.loads(body)
    new_value = payload.get("value", "")

    if not new_value:
        return response(400, "application/json", json.dumps({"error": "missing 'value' field"}))

    ssm.put_parameter(Name=PARAMETER_NAME, Value=new_value, Overwrite=True)
    return response(200, "application/json", json.dumps({"message": "updated", "value": new_value}))


def response(status_code, content_type, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": content_type},
        "body": body,
    }
