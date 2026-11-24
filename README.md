# Realo API Python Library

The official Python library for using [the Realo REST API](https://api.realo.com/docs).

Before using this library, you must have a valid API Key. To get an API Key, please contact your Realo customer success manager.

Also available for [PHP](https://github.com/realo-com/realo-api-client-php) and [C#](https://github.com/realo-com/realo-api-client-csharp).

Requires Python 3.9+. No runtime dependencies (uses `urllib` from the standard library).

## Installation

The package is not on PyPI yet; install it straight from GitHub:

```bash
pip install git+https://github.com/realo-com/realo-api-client-python.git
```

## Initialization
#### RealoApi.create(public_key, private_key, environment)
* `public_key` (`str`): API public key
* `private_key` (`str`): API private key
* `environment` (`str`, default `production`): either `production` or `sandbox`. Anything else raises `ValueError`.

#### RealoApi.create_with_transport(public_key, private_key, transport, environment)
Same as `create`, but requests are sent through your own `transport`, a callable
`(method, url, headers, body) -> TransportResponse(status, headers, body)`. Use it to proxy requests or to test without network.

## Methods
### request(path, method="GET", payload=None, headers=None)
* `path` (`str`): the path of the resource
* `method` (`str`): HTTP method
* `payload` (JSON-serializable, optional): request body, encoded as JSON
* `headers` (`dict`, optional): custom headers

Returns the parsed JSON when the response `Content-Type` starts with `application/json`, otherwise the raw body as `bytes`.

## Examples

### Use The Bundled CLI Tool
```bash
$ realo-api --public-key=xxx --private-key=xxx /valuations/xxx/data/mobility
{
    "data": {
        "mobilityScore": 0.88,
        "distanceToCityCenter": 3130
    }
}
```

Options: `-m/--http-method`, `-b/--http-body` (JSON), `-f/--force` (print non-JSON responses), `-e/--environment`. Exit code is 1 on errors.

### Send An API Call Using The Request Function
```python
from realo_api import RealoApi, RealoApiException

api = RealoApi.create("YOUR_PUBLIC_KEY", "YOUR_PRIVATE_KEY")
try:
    response = api.request("/agencies", "GET")
    print(response)
except RealoApiException as e:
    print("Error %d: %s" % (e.code, e))
```

## Exceptions
`RealoApiException` is raised when there is a problem with the request or the server returns a status code of `400` or higher.

* `code`: the HTTP status code (`0` when no response was received)
* `str(e)`: the message, `"<type>: <message>"` of the first error when available
* `errors`: the list of errors from a JSON response body, otherwise `None`
* `type`: the type of the first error, otherwise `None`

## License
MIT
