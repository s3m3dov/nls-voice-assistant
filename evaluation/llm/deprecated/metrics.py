import re
from collections import defaultdict
from datetime import datetime, timedelta

WEEKDAY_MAP = {
    "mon": "monday",
    "monday": "monday",
    "tue": "tuesday",
    "tues": "tuesday",
    "tuesday": "tuesday",
    "wed": "wednesday",
    "weds": "wednesday",
    "wednesday": "wednesday",
    "thu": "thursday",
    "thur": "thursday",
    "thurs": "thursday",
    "thursday": "thursday",
    "fri": "friday",
    "friday": "friday",
    "sat": "saturday",
    "saturday": "saturday",
    "sun": "sunday",
    "sunday": "sunday",
}

RELATIVE_DAY_MAP = {
    "today": "today",
    "tomorrow": "tomorrow",
}


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_place(value: object) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_weekday(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""

    if text in RELATIVE_DAY_MAP:
        offset = 0 if text == "today" else 1
        return (datetime.today() + timedelta(days=offset)).strftime("%A").lower()

    text = text.replace("next ", "").replace("this ", "")
    text = text.strip()
    if text in WEEKDAY_MAP:
        return WEEKDAY_MAP[text]

    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        try:
            parsed = datetime.fromisoformat(text)
            return parsed.strftime("%A").lower()
        except ValueError:
            return text

    return text


def normalize_datetime(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""

    text = text.replace(" at ", " ")
    text = text.replace("/", "-")
    text = text.strip()

    iso_candidate = text.replace(" ", "T")
    try:
        parsed = datetime.fromisoformat(iso_candidate)
        return parsed.strftime("%Y-%m-%dT%H:%M")
    except ValueError:
        pass

    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        return text

    return normalize_weekday(text)


def normalize_value(key: str, value: object) -> str:
    key = key.lower()
    if key in {"place", "location", "title", "description", "reference"}:
        return normalize_text(value)
    if key in {"day", "date"}:
        return normalize_weekday(value)
    if key in {"start_time", "end_time"}:
        return normalize_datetime(value)
    if key in {"id"}:
        return normalize_text(value)
    return normalize_text(value)


def normalize_intent(value: object) -> str:
    return normalize_text(value).upper()


def normalize_api_call(call: dict | None) -> dict:
    if not isinstance(call, dict):
        call = {}
    method = normalize_text(call.get("method")).upper() if call.get("method") else ""
    endpoint = normalize_text(call.get("endpoint"))
    params = call.get("params") if isinstance(call.get("params"), dict) else {}
    body = call.get("body") if isinstance(call.get("body"), dict) else {}
    return {
        "method": method,
        "endpoint": endpoint,
        "params": params,
        "body": body,
    }


def normalize_output(output: object) -> dict:
    if not isinstance(output, dict):
        output = {}
    intent = output.get("intent", "")
    slots = output.get("slots") if isinstance(output.get("slots"), dict) else {}
    api_call = normalize_api_call(output.get("api_call"))
    assistant_reply = output.get("assistant_reply", "")
    return {
        "intent": intent,
        "slots": slots,
        "api_call": api_call,
        "assistant_reply": assistant_reply,
    }


def compare_slots(expected: dict, predicted: dict, optional_slots: set | None = None) -> tuple[dict, dict]:
    expected = expected or {}
    predicted = predicted or {}
    optional_slots = optional_slots or set()

    slot_results = {}
    slot_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for key, expected_value in expected.items():
        expected_norm = normalize_value(key, expected_value)
        pred_value = predicted.get(key)
        if key in optional_slots and (pred_value is None or pred_value == ""):
            slot_results[key] = True
            continue
        pred_norm = normalize_value(key, pred_value)
        match = bool(pred_value is not None and expected_norm == pred_norm)
        slot_results[key] = match
        if match:
            slot_stats[key]["tp"] += 1
        else:
            slot_stats[key]["fn"] += 1

    for key in predicted.keys():
        if key not in expected:
            slot_stats[key]["fp"] += 1

    return slot_results, slot_stats


def merge_slot_stats(stats_list: list[dict]) -> dict:
    merged = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for stats in stats_list:
        for key, values in stats.items():
            merged[key]["tp"] += values.get("tp", 0)
            merged[key]["fp"] += values.get("fp", 0)
            merged[key]["fn"] += values.get("fn", 0)
    return merged


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def field_accuracy(expected: dict, predicted: dict) -> tuple[int, int]:
    if not expected:
        return 1, 1
    correct = 0
    total = 0
    for key, expected_value in expected.items():
        total += 1
        pred_value = predicted.get(key)
        if normalize_value(key, expected_value) == normalize_value(key, pred_value):
            correct += 1
    return correct, total


def build_confusion_matrix(confusion: dict) -> list[list[str]]:
    labels = sorted(confusion.keys())
    for expected in list(confusion.keys()):
        for predicted in confusion[expected].keys():
            if predicted not in labels:
                labels.append(predicted)
    labels = sorted(set(labels))

    rows = []
    header = ["expected\\predicted"] + labels
    rows.append(header)
    for expected in labels:
        row = [expected]
        for predicted in labels:
            row.append(str(confusion.get(expected, {}).get(predicted, 0)))
        rows.append(row)
    return rows
