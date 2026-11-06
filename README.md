# kwtSMS for Home Assistant

Send SMS from Home Assistant automations through [kwtSMS](https://www.kwtsms.com), the SMS gateway for Kuwait and
the Gulf: alarm, water leak, door left open, power cut.

## Features

- Set up from the UI: API login, phone numbers, Sender ID, test mode.
- One notify entity per phone number, used with the standard `notify.send_message` action.
- Message titles are sent as the first line.
- English and Arabic. Test mode: queued on kwtSMS, never delivered; their credits are held until you delete them from the Sending Queue in your kwtSMS account.
- Failed sends show the kwtSMS error (for example `ERR010` zero balance) in the automation trace.

## Requirements

- Home Assistant 2024.6 or later.
- A kwtSMS account with API access. [Sign up free](https://www.kwtsms.com/signup/).

## Installation

**HACS:** add `https://github.com/kwtsms/kwtsms-homeassistant` as a custom repository (type Integration), install
**kwtSMS**, and restart Home Assistant.

**Manual:** copy `custom_components/kwtsms` into your `config/custom_components/` folder and restart.

## Setup

1. **Settings > Devices & services > Add integration > kwtSMS.**
2. Enter the API username and password of your kwtSMS account (not your mobile number) and the phone numbers in
   international format, separated by commas, for example `965XXXXXXXX`.
3. Each number becomes an entity such as `notify.sms_965xxxxxxxx`. Change numbers, Sender ID or
   test mode later under **Configure**.

## Use in an automation

```yaml
action: notify.send_message
target:
  entity_id: notify.sms_965xxxxxxxx
data:
  title: Water leak
  message: Kitchen sensor is wet.
```

## Arabic

Arabic messages are sent as Unicode: one SMS page holds 70 Arabic characters, against 160 English ones. Keep
messages short to save credits.

## Support

Help: https://www.kwtsms.com/support.html | FAQ: https://www.kwtsms.com/faq/ | support@kwtsms.com

## Security

See [SECURITY.md](SECURITY.md).

## License

MIT, (c) kwtSMS
