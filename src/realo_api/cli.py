"""``realo-api`` command line tool."""

import argparse
import json
import sys
from typing import Any, List, Optional

from .client import ENVIRONMENTS, PRODUCTION_ENVIRONMENT, RealoApi
from .exceptions import RealoApiException


def _dump(data: Any) -> str:
    return json.dumps(data, indent=4, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="realo-api", description="Call the Realo REST API.")
    parser.add_argument("--public-key", required=True)
    parser.add_argument("--private-key", required=True)
    parser.add_argument("-m", "--http-method", default="GET")
    parser.add_argument("-b", "--http-body", help="JSON request body")
    parser.add_argument("-f", "--force", action="store_true", help="print non-JSON responses")
    parser.add_argument(
        "-e",
        "--environment",
        default=PRODUCTION_ENVIRONMENT,
        help="one of: " + ", ".join(ENVIRONMENTS),
    )
    parser.add_argument("path", metavar="PATH")
    return parser


def main(argv: Optional[List[str]] = None, api: Optional[RealoApi] = None) -> int:
    """Run the CLI and return the exit code. ``api`` lets tests inject a client."""
    args = build_parser().parse_args(argv)

    body: Any = None
    if args.http_body is not None:
        try:
            body = json.loads(args.http_body)
        except ValueError as e:
            print("Invalid JSON body given: %s" % e, file=sys.stderr)
            return 1

    if api is None:
        try:
            api = RealoApi.create(args.public_key, args.private_key, args.environment)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 1

    try:
        response = api.request(args.path, args.http_method, body)
    except RealoApiException as e:
        if e.errors is not None:
            print(_dump({"errors": e.errors}))
        else:
            print("Error %d: %s" % (e.code, e), file=sys.stderr)
        return 1

    if isinstance(response, bytes):
        if args.force:
            sys.stdout.flush()
            sys.stdout.buffer.write(response)
            sys.stdout.buffer.flush()
        else:
            print(
                "Warning: the response is probably binary data, if you do want to continue "
                "re-run this command with -f.",
                file=sys.stderr,
            )
        return 0
    print(_dump(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
