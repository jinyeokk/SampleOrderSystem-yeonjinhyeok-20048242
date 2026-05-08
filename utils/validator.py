def validate_non_empty(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name}은(는) 필수 입력입니다.")
    return value.strip()


def validate_max_length(value: str, max_len: int, field_name: str) -> str:
    if len(value) > max_len:
        raise ValueError(f"{field_name}은(는) 최대 {max_len}자까지 입력 가능합니다.")
    return value


def validate_positive_float(value: str, field_name: str) -> float:
    try:
        f = float(value)
    except ValueError:
        raise ValueError(f"{field_name}은(는) 숫자여야 합니다.")
    if f <= 0:
        raise ValueError(f"{field_name}은(는) 0보다 커야 합니다.")
    return f


def validate_positive_int(value: str, field_name: str) -> int:
    try:
        i = int(value)
    except ValueError:
        raise ValueError(f"{field_name}은(는) 정수여야 합니다.")
    if i < 1:
        raise ValueError(f"{field_name}은(는) 1 이상이어야 합니다.")
    return i


def validate_yield_rate(value: str) -> float:
    try:
        f = float(value)
    except ValueError:
        raise ValueError("수율은 숫자여야 합니다.")
    if not (0.01 <= f <= 1.00):
        raise ValueError("수율은 0.01 ~ 1.00 사이 값이어야 합니다.")
    return f
