import json
import re
from typing import Optional
from . import config


def generate_uri(base_uri: str, params: dict[str, str]) -> str:
    query_string = '&'.join(f"{key}={value}" for key, value in params.items())
    return f"{base_uri}?{query_string}" if query_string else base_uri


def format_ws_msg(id_: int, method: Optional[str] = None, params: Optional[dict | list] = None) -> str:
    if method is None and params is None:
        return str(id_)
    elif params is None:
        return f"{id_}[{method}]"
    return f"{id_}[{method},{params}]"


def choose_encoding(array: tuple[str, ...]) -> tuple[int, Optional[str], Optional[dict | bool]]:
    encoding_id = int(array[0])
    encoding_name = array[3] if array[3] is not None else None
    encoding_params = None

    if array[1] is not None:
        encoding_format = None if array[1] == 'null' else array[1]
        return encoding_id, encoding_format, {}

    if array[2] is not None:
        encoding_params = json.loads(array[2])
    elif array[8] is not None:
        encoding_params = json.loads(array[8])

    if encoding_params is None:
        if array[5] is not None:
            encoding_params = array[5] == "true"
        elif array[6] is not None:
            encoding_params = json.loads(array[6])
        elif array[7] is not None:
            encoding_params = json.loads(array[7])

    return encoding_id, encoding_name, encoding_params


def get_data_ws_msg(msg: str):
    m = re.match(config.msg_regex, msg)
    if m is None:
        raise ValueError(f"Line is not matched: {msg}")
    return choose_encoding(m.groups())


def generate_recv_id(id_: int) -> int:
    num_list = list(str(id_))
    if len(num_list) >= 3:
        num_list[1] = str(int(num_list[1]) + 1)
    return int("".join(num_list))
