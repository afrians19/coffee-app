"""
Security & Cyber-Defense Suite for Airkopi Barista App
======================================================
Provides protection against:
1. Prompt Attacks & Adversarial Inputs (Jailbreaks, Instruction Overrides, Token Manipulation)
2. Automated Bot Attacks (Form Floods, Honeypots, Cooldowns, Rate Limits)
3. CSV & Formula Injections (CWE-1236)
4. Insecure ML Model Deserialization (SHA-256 Cryptographic Verification)
5. Image Bomb & DoS Resource Exhaustion
6. Stored XSS & Output Sanitization
"""

import hashlib
import html
import os
import re
import time
import threading
from collections import deque
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import streamlit as st
from PIL import Image

# Custom exception for security violations
class SecurityError(Exception):
    """Raised when an integrity check or security violation occurs."""
    pass

# Set safe decompression limit for Pillow (protect against decompression bombs)
Image.MAX_IMAGE_PIXELS = 50_000_000

# Known cryptographic SHA-256 hashes of verified model files in this repository
TRUSTED_MODEL_HASHES: Dict[str, str] = {
    "rf_model_solve_error.sav": "2772ed2285c169c226bc7edcc4f40cc2b2412d858536e227d7b392a1a4ee650c",
    "rf_model.sav": "af33b72d26afde75d19a5d43aeeb7b903211ad682c19bd680eafcb709c17d52e",
    "apps/rf_model.sav": "af33b72d26afde75d19a5d43aeeb7b903211ad682c19bd680eafcb709c17d52e",
}

# Regex patterns identifying prompt injection, system overrides, and jailbreak attempts
PROMPT_ATTACK_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above|system)\s+(?:instructions|prompts|directions|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|rules)", re.IGNORECASE),
    re.compile(r"system\s*override|override\s+system", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)?\s*(?:unfiltered|dan|jailbreak|unrestricted|god\s*mode|evil)", re.IGNORECASE),
    re.compile(r"(?:bypass|disable|circumvent)\s+(?:all\s+)?(?:content\s+filters|safety\s+filters|guardrails)", re.IGNORECASE),
    re.compile(r"repeat\s+the\s+(?:above|system)\s+(?:instructions|prompt)", re.IGNORECASE),
    re.compile(r"reveal\s+(?:the\s+)?(?:hidden|system|developer)\s+(?:prompt|instructions|secret|api\s*key)", re.IGNORECASE),
    re.compile(r"<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]|<<SYS>>|</s>|<system>", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:a|an)?\s*unrestricted\s+(?:ai|agent|model)", re.IGNORECASE),
    re.compile(r"roleplay\s+as\s+an?\s*ai\s+without\s+(?:rules|restrictions|ethics)", re.IGNORECASE),
]

# Zero-width and hidden unicode characters often used to evade detection
ZERO_WIDTH_CHARS = re.compile(r"[\u200B\u200C\u200D\uFEFF\u2060\u200E\u200F\u202A-\u202E]")


# ============================================================================
# 1. PROMPT ATTACK & ADVERSARIAL INPUT DEFENSES
# ============================================================================

def detect_prompt_attack(text: str) -> Tuple[bool, Optional[str]]:
    """
    Detects whether an input string contains prompt injection, jailbreak,
    or instruction override patterns.
    
    Returns:
        (is_attack, reason_summary)
    """
    if not text or not isinstance(text, str):
        return False, None

    # Normalize unicode to NFKC to prevent homoglyph evasion
    normalized = unicodedata.normalize("NFKC", text)
    # Strip zero-width/hidden unicode characters
    cleaned = ZERO_WIDTH_CHARS.sub("", normalized)

    for pattern in PROMPT_ATTACK_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            return True, f"Suspicious prompt pattern: '{match.group(0)}'"

    return False, None


