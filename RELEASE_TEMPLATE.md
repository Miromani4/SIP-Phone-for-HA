# 📝 Инструкция по созданию релизов на GitHub

## Создание релиза через GitHub UI

1. Откройте страницу релизов: https://github.com/Miromani4/SIP-Phone-for-HA/releases/new

2. **Choose a tag**: Выберите существующий тег (например, `v1.1.3`)

3. **Target**: `main`

4. **Release title**: `v1.1.3 - Bug Fix Release`

5. **Description** (скопируйте шаблон ниже):

---

## Шаблон описания релиза

```markdown
## 🐛 Bug Fixes

### Fixed
- **Описание проблемы**: Что было исправлено
  - Детали исправления

## 📦 Installation

Update via HACS:
1. HACS → Integrations → SIP Doorbell
2. Click "Download" or "Update"
3. Restart Home Assistant

**Full Changelog**: https://github.com/Miromani4/SIP-Phone-for-HA/compare/v1.1.2...v1.1.3
```

---

## Пример для v1.1.3

```markdown
## 🐛 Bug Fixes

### Fixed
- **NameError in switch.py**: Fixed undefined variable 'phone' in device_info property
  - Changed `phone.user` to `self._phone.user`
  - Error: `NameError: name 'phone' is not defined`

## 📦 Installation

Update via HACS:
1. HACS → Integrations → SIP Doorbell
2. Click "Download" or "Update"
3. Restart Home Assistant

**Full Changelog**: https://github.com/Miromani4/SIP-Phone-for-HA/compare/v1.1.2...v1.1.3
```

---

## Пример для v1.1.2

```markdown
## 🔧 Bug Fixes

### Fixed
- **Popup card not opening**: Added debug logging for events
- **hangup() not working in RINGING state**: Now properly rejects incoming calls
  - Sends 487 Request Terminated for ringing calls
  - Clears `_dialog` and `_pending_invite` after call ends
- **Status not updating after hangup**: Fixed state transition
  - RINGING → HANGUP → REGISTERED
  - EVENT_CALL_ENDED fired before state change

## 📦 Installation

Update via HACS:
1. HACS → Integrations → SIP Doorbell
2. Click "Download" or "Update"
3. Restart Home Assistant

**Full Changelog**: https://github.com/Miromani4/SIP-Phone-for-HA/compare/v1.1.1...v1.1.2
```

---

## Пример для v1.1.1

```markdown
## 📝 Documentation

### Added
- Complete README.md with installation and configuration examples
- Automation examples (door opening, notifications, video recording)
- WebSocket API documentation
- Call Popup card installation guide
- Updated info.md for HACS
- Full changelog for all versions

## 📦 Installation

Update via HACS:
1. HACS → Integrations → SIP Doorbell
2. Click "Download" or "Update"
3. Restart Home Assistant

**Full Changelog**: https://github.com/Miromani4/SIP-Phone-for-HA/compare/v1.1.0...v1.1.1
```

---

## Пример для v1.1.0

```markdown
## ✨ New Features

### Added
- **WebSocket API** for real-time call events
  - `sip_doorbell/subscribe_calls` — Subscribe to incoming/ended calls
  - `sip_doorbell/get_status` — Get current SIP phone status
- **Frontend Popup Card** for incoming calls
  - Auto-open on incoming call
  - Caller ID display (name & number)
  - Answer/Hangup buttons
  - DTMF keypad for door opening
- **Caller ID Parsing** from SIP headers
  - Extracts name and number from SIP From header
- **Auto-answer support** — Works correctly now

### Events
- `sip_doorbell_incoming_call` — Fired when call arrives
- `sip_doorbell_call_ended` — Fired when call ends

## 📦 Installation

Update via HACS:
1. HACS → Integrations → SIP Doorbell
2. Click "Download" or "Update"
3. Restart Home Assistant

### Popup Card Setup
1. Settings → Dashboards → Resources → Add Resource
2. URL: `/hacsfiles/sip_doorbell/call_popup.js`
3. Type: Module
4. Add card to dashboard:
```yaml
type: custom:sip-doorbell-call-popup
title: 🔔 Doorbell
auto_open: true
auto_close: true
timeout: 30
```

**Full Changelog**: https://github.com/Miromani4/SIP-Phone-for-HA/compare/v1.0.4...v1.1.0
```

---

## Пример для v1.0.4

```markdown
## 🔧 Thread Safety Fix

### Fixed
- **RuntimeError in async_dispatcher_send**: Fixed thread-safe dispatch
  - Uses `asyncio.run_coroutine_threadsafe()` for proper event loop scheduling
  - Prevents "calls async_dispatcher_send from a thread other than the event loop" error

## 📦 Installation

**IMPORTANT**: After update:
1. Delete integration
2. Clear cache: `rm -rf /config/custom_components/sip_doorbell/__pycache__`
3. Restart Home Assistant
4. Reinstall via HACS

Update via HACS:
1. HACS → Integrations → SIP Doorbell
2. Click "Download" or "Update"
3. **Restart Home Assistant**

**Full Changelog**: https://github.com/Miromani4/SIP-Phone-for-HA/compare/v1.0.3...v1.1.0
```

---

## Советы

1. **SemVer**: Используйте семантическую версионность (MAJOR.MINOR.PATCH)
   - MAJOR: Несовместимые изменения API
   - MINOR: Новые функции (обратно совместимые)
   - PATCH: Исправления багов

2. **Changelog**: Всегда добавляйте ссылку на полный changelog

3. **Installation**: Указывайте инструкции по установке

4. **Breaking Changes**: Если есть, выделите отдельным разделом
