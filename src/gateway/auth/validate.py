import os

import requests


def token(request):
    if not "Authorization" in request.headers:
        return None, ("missing credentials", 401)

    jwt_token = request.headers["Authorization"]

    if not jwt_token:
        return None, ("missing credentials", 401)

    # send an HTTP POST request to our service
    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/validate",
        headers={"Authorization": jwt_token}
    )

    if response.status_code == 200:
        # return body of JWT with claims (in JSON)
        return response.text, None

    return None, (response.text, response.status_code)
