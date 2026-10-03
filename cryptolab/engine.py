"""Compare immediate consolidation cost against future input savings and privacy-cluster restrictions."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    current = integer(d["current_fee_rate"])
    future = integer(d["future_fee_rate"])
    inputbytes = integer(d["input_bytes"], 1)
    outputbytes = integer(d["output_bytes"], 1)
    overhead = integer(d["overhead_bytes"])
    groups = {}
    for c in records(d["coins"], "id"):
        cluster = identity(c["cluster"])
        integer(c["value"], 1)
        groups.setdefault(cluster, []).append(c)
    plans = []
    for cluster, coins in sorted(groups.items()):
        size = overhead + len(coins) * inputbytes + outputbytes
        fee = size * current
        value = sum(c["value"] for c in coins)
        saved_inputs = max(len(coins) - 1, 0)
        saving = saved_inputs * inputbytes * future
        plans.append(
            {
                "cluster": cluster,
                "inputs": sorted(c["id"] for c in coins),
                "fee": fee,
                "output_value": max(value - fee, 0),
                "future_fee_saving": saving,
                "net_saving": saving - fee,
                "worthwhile": len(coins) > 1 and saving > fee and value > fee,
            }
        )
    return {
        "plans": plans,
        "total_immediate_fee": sum(p["fee"] for p in plans),
        "total_net_saving": sum(p["net_saving"] for p in plans),
    }


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
