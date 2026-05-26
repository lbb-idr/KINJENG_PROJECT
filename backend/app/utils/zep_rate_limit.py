import time

_last_zep_call = 0.0
_ZEP_MIN_INTERVAL = 18


def rate_limit():
    global _last_zep_call
    elapsed = time.time() - _last_zep_call
    if elapsed < _ZEP_MIN_INTERVAL:
        sleep_time = _ZEP_MIN_INTERVAL - elapsed
        time.sleep(sleep_time)
    _last_zep_call = time.time()
