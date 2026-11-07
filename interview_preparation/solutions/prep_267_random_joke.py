"""Only the validated joke goes to stdout; diagnostics use stderr and exit code."""
import json
import sys
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ENDPOINT = "https://api.chucknorris.io/jokes/random"
MAX_BYTES = 1_048_576


class JokeError(Exception):
    pass


def fetch_joke(opener=urlopen, timeout=5):
    request = Request(ENDPOINT, headers={"Accept": "application/json"})
    try:
        with opener(request, timeout=timeout) as response:
            if not 200 <= response.status < 300:
                raise JokeError("HTTP status is not successful")
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise JokeError("response body exceeds the chosen limit")
    except (HTTPError, URLError, TimeoutError, OSError, HTTPException) as exc:
        raise JokeError("request failed or timed out") from exc
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeError) as exc:
        raise JokeError("response is not valid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("value"), str):
        raise JokeError("expected a JSON object with a string value field")
    return payload["value"]


def main(fetch=fetch_joke):
    try:
        joke = fetch()
    except JokeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(joke)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
