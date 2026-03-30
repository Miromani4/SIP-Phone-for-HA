/**
 * SIP Doorbell Call Popup
 * 
 * Автоматически открывает карточку звонка при входящем вызове.
 * Установите как "Dashboard Card" или добавьте в resources.
 */

class SIPDoorbellCallPopup extends HTMLElement {
    constructor() {
        super();
        this._hass = null;
        this._config = null;
        this._activeCall = null;
        this._dialog = null;
    }

    setConfig(config) {
        this._config = {
            title: '🔔 Входящий звонок',
            auto_open: true,
            auto_close: true,
            timeout: 30,
            ...config
        };
    }

    set hass(hass) {
        this._hass = hass;
        
        // Подписка на события SIP Doorbell
        if (!this._subscription) {
            this._subscribeToCalls();
        }
    }

    async _subscribeToCalls() {
        try {
            this._subscription = await this._hass.connection.subscribeMessage(
                (message) => this._handleCallEvent(message),
                {
                    type: 'sip_doorbell/subscribe_calls',
                }
            );
        } catch (err) {
            console.error('Failed to subscribe to SIP calls:', err);
        }
    }

    _handleCallEvent(message) {
        const event = message.event;
        
        if (event.event_type === 'sip_doorbell_incoming_call') {
            this._showCallPopup(event.data);
        } else if (event.event_type === 'sip_doorbell_call_ended') {
            this._closeCallPopup();
        }
    }

    _showCallPopup(data) {
        if (this._dialog) {
            this._dialog.close();
        }

        const callerName = data.caller_name || 'Неизвестно';
        const callerNumber = data.caller_number || 'Неизвестно';
        const extension = data.extension || '';

        // Создаём диалог
        this._dialog = document.createElement('ha-dialog');
        this._dialog.heading = this._config.title;
        this._dialog scrimClickAction = 'close';
        this._dialog escapeKeyAction = 'close';

        const content = document.createElement('div');
        content.className = 'sip-call-popup';
        content.innerHTML = `
            <div class="caller-info">
                <ha-icon icon="mdi:phone-incoming" class="call-icon"></ha-icon>
                <div class="caller-details">
                    <div class="caller-name">${callerName}</div>
                    <div class="caller-number">${callerNumber}</div>
                    <div class="caller-extension">Extension: ${extension}</div>
                </div>
            </div>
            
            <div class="call-actions">
                <mwc-button 
                    raised 
                    class="answer-btn"
                    icon="mdi:phone"
                >
                    Ответить
                </mwc-button>
                <mwc-button 
                    outlined 
                    class="decline-btn"
                    icon="mdi:phone-hangup"
                >
                    Отклонить
                </mwc-button>
            </div>
            
            <div class="dtmf-panel" style="display: none;">
                <p>Отправить DTMF:</p>
                <div class="dtmf-buttons">
                    <mwc-button data-digit="1">1</mwc-button>
                    <mwc-button data-digit="2">2</mwc-button>
                    <mwc-button data-digit="3">3</mwc-button>
                    <mwc-button data-digit="4">4</mwc-button>
                    <mwc-button data-digit="5">5</mwc-button>
                    <mwc-button data-digit="6">6</mwc-button>
                    <mwc-button data-digit="7">7</mwc-button>
                    <mwc-button data-digit="8">8</mwc-button>
                    <mwc-button data-digit="9">9</mwc-button>
                    <mwc-button data-digit="*">*</mwc-button>
                    <mwc-button data-digit="0">0</mwc-button>
                    <mwc-button data-digit="#">#</mwc-button>
                </div>
            </div>
        `;

        this._dialog.appendChild(content);
        document.body.appendChild(this._dialog);

        // Обработчики кнопок
        const answerBtn = content.querySelector('.answer-btn');
        const declineBtn = content.querySelector('.decline-btn');
        const dtmfButtons = content.querySelectorAll('.dtmf-buttons mwc-button');

        answerBtn.addEventListener('click', () => {
            this._hass.callService('sip_doorbell', 'answer');
            content.querySelector('.dtmf-panel').style.display = 'block';
        });

        declineBtn.addEventListener('click', () => {
            this._hass.callService('sip_doorbell', 'hangup');
            this._closeCallPopup();
        });

        dtmfButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const digit = e.target.getAttribute('data-digit');
                this._hass.callService('sip_doorbell', 'send_dtmf', {
                    digits: digit,
                    duration: 250
                });
            });
        });

        this._dialog.show();
        this._activeCall = data;

        // Автозакрытие через timeout
        if (this._config.auto_close && this._config.timeout > 0) {
            this._closeTimeout = setTimeout(() => {
                this._closeCallPopup();
            }, this._config.timeout * 1000);
        }
    }

    _closeCallPopup() {
        if (this._dialog) {
            this._dialog.close();
            this._dialog.remove();
            this._dialog = null;
        }
        
        if (this._closeTimeout) {
            clearTimeout(this._closeTimeout);
            this._closeTimeout = null;
        }
        
        this._activeCall = null;
    }

    getCardSize() {
        return 1;
    }
}

customElements.define('sip-doorbell-call-popup', SIPDoorbellCallPopup);

console.info('%c SIP Doorbell Call Popup %c Loaded ', 'background: #03a9f4; color: white; border-radius: 3px; padding: 2px;', 'background: #4caf50; color: white; border-radius: 3px; padding: 2px;');
