## Table of Contents

- [Description](#local_sofar_inverter)
- [Installation](#installation)
  - [Manual Installation](#manual-installation)
- [Configuration](#configuration)
   - [Entities returned](#entities-returned)
- [History](#history)

# local Sofar inverter

The `local_sofar_inverter` component is a Home Assistant integration that creates custom sensors for local monitoring your **Sofar inverter**.
It reads data from your inverter page, so you dont need to connect to any 'cloud'
When there is no sun, tthere is no PV energy so integration doesnt ask your inverter about it

Returns:
 - current power
 - today's energy
 - total energy
 - inverter errors 

My 1st HA component so be polite :)


## Installation

### MANUAL INSTALLATION

1. Download the
   [latest release](https://github.com/magumagus/local_sofar_inverter/releases/latest).
2. Unpack the release and copy the `custom_components/local_sofar_inverter` directory
   into the `custom_components` directory of your Home Assistant installation.
3. Restart Home Assistant.
4. Configure in the normal way by adding integration via HA website 


## Configuration

via HA webpage
- give ur inverter ID, username & password to login
- set how often ask ur inverter
- set minimal sun elevation when DONT ask inverter (he can be offline)

#### Entities returned

| Attribute                  | Description                              |
| :------------------------- | :--------------------------------------- |
| **name_**`now_p`           | Current PV power                         |
| **name_**`today_e`         | Energy produced today                    |
| **name_**`total_e`         | Total produced energy                    |
| **name_**`alarm`           | Errors returned by your inverter         |

#### Problems?
Try to turn on `debug` mode in your `configuration.yaml` and read/send your log file.

```yaml
logger:
  default: warning
  logs:
    custom_components.local_sofar_inverter: debug
```

## History
0.0.2  configuration via web, adding device  
0.0.1  first working version, working with one phase Sofar inverter (model `SA3ES233` software version V310)  