# 📱 Полное руководство по настройке SIP Soft Phone для Home Assistant

## Содержание

1. [Общая архитектура](#общая-архитектура)
2. [Требования](#требования)
3. [Установка](#установка)
4. [Настройка SIP сервера (Asterisk)](#настройка-sip-сервера-asterisk)
5. [Настройка Home Assistant](#настройка-home-assistant)
6. [Настройка карточки звонка](#настройка-карточки-звонка)
7. [Кастомизация](#кастомизация)
8. [Использование](#использование)
9. [Диагностика](#диагностика)
10. [Дополнительные возможности](#дополнительные-возможности)

---

## Общая архитектура

```
┌─────────────────┐     SIP (UDP 5060)     ┌─────────────────┐
│   IP Телефон    │◄───────────────────────►│    Asterisk     │
│   или Софтфон   │                         │   (SIP Сервер)  │
└─────────────────┘                         └────────┬────────┘
                                                     │
┌─────────────────┐     SIP (UDP 5060)             │
│  Домофон/Камера │◄────────────────────────────────┤
└─────────────────┘                                   │
                                                      │
┌─────────────────┐     SIP (UDP 5060)              │
│   HA Extension  │◄──────────────────────────────────┘
│  (Эта интеграция)│
└────────┬────────┘
         │
         │ HTTP/WebSocket (events)
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Home Assistant │────►│  Web Browser    │
│    (Frontend)    │     │  (Dashboard)     │
└─────────────────┘     └─────────────────┘
```

---

## Требования

### Аппаратные требования

- **Home Assistant**:
  - RAM: минимум 2GB (рекомендуется 4GB+)
  - CPU: любой современный процессор
  - Сеть: стабильное подключение к LAN

- **SIP Сервер (Asterisk)**:
  - Может работать на том же сервере что и HA
  - Требует UDP порты 5060 (SIP) и 10000-20000 (RTP)

### Программные требования

- Home Assistant Core 2023.12+
- HACS (Home Assistant Community Store) - для установки
- Asterisk 18+ или другой SIP сервер

---

## Установка

### Способ 1: Через HACS (Рекомендуется)

1. Убедитесь что HACS установлен:
   ```bash
   # В терминале HA
   wget -q -O - https://hacs.vip/install | bash -
   ```

2. Добавьте кастомный репозиторий:
   - Откройте HACS → Интеграции
   - Нажмите ⋮ → Пользовательские репозитории
   - URL: `https://github.com/Miromani4/SIP-Phone-for-HA`
   - Категория: Интеграция

3. Найдите "SIP Doorbell" и установите

4. Перезапустите Home Assistant

### Способ 2: Ручная установка

```bash
# SSH в Home Assistant
cd /config/custom_components
mkdir -p sip_doorbell
cd sip_doorbell

# Скачайте файлы интеграции
wget https://raw.githubusercontent.com/Miromani4/SIP-Phone-for-HA/main/custom_components/sip_doorbell/__init__.py
wget https://raw.githubusercontent.com/Miromani4/SIP-Phone-for-HA/main/custom_components/sip_doorbell/config_flow.py
wget https://raw.githubusercontent.com/Miromani4/SIP-Phone-for-HA/main/custom_components/sip_doorbell/const.py
wget https://raw.githubusercontent.com/Miromani4/SIP-Phone-for-HA/main/custom_components/sip_doorbell/phone.py
wget https://raw.githubusercontent.com/Miromani4/SIP-Phone-for-HA/main/custom_components/sip_doorbell/sensor.py
wget https://raw.githubusercontent.com/Miromani4/SIP-Phone-for-HA/main/custom_components/sip_doorbell/switch.py
wget https://raw.githubusercontent.com/Miromani4/SIP-Phone-for-HA/main/custom_components/sip_doorbell/manifest.json
wget https://raw.githubusercontent.com/Miromani4/SIP-Phone-for-HA/main/custom_components/sip_doorbell/services.yaml

mkdir -p translations
wget -P translations/ https://raw.githubusercontent.com/Miromani4/SIP-Phone-for-HA/main/custom_components/sip_doorbell/translations/en.json
wget -P translations/ https://raw.githubusercontent.com/Miromani4/SIP-Phone-for-HA/main/custom_components/sip_doorbell/translations/ru.json

# Перезапустите Home Assistant
```

---

## Настройка SIP сервера (Asterisk)

### Установка Asterisk (Debian/Ubuntu)

```bash
# Установка зависимостей
sudo apt update
sudo apt install -y asterisk

# Резервная копия конфигов
sudo cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.backup
sudo cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup
```

### Конфигурация pjsip.conf

```ini
; /etc/asterisk/pjsip.conf

[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060

; ================================
; Extension для Home Assistant
; ================================
[ha_sip_user]
type=aor
max_contacts=5
remove_existing=yes

[ha_sip_user]
type=auth
auth_type=userpass
username=ha_sip_user
password=SecurePassword123!

[ha_sip_user]
type=endpoint
context=from-internal
disallow=all
allow=ulaw
allow=alaw
allow=g722
auth=ha_sip_user
aors=ha_sip_user
direct_media=no
dtmf_mode=rfc4733

; ================================
; Extension для домофона
; ================================
[doorbell]
type=aor
max_contacts=1

[doorbell]
type=auth
auth_type=userpass
username=doorbell
password=DoorbellPass456!

[doorbell]
type=endpoint
context=from-internal
disallow=all
allow=ulaw
allow=alaw
auth=doorbell
aors=doorbell
direct_media=no

; ================================
; Пример: Extension для мобильного
; ================================
[mobile_app]
type=aor
max_contacts=5
remove_existing=yes

[mobile_app]
type=auth
auth_type=userpass
username=mobile_app
password=MobilePass789!

[mobile_app]
type=endpoint
context=from-internal
disallow=all
allow=ulaw
allow=alaw
allow=g722
auth=mobile_app
aors=mobile_app
direct_media=no
dtmf_mode=rfc4733
```

### Конфигурация extensions.conf

```ini
; /etc/asterisk/extensions.conf

[general]
static=yes
writeprotect=no

[from-internal]
; Набор номера для вызова HA
exten => 100,1,Dial(PJSIP/ha_sip_user)
 same => n,Hangup()

; Набор номера для вызова домофона
exten => 101,1,Dial(PJSIP/doorbell)
 same => n,Hangup()

; Набор номера для вызова мобильного
exten => 102,1,Dial(PJSIP/mobile_app)
 same => n,Hangup()

; Вызов группы (HA + Мобильное)
exten => 200,1,Dial(PJSIP/ha_sip_user&PJSIP/mobile_app,30)
 same => n,VoiceMail(100@default)
 same => n,Hangup()

; Пример: Переадресация с домофона на HA
exten => doorbell,1,NoOp(Incoming call from doorbell)
 same => n,Set(CALLERID(name)=Doorbell)
 same => n,Dial(PJSIP/ha_sip_user&PJSIP/mobile_app,60)
 same => n,VoiceMail(100@default)
 same => n,Hangup()
```

### Перезапуск Asterisk

```bash
# Проверка конфигурации
sudo asterisk -rx "core reload"

# Перезапуск
sudo systemctl restart asterisk

# Проверка статуса
sudo systemctl status asterisk

# Просмотр зарегистрированных extension
sudo asterisk -rx "pjsip show endpoints"
```

---

## Настройка Home Assistant

### Добавление интеграции

1. **Настройки → Устройства и службы → Добавить интеграцию**
2. Найдите **"SIP Doorbell"**

3. **Заполните параметры:**

| Параметр | Описание | Пример |
|----------|----------|--------|
| SIP Сервер | IP или hostname Asterisk | `192.168.1.100` |
| SIP Порт | Порт сервера (обычно 5060) | `5060` |
| SIP Пользователь | Имя пользователя (extension) | `ha_sip_user` |
| SIP Пароль | Пароль из pjsip.conf | `SecurePassword123!` |
| SIP Realm | Домен авторизации | `asterisk` |
| Автоответ | Отвечать автоматически | `false` |

### Добавление в configuration.yaml (опционально)

```yaml
# Если нужно дополнительно настроить логирование
logger:
  default: warning
  logs:
    custom_components.sip_doorbell: debug
```

---

## Настройка карточки звонка

### Способ 1: Модульная карточка (Рекомендуется)

Создайте файл `www/sip-doorbell-card.js`:

```javascript
// www/sip-doorbell-card.js

class SIPDoorbellCard extends HTMLElement {
    constructor() {
        super();
        this._config = {};
        this._hass = null;
    }

    setConfig(config) {
        this._config = {
            title: '☎️ SIP Телефон',
            entity: null,
            camera_entity: null,
            position: 'center',
            theme: 'auto',
            auto_open: true,
            timeout: 30,
            show_dtmf: true,
            ...config
        };
    }

    set hass(hass) {
        this._hass = hass;
        
        if (!this.content) {
            this._createContent();
            this._subscribeEvents();
        }
        
        this._updateUI();
    }

    _createContent() {
        this.innerHTML = `
            <ha-card>
                <div class="card-header">
                    ${this._config.title}
                </div>
                <div class="card-content">
                    <div id="sip-status" class="sip-status">
                        <span class="status-indicator"></span>
                        <span class="status-text">Инициализация...</span>
                    </div>
                    
                    <div id="active-call" class="active-call" style="display: none;">
                        <div class="caller-info">
                            <ha-icon icon="mdi:phone-incoming"></ha-icon>
                            <div class="caller-details">
                                <div class="caller-name">Входящий звонок</div>
                                <div class="caller-number">-</div>
                            </div>
                        </div>
                        
                        <div class="call-actions">
                            <mwc-button raised id="btn-answer" class="btn-answer">
                                <ha-icon icon="mdi:phone"></ha-icon> Ответить
                            </mwc-button>
                            <mwc-button outlined id="btn-decline" class="btn-decline">
                                <ha-icon icon="mdi:phone-hangup"></ha-icon> Отклонить
                            </mwc-button>
                        </div>
                        
                        <div id="dtmf-panel" class="dtmf-panel" style="display: none;">
                            <div class="dtmf-grid">
                                ${[1,2,3,4,5,6,7,8,9,'*',0,'#'].map(d => `
                                    <button class="dtmf-btn" data-digit="${d}">${d}</button>
                                `).join('')}
                            </div>
                            <mwc-button outlined id="btn-hangup" class="btn-hangup">
                                <ha-icon icon="mdi:phone-hangup"></ha-icon> Завершить
                            </mwc-button>
                        </div>
                    </div>
                </div>
            </ha-card>
        `;

        this.content = this.querySelector('.card-content');
        this._setupEventListeners();
    }

    _setupEventListeners() {
        const answerBtn = this.querySelector('#btn-answer');
        const declineBtn = this.querySelector('#btn-decline');
        const hangupBtn = this.querySelector('#btn-hangup');
        const dtmfBtns = this.querySelectorAll('.dtmf-btn');

        answerBtn?.addEventListener('click', () => {
            this._hass.callService('sip_doorbell', 'answer');
            this._showDtmfPanel();
        });

        declineBtn?.addEventListener('click', () => {
            this._hass.callService('sip_doorbell', 'hangup');
        });

        hangupBtn?.addEventListener('click', () => {
            this._hass.callService('sip_doorbell', 'hangup');
        });

        dtmfBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const digit = e.target.dataset.digit;
                this._hass.callService('sip_doorbell', 'send_dtmf', {
                    digits: digit,
                    duration: 250
                });
            });
        });
    }

    async _subscribeEvents() {
        this._hass.connection.subscribeEvents((event) => {
            if (event.event_type === 'sip_doorbell_incoming_call') {
                this._handleIncomingCall(event.data);
            } else if (event.event_type === 'sip_doorbell_call_ended') {
                this._handleCallEnded();
            }
        });
    }

    _handleIncomingCall(data) {
        const activeCall = this.querySelector('#active-call');
        const callerNumber = activeCall.querySelector('.caller-number');
        
        callerNumber.textContent = data.caller_number || data.caller || 'Неизвестно';
        activeCall.style.display = 'block';
        
        // Вибрация на мобильных
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200]);
        }
    }

    _handleCallEnded() {
        const activeCall = this.querySelector('#active-call');
        const dtmfPanel = this.querySelector('#dtmf-panel');
        
        activeCall.style.display = 'none';
        dtmfPanel.style.display = 'none';
    }

    _showDtmfPanel() {
        const dtmfPanel = this.querySelector('#dtmf-panel');
        const callActions = this.querySelector('.call-actions');
        
        dtmfPanel.style.display = 'block';
        callActions.style.display = 'none';
    }

    _updateUI() {
        const entity = this._hass.states[this._config.entity];
        const statusEl = this.querySelector('#sip-status');
        
        if (entity) {
            const state = entity.state;
            const statusText = {
                'unregistered': 'Не зарегистрирован',
                'registering': 'Регистрация...',
                'registered': '✓ Готов к звонкам',
                'ringing': 'Входящий звонок!',
                'in_call': 'Разговор',
                'hangup': 'Завершено'
            }[state] || state;
            
            statusEl.querySelector('.status-text').textContent = statusText;
            statusEl.querySelector('.status-indicator').className = 
                `status-indicator status-${state}`;
        }
    }

    getCardSize() {
        return 3;
    }

    static getConfigElement() {
        return document.createElement('sip-doorbell-card-editor');
    }

    static getStubConfig() {
        return {
            title: '☎️ SIP Телефон',
            entity: 'sensor.sip_doorbell_state'
        };
    }
}

customElements.define('sip-doorbell-card', SIPDoorbellCard);

// Редактор конфигурации
class SIPDoorbellCardEditor extends HTMLElement {
    setConfig(config) {
        this._config = config;
        this.render();
    }

    render() {
        this.innerHTML = `
            <div class="card-config">
                <h3>SIP Doorbell Card</h3>
                <p>Конфигурация в YAML:</p>
                <pre>
type: custom:sip-doorbell-card
title: ☎️ Мой SIP
entity: sensor.sip_doorbell_state
camera_entity: camera.doorbell
auto_open: true
                </pre>
            </div>
        `;
    }
}

customElements.define('sip-doorbell-card-editor', SIPDoorbellCardEditor);

// Стили
const style = document.createElement('style');
style.textContent = `
    .sip-status {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px;
        background: var(--card-background-color);
        border-radius: 8px;
    }
    
    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #9e9e9e;
    }
    
    .status-registered { background: #4caf50; }
    .status-ringing { background: #ff9800; animation: pulse 1s infinite; }
    .status-in_call { background: #f44336; }
    .status-registering { background: #2196f3; animation: pulse 1s infinite; }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .active-call {
        margin-top: 16px;
        padding: 16px;
        background: var(--secondary-background-color);
        border-radius: 12px;
    }
    
    .caller-info {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
    }
    
    .caller-details {
        flex: 1;
    }
    
    .caller-name {
        font-weight: 500;
        font-size: 1.1em;
    }
    
    .caller-number {
        color: var(--secondary-text-color);
    }
    
    .call-actions {
        display: flex;
        gap: 12px;
    }
    
    .call-actions mwc-button {
        flex: 1;
    }
    
    .btn-answer {
        --mdc-theme-primary: #4caf50;
    }
    
    .btn-decline, .btn-hangup {
        --mdc-theme-primary: #f44336;
    }
    
    .dtmf-panel {
        margin-top: 16px;
    }
    
    .dtmf-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 12px;
    }
    
    .dtmf-btn {
        padding: 16px;
        font-size: 1.2em;
        border: none;
        border-radius: 8px;
        background: var(--primary-color);
        color: white;
        cursor: pointer;
    }
    
    .dtmf-btn:hover {
        opacity: 0.9;
    }
    
    .dtmf-btn:active {
        transform: scale(0.95);
    }
`;
document.head.appendChild(style);
```

### Регистрация карточки

1. Создайте файл `configuration.yaml`:

```yaml
lovelace:
  mode: yaml
  resources:
    - url: /local/sip-doorbell-card.js
      type: module
```

2. Добавьте в Dashboard:

```yaml
type: custom:sip-doorbell-card
title: ☎️ SIP Телефон
entity: sensor.sip_doorbell_state
camera_entity: camera.doorbell  # Опционально
auto_open: true
```

### Способ 2: Использование встроенной карточки

```yaml
type: custom:sip-doorbell-call-popup
title: 🔔 Входящий звонок
auto_open: true
auto_close: true
timeout: 30
position: center  # center, top, bottom-right, bottom-left, top-right, top-left
theme: auto  # light, dark, auto
camera_entity: camera.doorbell
play_sound: true
sound_url: /local/sounds/doorbell.mp3
colors:
  answer: '#4caf50'
  decline: '#f44336'
  dtmf: '#2196f3'
custom_actions:
  - name: Открыть дверь
    icon: mdi:door-open
    service: switch.toggle
    service_data:
      entity_id: switch.door_lock
    dtmf_digit: '1'
  - name: Включить свет
    icon: mdi:lightbulb
    service: light.turn_on
    service_data:
      entity_id: light.entrance
```

---

## Кастомизация

### Темы

```yaml
# Тёмная тема
theme: dark

# Светлая тема
theme: light

# Автоматически (как в HA)
theme: auto
```

### Позиции окна

| Значение | Описание |
|----------|----------|
| `center` | По центру экрана |
| `top` | Сверху по центру |
| `bottom-right` | Нижний правый угол |
| `bottom-left` | Нижний левый угол |
| `top-right` | Верхний правый угол |
| `top-left` | Верхний левый угол |

### Кастомные кнопки

```yaml
custom_actions:
  - name: Открыть ворота
    icon: mdi:gate
    service: switch.turn_on
    service_data:
      entity_id: switch.gate
    dtmf_digit: '5'
    
  - name: Включить сирену
    icon: mdi:alarm-light
    service: siren.turn_on
    service_data:
      entity_id: siren.security
```

---

## Использование

### Автоматизации

```yaml
# Автоматическое открытие карточки при звонке
alias: "SIP: Показать карточку звонка"
trigger:
  - platform: event
    event_type: sip_doorbell_incoming_call
action:
  - service: browser_mod/popup
    data:
      title: "🔔 Входящий звонок"
      content: |
        Звонит: {{ trigger.event.data.caller_name }}
        Номер: {{ trigger.event.data.caller_number }}

# Уведомление на мобильное при звонке
alias: "SIP: Уведомление о звонке"
trigger:
  - platform: event
    event_type: sip_doorbell_incoming_call
action:
  - service: notify.mobile_app_iphone
    data:
      title: "🔔 Входящий звонок"
      message: "Звонит: {{ trigger.event.data.caller_name }}"
      data:
        actions:
          - action: "ANSWER"
            title: "Ответить"
          - action: "DECLINE"
            title: "Отклонить"

# Открытие двери при нажатии кнопки
alias: "SIP: Открыть дверь по DTMF"
trigger:
  - platform: event
    event_type: sip_doorbell_dtmf_received
    event_data:
      digit: "1"
action:
  - service: switch.turn_on
    target:
      entity_id: switch.door_lock
  - delay: "00:00:03"
  - service: switch.turn_off
    target:
      entity_id: switch.door_lock
```

### Скрипты

```yaml
# Исходящий звонок
sip_call_security:
  alias: "Позвонить в охрану"
  sequence:
    - service: sip_doorbell.call
      data:
        number: "102"

# Отправка DTMF
sip_open_gate:
  alias: "Открыть шлагбаум"
  sequence:
    - service: sip_doorbell.send_dtmf
      data:
        digits: "1234"
        duration: 300
```

---

## Диагностика

### Проверка логов

```bash
# Логи в Home Assistant
tail -f ~/.homeassistant/sip_logs/sip_doorbell.log

# Логи Asterisk
sudo tail -f /var/log/asterisk/full

# Статистика SIP
sudo asterisk -rx "pjsip show endpoints"
sudo asterisk -rx "core show channels"
```

### Распространённые проблемы

#### "Не зарегистрирован"

**Причины:**
- Неверные учётные данные
- Неправильный IP сервера
- Брандмауэр блокирует UDP 5060

**Решение:**
```bash
# Проверьте связь с сервером
nc -vz -u SIP_SERVER_IP 5060

# Проверьте регистрацию
sudo asterisk -rx "pjsip show endpoint ha_sip_user"
```

#### "Входящий звонок не открывает карточку"

**Причины:**
- Карточка не добавлена в Dashboard
- JavaScript не загружен

**Решение:**
1. Проверьте Developer Tools → Events → `sip_doorbell_incoming_call`
2. Проверьте Console браузера на ошибки JS

#### Нет звука

**Примечание:** Текущая версия работает как "сигнализатор" звонков. Для полноценной аудиосвязи требуется интеграция с медиашлюзом или IP-телефоном.

---

## Дополнительные возможности

### Интеграция с камерой

При настройке `camera_entity` в карточке будет показываться видео с камеры во время звонка.

### История звонков

Для просмотра истории добавьте:

```yaml
type: history-graph
entities:
  - sensor.sip_doorbell_state
hours_to_show: 24
```

### REST API

```bash
# Получить статус
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://HA_IP:8123/api/states/sensor.sip_doorbell_state

# Вызвать сервис (ответить)
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "switch.sip_doorbell_line"}' \
  http://HA_IP:8123/api/services/sip_doorbell/answer
```

---

## Поддержка

При возникновении проблем:

1. Проверьте логи: `~/.homeassistant/sip_logs/sip_doorbell.log`
2. Создайте issue на GitHub с логами
3. Используйте команду:

```bash
# Сбор диагностики
ha info > /config/sip_debug.txt
ha logs >> /config/sip_debug.txt
cat ~/.homeassistant/sip_logs/sip_doorbell.log >> /config/sip_debug.txt
```

---

## Лицензия

MIT License - см. LICENSE файл в репозитории.