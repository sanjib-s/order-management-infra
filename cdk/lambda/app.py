import json
import os
import base64
import boto3
import urllib3

ssm = boto3.client("ssm")
dynamodb = boto3.resource("dynamodb")

http = urllib3.PoolManager(
    retries=urllib3.Retry(
        total=2,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
)

TABLE_PARAM = os.environ["TABLE_NAME_PARAM"]
EKS_ORDERS_URL = os.environ.get("EKS_ORDERS_URL")


def _get_table():
    table_name = ssm.get_parameter(Name=TABLE_PARAM)["Parameter"]["Value"]
    return dynamodb.Table(table_name)


def _method(event):
    return (event.get("requestContext", {}).get("http", {}) or {}).get("method", "")


def _claims(event):
    auth = (event.get("requestContext", {}).get("authorizer", {}) or {}).get("jwt", {}) or {}
    return auth.get("claims", {}) or {}


def _parse_body(event):
    body = event.get("body")
    if not body:
        return {}
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    try:
        return json.loads(body)
    except Exception:
        return {"_raw": body}

print("HANDLER START")
print("TABLE_PARAM:", TABLE_PARAM)
print("EKS_ORDERS_URL:", EKS_ORDERS_URL)

def handler(event, context):
    try:
        method = _method(event)
        path_params = event.get("pathParameters") or {}

        claims = _claims(event)
        user_sub = claims.get("sub", "unknown")
        user_email = claims.get("email", "unknown")

        table = _get_table()

        if method == "GET":
            order_id = path_params.get("orderId")
            if not order_id:
                return _resp(400, {"message": "orderId is required"})

            item = table.get_item(Key={"orderId": order_id}).get("Item")
            if not item:
                return _resp(404, {"message": "Order not found"})
            return _resp(200, item)

        if method == "POST":
            if not EKS_ORDERS_URL:
                return _resp(500, {"message": "EKS_ORDERS_URL not configured"})

            payload = _parse_body(event)

            r = http.request(
                "POST",
                EKS_ORDERS_URL,
                body=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                timeout=urllib3.Timeout(connect=3.0, read=20.0),
            )

           
            if r.status >= 400:
                return _resp(r.status, {
                    "message": "EKS call failed",
                    "url": EKS_ORDERS_URL,
                    "status": r.status,
                    "details": (r.data.decode("utf-8") if r.data else "")
                })

            order = json.loads(r.data.decode("utf-8")) if r.data else {}

            order["createdBy"] = {"sub": user_sub, "email": user_email}

            if "orderId" not in order:
                return _resp(500, {"message": "Invalid EKS response: missing orderId", "eksResponse": order})

            table.put_item(Item=order)
            return _resp(201, order)

        return _resp(405, {"message": f"Unsupported method: {method}"})

    except Exception as e:
        return _resp(500, {"message": "Unhandled exception", "error": str(e)})


def _resp(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}