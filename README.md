## Table of Contents

- [Description](#local_sofar_inverter)
- [Installation](#installation)
  - [Manual Installation](#manual-installation)
- [Configuration](#configuration)
   - [Parameters](#parameters)
   - [configuration.yaml](#configuration.yaml)
   - [Entities returned](#entities-returned)
- [History](#history)

# local Sofar inverter

The `local_sofar_inverter` component is a Home Assistant integration that creates custom sensors for local monitoring your **Sofar inverter**.
It reads data from your inverter page, so you dont need to connect to any 'cloud'
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
3. Configure the `local_sofar_inverter` platform in your `configuration.yaml`.
4. Restart Home Assistant.


## Configuration

### Parameters

| Parameter           | Required | Description                                                                                                                                                                                                                                                                                                                                                                          |
| :------------------ | :------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `host`     		  | Yes      | IP of your inverter                                                                                                                                                                                                                                                                                                                                                                  |
| `name`              | No       | Entity's prefix  **Default**: `local_sofar_inverter`                                                                                                                                                                                                                                                                                                                                            |
| `username`          | No       | Username to log int  **Default**: `admin`                                                                                                                                                                                                                                                                                                                                            |
| `password`          | No       | Password to log int  **Default**: `admin`                                                                                                                                                                                                                                                                                                                                            |
| `scan_interval`     | No       | How often to read the inverte page **Default**: `5` min                                                                                                                                                                                                                                                                                                                   |
| `elevation`         | No       | When it is dark then inverter goes dark and its web goes offline, so it scans the page only when your sun is over your horizont **Default**: `5`                                                                                                                                                                                                                                                                                                                                            |

#### **`configuration.yaml`**

Minimal
```yaml
sensor:
  - platform: local_sofar_inverter
    host: 192.168.67.111
```

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
0.0.1  first working version, working with one phase Sofar inverter (model `SA3ES233` software version V310)