# backend_project/decorators.py
from functools import wraps
from django.shortcuts import redirect

def role_required(*roles_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            tipo = request.session.get("tipo")
            if tipo in roles_permitidos:
                return view_func(request, *args, **kwargs)
            return redirect('login')
        return wrapper
    return decorator
