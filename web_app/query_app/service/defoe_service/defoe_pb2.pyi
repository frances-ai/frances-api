from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class JobRequest(_message.Message):
    __slots__ = ["job_id"]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...

class JobResponse(_message.Message):
    __slots__ = ["error", "job_id", "result_file_path", "state"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    error: str
    job_id: str
    result_file_path: str
    state: str
    def __init__(self, job_id: _Optional[str] = ..., state: _Optional[str] = ..., result_file_path: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class JobSubmitRequest(_message.Message):
    __slots__ = ["endpoint", "job_id", "model_name", "query_config", "query_name", "result_file_path"]
    class QueryConfigEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    QUERY_CONFIG_FIELD_NUMBER: _ClassVar[int]
    QUERY_NAME_FIELD_NUMBER: _ClassVar[int]
    RESULT_FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    endpoint: str
    job_id: str
    model_name: str
    query_config: _containers.ScalarMap[str, str]
    query_name: str
    result_file_path: str
    def __init__(self, job_id: _Optional[str] = ..., model_name: _Optional[str] = ..., query_name: _Optional[str] = ..., endpoint: _Optional[str] = ..., query_config: _Optional[_Mapping[str, str]] = ..., result_file_path: _Optional[str] = ...) -> None: ...

class JobSubmitResponse(_message.Message):
    __slots__ = ["job_id"]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...
