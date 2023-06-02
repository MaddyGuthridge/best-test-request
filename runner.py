"""
Script to test various combinations of things
"""
import sys
from subtask import Subtask
import requests
from requests.exceptions import ConnectionError
from time import perf_counter
from typing import Callable, TypedDict
from colorama import Fore
import itertools


# The number of tests to be run
NUM_TESTS = 100
# The number of requests to be sent per test
NUM_REQUESTS = 10


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


def jest_fetch_get():
    return jest_tester({"GET_REQUEST": "TRUE"})


def jest_sync_request_get():
    return jest_tester({
        "SYNC_REQUEST": "TRUE",
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
            # flask_jsonify,
            flask_json_lib,
            express,
        ],
        [
            # pytest_real_request_get,
            pytest_real_request_post,
            # jest_fetch_get,
            # jest_sync_request_get,
            jest_fetch_post,
            jest_sync_request_post,
        ]
    )
]
variants.append({
    "server": flask_jsonify,
    "tester": pytest_flask_testing,
})
# variants.append({
#     "server": flask_json_lib,
#     "tester": pytest_flask_testing,
# })


def print_output(
    server: Callable[[], Subtask],
    tester: Callable[[], Subtask],
    duration: float,
    ending="\n",
    output=sys.stdout,
    color="",
) -> None:
    print(
        f"{color}"
        f"| {name_variant(server).ljust(25)} "
        f"| {name_variant(tester).ljust(25)} "
        f"| {duration:9.3f} "
        f"|"
        f"{Fore.RESET if color != '' else ''}",
        end=ending,
        file=output,
    )


def main():
    print("# Benchmark results")
    print("")
    print(
        f"| {'Server'.ljust(25)} "
        f"| {'Tester'.ljust(25)} "
        f"| {'Duration'.ljust(9)} "
        f"|"
    )
    print(f"{'=' * (69)}")  # Nice

    for variant in variants:
        server = variant["server"]
        server_proc = server()
        tester = variant["tester"]
        start_time = perf_counter()
        tester_proc = tester()
        if "--progress" in sys.argv:
            while tester_proc.wait(0.1) is None:
                duration = perf_counter() - start_time
                print_output(
                    server, tester, duration, "\r", sys.stderr, Fore.YELLOW)
            assert tester_proc.wait() == 0
        else:
            assert tester_proc.wait() == 0
        duration = perf_counter() - start_time
        server_proc.interrupt()
        server_proc.wait()
        print_output(server, tester, duration)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted")
