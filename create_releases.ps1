# PowerShell скрипт для создания релизов на GitHub
# Запуск: .\create_releases.ps1

$repo = "Miromani4/SIP-Phone-for-HA"
$token = $env:GITHUB_TOKEN  # Или вставьте токен напрямую (не рекомендуется)

if (-not $token) {
    Write-Host "GITHUB_TOKEN не установлен. Введите токен:" -ForegroundColor Yellow
    $token = Read-Host "GitHub Personal Access Token"
}

$headers = @{
    "Authorization" = "token $token"
    "Accept" = "application/vnd.github.v3+json"
    "User-Agent" = "PowerShell"
}

# Функция создания релиза
function Create-Release {
    param(
        [string]$TagName,
        [string]$Title,
        [string]$Body
    )
    
    $body = @{
        tag_name = $TagName
        name = $Title
        body = $Body
        draft = $false
        prerelease = $false
    } | ConvertTo-Json
    
    $url = "https://api.github.com/repos/$repo/releases"
    
    Write-Host "Создание релиза $TagName..." -ForegroundColor Cyan
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body -ContentType "application/json"
        Write-Host "✓ Релиз создан: $($response.html_url)" -ForegroundColor Green
    } catch {
        $errorBody = $_.ErrorDetails.Message | ConvertFrom-Json
        if ($errorBody.errors -and $errorBody.errors[0].code -eq "already_exists") {
            Write-Host "⚠ Релиз $TagName уже существует" -ForegroundColor Yellow
        } else {
            Write-Host "✗ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "Ответ: $errorBody"
        }
    }
}

# v1.1.3
Create-Release -TagName "v1.1.3" -Title "v1.1.3 - Bug Fix Release" -Body @"
## 🐛 Bug Fixes

### Fixed
- **NameError in switch.py**: Fixed undefined variable 'phone' in device_info property
  - Changed `"phone.user"` to `"`self._phone.user`"`
  - Error: `"NameError: name 'phone' is not defined`"`

## 📦 Installation

Update via HACS:
1. HACS → Integrations → SIP Doorbell
2. Click `"Download`" or `"Update`"
3. Restart Home Assistant

**Full Changelog**: https://github.com/$repo/compare/v1.1.2...v1.1.3
"@

# v1.1.2
Create-Release -TagName "v1.1.2" -Title "v1.1.2 - Popup & Status Fixes" -Body @"
## 🔧 Bug Fixes

### Fixed
- **Popup card not opening**: Added debug logging for events
- **hangup() not working in RINGING state**: Now properly rejects incoming calls
  - Sends 487 Request Terminated for ringing calls
  - Clears `"_dialog"` and `"_pending_invite"` after call ends
- **Status not updating after hangup**: Fixed state transition
  - RINGING → HANGUP → REGISTERED

## 📦 Installation

Update via HACS:
1. HACS → Integrations → SIP Doorbell
2. Click `"Download`" or `"Update`"
3. Restart Home Assistant

**Full Changelog**: https://github.com/$repo/compare/v1.1.1...v1.1.2
"@

# v1.1.1
Create-Release -TagName "v1.1.1" -Title "v1.1.1 - Documentation Update" -Body @"
## 📝 Documentation

### Added
- Complete README.md with installation and configuration examples
- Automation examples (door opening, notifications, video recording)
- WebSocket API documentation
- Call Popup card installation guide
- Updated info.md for HACS

## 📦 Installation

Update via HACS:
1. HACS → Integrations → SIP Doorbell
2. Click `"Download`" or `"Update`"
3. Restart Home Assistant

**Full Changelog**: https://github.com/$repo/compare/v1.1.0...v1.1.1
"@

# v1.1.0
Create-Release -TagName "v1.1.0" -Title "v1.1.0 - Call Popup & WebSocket API" -Body @"
## ✨ New Features

### Added
- **WebSocket API** for real-time call events
  - `"sip_doorbell/subscribe_calls"` — Subscribe to incoming/ended calls
  - `"sip_doorbell/get_status"` — Get current SIP phone status
- **Frontend Popup Card** (`"call_popup.js`") for incoming calls
  - Auto-open on incoming call
  - Caller ID display (name & number)
  - Answer/Hangup buttons
  - DTMF keypad for door opening
- **Caller ID Parsing** from SIP headers

### Events
- `"sip_doorbell_incoming_call"` — Fired when call arrives
- `"sip_doorbell_call_ended"` — Fired when call ends

## 📦 Installation

Update via HACS:
1. HACS → Integrations → SIP Doorbell
2. Click `"Download`" or `"Update`"
3. Restart Home Assistant

### Popup Card Setup
1. Settings → Dashboards → Resources → Add Resource
2. URL: `"/hacsfiles/sip_doorbell/call_popup.js`"
3. Type: Module
4. Add card to dashboard

**Full Changelog**: https://github.com/$repo/compare/v1.0.4...v1.1.0
"@

Write-Host "`n✅ Готово!" -ForegroundColor Green
