# Existing Streamlit Application — Inspection & Migration Readiness

## Current Status

**The legacy Streamlit source files have NOT been supplied in the workspace.**

Expected files listed in the project brief:
- `app.py`
- `crop_recommend.py`
- `weather_bot.py`
- `farmer_tools.py`
- `i18n.py`
- `sms_ussd_stub.py`
- `requirements.txt`
- `README.md`

Per project rules, no inspection or migration claims are made for files that are not present.

## Migration Plan Once Source Files Are Provided

1. **Audit each file** for business logic, hardcoded keys/URLs, unsafe file/SQL operations, and Streamlit state assumptions (`st.session_state`).
2. **Preserve & Refactor**:
   - `crop_recommend.py` -> `apps/api/app/analytics/` (transparent rule-based recommendation engine with documented inputs, limits, and uncertainty notes).
   - `weather_bot.py` -> `apps/api/app/integrations/` (provider-independent weather adapter returning explicit unavailable/unconfigured states when no API key exists).
   - `farmer_tools.py` -> `apps/api/app/modules/` (validated unit conversions, area/yield calculators).
   - `i18n.py` -> `packages/shared-config/` + `apps/web/` localization dictionaries (English and Gambian local-language keys).
   - `sms_ussd_stub.py` -> `apps/api/app/integrations/` (documented low-connectivity gateway interface).
3. **Discard** all Streamlit UI rendering calls (`st.*`) in favor of Next.js + FastAPI REST endpoints.
