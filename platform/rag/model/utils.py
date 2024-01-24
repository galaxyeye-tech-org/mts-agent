import copy
import time


class DataUtils:

    StrategyPublicUid = r'0'

    @classmethod
    def format_mongo_record(cls, record: dict) -> dict:

        if not record:
            return record

        result = copy.copy(record)

        result[r'id'] = result.pop(r'_id')

        return result

    @classmethod
    def format_mongo_records(cls, records: list[dict]) -> list[dict]:

        if not records:
            return records

        results = copy.deepcopy(records)

        for result in results:
            result[r'id'] = result.pop(r'_id')

        return results


class AttentionUtils:

    @classmethod
    def get_decayed_of_attention(
            cls, original_attention: int, create_timestamp: int,
            cost_hour_decay_one_attention: int = 5,
            current_timestamp: int = None
    ):
        if current_timestamp is None:
            current_timestamp = time.time()

        decay_attention = (current_timestamp - create_timestamp) // (3600 * cost_hour_decay_one_attention)

        decayed_attention = original_attention - decay_attention if decay_attention <= original_attention else 0

        return decayed_attention


