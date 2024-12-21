import json
import subprocess

patch_data = {
    "op": "replace",
    "path": "/accessLogSettings/format",
    "value": json.dumps({  # Convert value to string here
        "requestId": "$context.requestId",
        "ip": "$context.identity.sourceIp",
        "requestTime": "$context.requestTime",
        "httpMethod": "$context.httpMethod",
        "resourcePath": "$context.resourcePath",
        "status": "$context.status",
        "protocol": "$context.protocol",
        "responseLength": "$context.responseLength"
    })
}

json_patch_string = json.dumps([patch_data])

try:
    result = subprocess.run(
        [
            "aws",
            "apigateway",
            "update-stage",
            "--rest-api-id",
            "qow3wyg1nj",
            "--stage-name",
            "prod",
            "--patch-operations",
            json_patch_string,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    print("API Gateway stage updated successfully!")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"Error updating API Gateway stage: {e.stderr}")
    print(f"Return code: {e.returncode}")
except json.JSONEncoderError as e:
    print(f"Error encoding JSON: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
