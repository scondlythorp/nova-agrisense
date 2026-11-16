from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthTokenResponse,
    ChangePasswordRequest,
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    UserProfileResponse,
)
from app.security.dependencies import get_current_user, verify_csrf_for_cookie_request
from app.security.rate_limit import auth_rate_limiter
from app.security.tokens import generate_csrf_token
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _client_ip(request: Request) -> str:
    settings = get_settings()
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Behind trusted reverse proxies (e.g., Cloud Run / GCLB), the rightmost
            # proxy-appended entry reflects the peer IP rather than client-spoofed prefix.
            parts = [part.strip() for part in forwarded.split(",") if part.strip()]
            if parts:
                return parts[-1]
    return request.client.host if request.client else "unknown"


def _set_auth_cookies(response: Response, raw_refresh_token: str) -> str:
    settings = get_settings()
    max_age = settings.refresh_token_expire_days * 86400
    csrf_token = generate_csrf_token()
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw_refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.effective_cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path=f"{settings.api_v1_prefix}/auth",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.effective_cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
    )
    return csrf_token


def _clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        domain=settings.cookie_domain,
        path=f"{settings.api_v1_prefix}/auth",
    )
    response.delete_cookie(
        key=settings.csrf_cookie_name,
        domain=settings.cookie_domain,
        path="/",
    )


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    settings = get_settings()
    auth_rate_limiter.check(
        f"register:{_client_ip(request)}",
        max_attempts=settings.auth_rate_limit_max_attempts,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    return auth_service.register_user(
        db,
        payload,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    summary="Authenticate user and issue access token + HttpOnly refresh cookie",
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthTokenResponse:
    settings = get_settings()
    ip = _client_ip(request)
    normalized_email = payload.email.strip().lower()
    auth_rate_limiter.check(
        f"login:ip:{ip}",
        max_attempts=settings.auth_rate_limit_max_attempts * 2,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    auth_rate_limiter.check(
        f"login:acct:{normalized_email}",
        max_attempts=settings.auth_rate_limit_max_attempts,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )

    token_response, raw_refresh = auth_service.login_user(
        db,
        payload,
        request_id=getattr(request.state, "request_id", None),
        user_agent=request.headers.get("User-Agent"),
        ip_address=ip,
    )
    token_response.csrf_token = _set_auth_cookies(response, raw_refresh)
    return token_response


@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
    dependencies=[Depends(verify_csrf_for_cookie_request)],
    summary="Rotate refresh cookie and issue a fresh access token",
)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthTokenResponse:
    settings = get_settings()
    ip = _client_ip(request)
    auth_rate_limiter.check(
        f"refresh:{ip}",
        max_attempts=settings.auth_rate_limit_max_attempts * 2,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )

    raw_refresh = request.cookies.get(settings.refresh_cookie_name)
    try:
        token_response, new_raw_refresh = auth_service.rotate_refresh_session(
            db,
            raw_refresh,
            request_id=getattr(request.state, "request_id", None),
            user_agent=request.headers.get("User-Agent"),
            ip_address=ip,
        )
    except Exception:
        _clear_auth_cookies(response)
        raise

    token_response.csrf_token = _set_auth_cookies(response, new_raw_refresh)
    return token_response


@router.post(
    "/logout",
    response_model=LogoutResponse,
    dependencies=[Depends(verify_csrf_for_cookie_request)],
    summary="Revoke active refresh session and clear authentication cookies",
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> LogoutResponse:
    settings = get_settings()
    raw_refresh = request.cookies.get(settings.refresh_cookie_name)
    revoked = auth_service.revoke_refresh_session(
        db,
        raw_refresh,
        request_id=getattr(request.state, "request_id", None),
    )
    _clear_auth_cookies(response)
    return LogoutResponse(
        revoked=revoked,
        message="Session closed.",
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get authenticated user profile and organization memberships",
)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    return auth_service.build_user_profile(db, current_user)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change authenticated user password and revoke active refresh sessions",
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    auth_service.change_user_password(
        db,
        current_user,
        payload,
        request_id=getattr(request.state, "request_id", None),
    )
    _clear_auth_cookies(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
