import json

from redis import Redis

from factorization import factorize, Factorization


def cached_factorize(n: int, cache_key: str, cache_url: str) -> Factorization:
    cache = Redis.from_url(cache_url)
    cache_result = cache.get(cache_key)
    if cache_result is not None:
        return json.loads(cache_result)
    else:
        result = factorize(n)
        cache.set(cache_key, json.dumps(result))
        return result
