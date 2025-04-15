from django.urls import resolve
from django.utils import timezone
import re
import logging
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

class APIUsageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request first to let Django's authentication happen
        response = self.get_response(request)
        
        # Now check if the user is authenticated and if it's an API request
        user = request.user
        print(f"--------------------------")
        print(f"Request path: {request.path}")  
        print(f"Request user: {user}")
        print(f"User authenticated: {user.username}")
        
        if self._is_api_request(request) and user and user.is_authenticated:
            print(f"+++++++++++++++-")
            print(f"API call detected: {user.username}: {request.method} {request.path}")
            logger.info(f"[API CALL] User: {user.username} | Method: {request.method} | Path: {request.path}")
            
            # Send signal here
            from task_metering.signals import api_call_made
            api_call_made.send(
                sender=self.__class__,
                user=user,
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                timestamp=timezone.now()
            )
        
        return response 
    def _authenticate_user(self, request):
        """
        Try to authenticate the user from the Authorization header.
        Return the authenticated user or None.
        """
        # First, check if the user is already authenticated via session
        if request.user.is_authenticated:
            return request.user
        
        # Then try JWT authentication
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                # Create a DRF Request object since JWTAuthentication expects it
                drf_request = Request(request)
                auth = JWTAuthentication()
                validated_token = auth.get_validated_token(auth_header.split(' ')[1])
                user = auth.get_user(validated_token)
                if user:
                    logger.info(f"[AUTH] JWT Authentication successful for user: {user.username}")
                    return user
            except Exception as e:
                logger.warning(f"[AUTH] JWT Authentication failed: {str(e)}")
        
        return request.user
    
    def _is_api_request(self, request):
        """
        Determine if this request should be metered as an API call.
        """
        try:
            # Check the URL name from the resolver
            resolved = resolve(request.path_info)
            print(f"Resolved URL name: {resolved.url_name},----------{resolved}")
            logger.info(f"[RESOLVE] URL name: {resolved.url_name}")
            
            # List of URL names that should be metered
            metered_url_names = ['task-list-create', 'task-detail']
            if resolved.url_name in metered_url_names:
                print(f"Metered URL name: {resolved.url_name}")
                return True
        except Exception as e:
            logger.debug(f"URL resolution error: {str(e)}")
        
        # Secondary check using regex patterns
        metered_paths = [
            r'^/tasks/$',
            r'^/tasks/\d+/$',
        ]
        for pattern in metered_paths:
            if re.match(pattern, request.path):
                return True
        
        return False



# class APIUsageMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Manually authenticate user with JWT
#         user = self._get_jwt_user(request)
#         print(f"--------------------------")
#         print(f"Request path: {request.path}")
#         print(f"Request user: {user}")
#         print(f"User authenticated: {user.username if user else 'Anonymous'}")


#         if self._is_api_request(request) and user and user.is_authenticated:
#             print(f"+++++++++++++++-")
#             print(f"API call detected: {user.username}: {request.method} {request.path}")
#             logger.debug(f"Detected API call from user {user.username}: {request.method} {request.path}")
            
#             request.is_api_call = True
#             request.api_call_time = timezone.now()
#             request._authenticated_user = user  # store for later
#         else:
#             request.is_api_call = False

#         response = self.get_response(request)

#         if getattr(request, 'is_api_call', False):
#             from .signals import api_call_made
#             api_call_made.send(
#                 sender=self.__class__,
#                 user=getattr(request, '_authenticated_user', None),
#                 method=request.method,
#                 path=request.path,
#                 status_code=response.status_code,
#                 timestamp=request.api_call_time
#             )

#         return response

#     def _is_api_request(self, request):
#         try:
#             current_url = resolve(request.path_info)
#             url_name = current_url.url_name
#             print(f"Resolved URL name: {url_name},----------{current_url}")

#             metered_url_names = ['task-list-create', 'task-detail']
#             if url_name in metered_url_names:
#                 return True
#         except:
#             pass

#         metered_paths = [
#             r'^/tasks/$',
#             r'^/tasks/\d+/$',
#         ]
#         for pattern in metered_paths:
#             if re.match(pattern, request.path):
#                 return True
#         return False

#     def _get_jwt_user(self, request):
#         """
#         Authenticates the user using JWT from the Authorization header.
#         """
#         jwt_auth = JWTAuthentication()
#         try:
#             user_auth_tuple = jwt_auth.authenticate(Request(request))
#             if user_auth_tuple:
#                 return user_auth_tuple[0]
#         except AuthenticationFailed:
#             pass
#         return request.user  # Fallback