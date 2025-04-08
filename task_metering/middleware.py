from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
import time

class APIMeteringMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            key = f"api_usage:{request.user.pk}"
            count = cache.get(key, 0)
            cache.set(key, count + 1, timeout=3600)  # Track per hour
            print(f"API call count for user {request.user.pk}: {count + 1}")
