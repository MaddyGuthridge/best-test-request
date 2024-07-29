"""
Script to test various combinations of things
"""
import sys
from datetime import datetime
from subtask import Subtask
import requests
from requests.exceptions import ConnectionError
from time import perf_counter
from typing import Callable, TypedDict, Union
from colorama import Fore
import itertools


# The number of tests to be run
NUM_TESTS = 100
# The number of requests to be sent per test
NUM_REQUESTS = 50
# Test timeout duration
TEST_TIMEOUT = 120


def server_is_up() -> bool:
    """
    Callback to determine whether the server is up and running
    """
    try:
        requests.get("http://127.0.0.1:5001/", {"input": 1})
        return True
    except ConnectionError:
        return False


def name_variant(func: Callable[[], Subtask]) -> str:
    return func.__name__.replace("_", " ").capitalize()


# Base generators


def flask_server(env: dict[str, str]):
    return Subtask(
        ["poetry", "run", "python", "-m", "flask_app"],
        env=env,
        wait_for=server_is_up,
    )


def express_server(env: dict[str, str]):
    return Subtask(
        ["npm", "start"],
        env=env,
        wait_for=server_is_up,
    )


def pytest_tester(env: dict[str, str]):
    env.update({
        "NUM_TESTS": str(NUM_TESTS),
        "NUM_REQUESTS": str(NUM_REQUESTS),
    })
    return Subtask(
        ["poetry", "run", "pytest"],
        env=env,
    )


def jest_tester(env: dict[str, str]):
    env.update({
        "NUM_TESTS": str(NUM_TESTS),
        "NUM_REQUESTS": str(NUM_REQUESTS),
    })
    return Subtask(
        ["npm", "run", "test"],
        env=env,
    )

# Server variants


def flask_jsonify():
    return flask_server({"FLASK_JSONIFY": "TRUE"})


def flask_json_lib():
    return flask_server({})


def express():
    return express_server({})


# Test variants


def pytest_flask_testing():
    return pytest_tester({})


def pytest_real_request_post():
    return pytest_tester({"REAL_REQUEST": "TRUE"})


def pytest_real_request_get():
    return pytest_tester({
        "REAL_REQUEST": "TRUE",
        "GET_REQUEST": "TRUE",
    })


def jest_fetch_post():
    return jest_tester({})


def jest_sync_request_post():
    return jest_tester({"SYNC_REQUEST": "TRUE"})


def jest_sync_request_curl_post():
    return jest_tester({"SYNC_REQUEST_CURL": "TRUE"})


def jest_light_my_request():
    return jest_tester({"LIGHT_MY_REQUEST": "TRUE"})


def jest_fetch_get():
    return jest_tester({"GET_REQUEST": "TRUE"})


def jest_sync_request_get():
    return jest_tester({
        "SYNC_REQUEST": "TRUE",
        "GET_REQUEST": "TRUE",
    })


def jest_sync_request_curl_get():
    return jest_tester({
        "SYNC_REQUEST_CURL": "TRUE",
        "GET_REQUEST": "TRUE",
    })


class Variation(TypedDict):
    server: Callable[[], Subtask]
    tester: Callable[[], Subtask]


variants: list[Variation] = []

# To adjust the benchmarks being run, comment out or uncomment these cases

variants += [  # type: ignore
    {"server": s, "tester": t}
    for s, t in itertools.product(
        [
            flask_jsonify,
            flask_json_lib,
            express,
        ],
        [
            pytest_real_request_get,
            pytest_real_request_post,
            jest_fetch_get,
            jest_sync_request_get,
            jest_fetch_post,
            jest_sync_request_post,
            jest_sync_request_curl_get,
            jest_sync_request_curl_post,
        ]
    )
]
variants.append({
    "server": flask_jsonify,
    "tester": pytest_flask_testing,
})
variants.append({
    "server": flask_json_lib,
    "tester": pytest_flask_testing,
})
variants.append({
    "server": express,
    "tester": jest_light_my_request,
})


def print_output(
    server: Callable[[], Subtask],
    tester: Callable[[], Subtask],
    duration: Union[float, str],
    ending="\n",
    output=sys.stdout,
    color="",
) -> None:
    if isinstance(duration, (float, int)):
        duration = f"{duration:9.3f}"
    print(
        f"{color}"
        f"| {name_variant(server).ljust(25)} "
        f"| {name_variant(tester).ljust(30)} "
        f"| {duration.ljust(9)} "
        f"|"
        f"{Fore.RESET if color != '' else ''}",
        end=ending,
        file=output,
    )


def main():
    print("# Best Test Request")
    print()
    print("A simple benchmark to determine the best request function when ")
    print("testing (or at least the fastest one).")
    print()
    print(
        f"This page was last updated at "
        f"{datetime.now().isoformat(timespec='minutes')}"
    )
    print()
    print(f"Each variant was benchmarked using a suite of {NUM_TESTS} tests,")
    print(f"with each test sending {NUM_REQUESTS} requests.")
    print()
    print(
        f"| {'Server'.ljust(25)} "
        f"| {'Tester'.ljust(30)} "
        f"| {'Duration'.ljust(9)} "
        f"|"
    )
    print(f"| {'-' * 25} | {'-' * 30} | {'-' * 8}: |")

    for variant in variants:
        server = variant["server"]
        server_proc = server()
        tester = variant["tester"]
        start_time = perf_counter()
        tester_proc = tester()

        timeout = False

        if "--progress" in sys.argv:
            while tester_proc.wait(0.1) is None:
                duration = perf_counter() - start_time
                # Check for timeout
                if duration > TEST_TIMEOUT:
                    tester_proc.interrupt()
                    timeout = True
                    break
                else:
                    print_output(
                        server,
                        tester,
                        duration,
                        "\r",
                        sys.stderr,
                        Fore.YELLOW,
                    )
        else:
            if tester_proc.wait(TEST_TIMEOUT) != 0:
                if tester_proc.poll() is None:
                    tester_proc.interrupt()
                    timeout = True
        duration = perf_counter() - start_time
        server_proc.interrupt()
        server_proc.wait(1)
        server_proc.kill()
        if timeout:
            print_output(
                server,
                tester,
                f"Timeout ({TEST_TIMEOUT} s)",
            )
        elif tester_proc.wait() != 0:
            print_output(
                server,
                tester,
                "Error",
            )
        else:
            print_output(server, tester, duration)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted")
        raise