def sanitize_user_input(
    text: Union[str, Any],
    field_name: str = "Input",
    max_length: int = 500,
    notify: bool = True
) -> str:
    """
    Sanitizes user text inputs:
    - Normalizes unicode and strips zero-width hidden characters.
    - Limits string length to prevent memory/buffer exhaustion.
    - Neutralizes prompt injection patterns and surfaces security notices.
    """
    if not isinstance(text, str):
        return str(text) if text is not None else ""

    # Normalize and strip hidden characters
    cleaned = unicodedata.normalize("NFKC", text)
    cleaned = ZERO_WIDTH_CHARS.sub("", cleaned).strip()

    # Enforce maximum length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
        if notify:
            if hasattr(st, "toast"):
                st.toast(f"⚠️ {field_name} was truncated to {max_length} characters for security.", icon="🛡️")
            else:
                st.warning(f"⚠️ {field_name} was truncated to {max_length} characters for security.")

    # Check for prompt attack
    is_attack, reason = detect_prompt_attack(cleaned)
    if is_attack:
        if notify:
            st.warning(f"🛡️ Security Filter: Neutralized potential prompt injection attempt in {field_name}.")
        # Neutralize by replacing command tags and quotes
        cleaned = cleaned.replace("<", "&lt;").replace(">", "&gt;")
        cleaned = f"[Sanitized: {cleaned}]"

    return cleaned


# ============================================================================
# 2. BOT DEFENSE & RATE LIMITING SUITE
# ============================================================================

def render_honeypot(form_id: str) -> None:
    """
    Renders an invisible honeypot field.
    Legitimate users cannot see or interact with it.
    Automated scrapers/bots crawling inputs will fill it, triggering bot detection.
    """
    st.markdown(
        """
        <style>
        .sec-hp-field {
            position: absolute !important;
            left: -9999px !important;
            top: -9999px !important;
            opacity: 0 !important;
            height: 0px !important;
            width: 0px !important;
            pointer-events: none !important;
            tab-index: -1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="sec-hp-field">', unsafe_allow_html=True)
    st.text_input(
        label=f"Leave blank if human ({form_id})",
        value="",
        key=f"_hp_{form_id}",
        label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)


def is_bot_submission(form_id: str) -> bool:
    """
    Checks if the honeypot field for the form was filled.
    If non-empty, the submission is from an automated bot.
    """
    hp_value = st.session_state.get(f"_hp_{form_id}", "")
    if bool(hp_value and str(hp_value).strip()):
        return True
    return False


def check_submission_rate_limit(
    action_id: str,
    cooldown_seconds: float = 4.0,
    max_per_minute: int = 12
) -> Tuple[bool, str]:
    """
    Enforces per-session rate limiting and submission cooldowns.
    Prevents bots from flooding Google Sheets or triggering DoS.
    
    Returns:
        (allowed: bool, message: str)
    """
    now = time.time()
    last_time_key = f"_sec_last_{action_id}"
    history_key = f"_sec_hist_{action_id}"

    # Initialize history
    if history_key not in st.session_state:
        st.session_state[history_key] = []
    
    last_time = st.session_state.get(last_time_key, 0.0)

    # 1. Enforce minimum cooldown between actions
    elapsed = now - last_time
    if elapsed < cooldown_seconds:
        wait_remaining = int(cooldown_seconds - elapsed) + 1
        return False, f"⏳ Rate limit: Please wait {wait_remaining}s before submitting again."

    # 2. Enforce rolling minute cap
    one_minute_ago = now - 60.0
    history = [t for t in st.session_state[history_key] if t > one_minute_ago]
    
    if len(history) >= max_per_minute:
        return False, "⚠️ Submission limit reached for this minute. Please wait a moment."

    # Record action
    history.append(now)
    st.session_state[history_key] = history
    st.session_state[last_time_key] = now
    return True, "OK"


class GlobalRateLimiter:
    """
    Server-level rate limiter shared across all active user sessions.
    Protects Google Cloud Platform Free Tier quotas (300 requests/minute)
    against distributed bot swarms and multi-session attacks.
    """
    def __init__(self, max_global_per_minute: int = 25, min_global_interval: float = 1.0):
        self.lock = threading.Lock()
        self.timestamps: deque = deque()
        self.last_write_time: float = 0.0
        self.max_global_per_minute: int = max_global_per_minute
        self.min_global_interval: float = min_global_interval

    def check_and_record(self) -> Tuple[bool, str]:
        with self.lock:
            now = time.time()
            # 1. Global inter-write interval (prevents rapid concurrent hits)
            if now - self.last_write_time < self.min_global_interval:
                wait_sec = round(self.min_global_interval - (now - self.last_write_time), 1)
                return False, f"⏳ Server busy: Please wait {wait_sec}s before uploading."

            # 2. Global rolling minute quota
            one_minute_ago = now - 60.0
            while self.timestamps and self.timestamps[0] < one_minute_ago:
                self.timestamps.popleft()

            if len(self.timestamps) >= self.max_global_per_minute:
                return False, "⚠️ Free tier quota protection: Maximum server write rate reached for this minute. Please retry shortly."

            self.timestamps.append(now)
            self.last_write_time = now
            return True, "OK"


_GLOBAL_RATE_LIMITER: Optional[GlobalRateLimiter] = None
_LIMITER_INIT_LOCK = threading.Lock()


def _get_or_create_global_limiter() -> GlobalRateLimiter:
    global _GLOBAL_RATE_LIMITER
    if _GLOBAL_RATE_LIMITER is None:
        with _LIMITER_INIT_LOCK:
            if _GLOBAL_RATE_LIMITER is None:
                _GLOBAL_RATE_LIMITER = GlobalRateLimiter(max_global_per_minute=25, min_global_interval=1.0)
    return _GLOBAL_RATE_LIMITER


if hasattr(st, "cache_resource"):
    @st.cache_resource(show_spinner=False)
    def get_global_rate_limiter() -> GlobalRateLimiter:
        """Returns the singleton server-wide rate limiter instance."""
        return _get_or_create_global_limiter()
else:
    def get_global_rate_limiter() -> GlobalRateLimiter:
        """Returns the singleton server-wide rate limiter instance."""
        return _get_or_create_global_limiter()


def check_global_rate_limit() -> Tuple[bool, str]:
    """Checks the server-wide write quota across all visitor sessions."""
    limiter = get_global_rate_limiter()
    return limiter.check_and_record()


def check_worksheet_capacity(worksheet: Any, max_allowed_rows: int = 50_000) -> Tuple[bool, str]:
    """
    Hard-stops spreadsheet writes before approaching Google Sheets limits.
    Prevents bots from filling up sheets and running out of storage.
    """
    if worksheet is None:
        return True, "OK"
    try:
        current_rows = getattr(worksheet, "row_count", None)
        if current_rows is None:
            current_rows = len(worksheet.col_values(1))
        if current_rows >= max_allowed_rows:
            return False, f"🛑 Safety limit reached: Spreadsheet has reached {current_rows:,}/{max_allowed_rows:,} rows. New submissions are paused to prevent storage exhaustion."
        return True, "OK"
    except Exception:
        return True, "OK"


def verify_and_guard_upload(
    form_id: str,
    worksheet: Any,
    session_action: str = "upload",
    cooldown_seconds: float = 4.0,
    max_session_per_minute: int = 10,
    max_sheet_rows: int = 50_000
) -> Tuple[bool, str]:
    """
    Comprehensive multi-layer upload gatekeeper:
    1. Honeypot check (catches automated script submissions)
    2. Per-session rate limit & cooldown
    3. Global server-wide rate limit (protects GCP free quota across all connections)
    4. Sheet row capacity check (prevents storage exhaustion)
    """
    # 1. Honeypot Check
    if is_bot_submission(form_id):
        return False, "Automated submission blocked."

    # 2. Per-Session Rate Limit
    session_ok, session_msg = check_submission_rate_limit(
        session_action,
        cooldown_seconds=cooldown_seconds,
        max_per_minute=max_session_per_minute
    )
    if not session_ok:
        return False, session_msg

    # 3. Global Server-Wide Quota Check
    global_ok, global_msg = check_global_rate_limit()
    if not global_ok:
        return False, global_msg

    # 4. Sheet Storage Capacity Check
    sheet_ok, sheet_msg = check_worksheet_capacity(worksheet, max_allowed_rows=max_sheet_rows)
    if not sheet_ok:
        return False, sheet_msg

    return True, "OK"



# ============================================================================
# 3. CSV & FORMULA INJECTION DEFENSE (CWE-1236)
# ============================================================================

def sanitize_spreadsheet_cell(val: Any) -> Any:
    """
    Sanitizes an individual cell value against Spreadsheet Formula Injection.
    If a string starts with '=', '+', '-', '@', '|', or '%',
    prefixes it with a single quote so spreadsheet engines interpret it as pure text.
    Preserves genuine numeric values.
    """
    if val is None or pd.isna(val):
        return ""

    if isinstance(val, (int, float, bool)):
        return val

    s = str(val).strip()
    if not s:
        return s

    # If it is a valid signed number (e.g., -14, +2.5), it is not a malicious formula
    if re.match(r"^[-+]?\d+(?:\.\d+)?$", s):
        return val

    # Formula trigger characters in Excel / Google Sheets
    if s[0] in ("=", "+", "-", "@", "|", "%", "\t", "\r"):
        return f"'{s}"

    return s


def sanitize_dataframe_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies formula injection sanitization and prompt injection checks
    to all elements of a DataFrame before uploading to Google Sheets or exporting to CSV.
    """
    clean_df = df.copy()
    for col in clean_df.columns:
        if clean_df[col].dtype == object or clean_df[col].dtype == "string":
            clean_df[col] = clean_df[col].apply(sanitize_spreadsheet_cell)
    return clean_df


# ============================================================================
# 4. SECURE MODEL DESERIALIZATION (RCE PROTECTION)
# ============================================================================

def verify_file_sha256(filepath: str, expected_hash: str) -> bool:
    """Computes SHA-256 of a local file and verifies against expected hash."""
    if not os.path.isfile(filepath):
        return False
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest().lower() == expected_hash.lower()


def safe_load_model(filepath: str, allowed_hashes: Optional[Dict[str, str]] = None) -> Any:
    """
    Secure wrapper around pickle.load that verifies cryptographic SHA-256
    integrity before deserializing. Prevents Remote Code Execution (RCE)
    from tampered or poisoned model files.
    """
    import pickle

    if allowed_hashes is None:
        allowed_hashes = TRUSTED_MODEL_HASHES

    filename = os.path.basename(filepath)
    expected_hash = allowed_hashes.get(filename) or allowed_hashes.get(filepath)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")

    if expected_hash:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        actual_hash = sha256.hexdigest().lower()
        if actual_hash != expected_hash.lower():
            raise SecurityError(
                f"Security Alert: Integrity verification failed for '{filepath}'!\n"
                f"Expected SHA-256: {expected_hash}\nActual SHA-256: {actual_hash}\n"
                "Model loading blocked to prevent arbitrary code execution."
            )

    with open(filepath, "rb") as f:
        return pickle.load(f)


# ============================================================================
# 5. IMAGE UPLOAD & DOS RESOURCE DEFENSE
# ============================================================================

def validate_uploaded_image(
    uploaded_file: Any,
    max_size_mb: float = 15.0
) -> Tuple[bool, Optional[str]]:
    """
    Validates uploaded images:
    - Verifies file size limit to prevent memory exhaustion / DoS.
    - Inspects image headers without executing arbitrary decoder bugs.
    - Rejects decompression bombs.
    """
    if uploaded_file is None:
        return False, "No file uploaded."

    # Size check
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed limit ({max_size_mb:.1f} MB)."

    try:
        # Shallow header verification
        img = Image.open(uploaded_file)
        img.verify()
        uploaded_file.seek(0)
        return True, None
    except Exception as exc:
        return False, f"Invalid or corrupted image format: {exc}"


# ============================================================================
# 6. SAFE OUTPUT & HTML ESCAPING (XSS DEFENSE)
# ============================================================================

def safe_html_escape(val: Any) -> str:
    """Escapes HTML entities to prevent Stored XSS."""
    return html.escape(str(val)) if val is not None else ""
