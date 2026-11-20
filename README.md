# PC Control Hub

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-informational)
![RAM](https://img.shields.io/badge/RAM%20Usage-%3C%2040%20MB-success)
![License](https://img.shields.io/badge/License-MIT-green)

[English](#english) | [Русский](#русский)

---

## English

> **Note:** An AI assistant was used during the design and development of this project.

### Overview
**PC Control Hub** is a lightweight, self-hosted web dashboard built for centralized management of home PCs, workstations, and local servers. Designed as a low-overhead alternative to heavy monitoring suites, it consumes less than 40 MB of RAM and requires no external database.

The server operates as a unified entry point and smart network directory: instead of proxying heavy video streams through the host, it generates direct P2P connections for native clients (RDP, Moonlight) and automatically switches between local (LAN) and virtual (ZeroTier) addressing depending on how the dashboard is accessed.

### Features
* **Automatic Network Routing:** Detects whether the dashboard is opened via LAN or ZeroTier IP and adjusts target links dynamically.
* **Direct P2P Launchers:** Generates pre-configured `.rdp` files, provides a Moonlight connection guide with one-click IP copy, and offers quick access to Copyparty web file managers.
* **Smart Power Management:** Sends Wake-on-LAN magic packets (via `etherwake` / `wakeonlan`) to offline machines, dynamically hides the reboot button when a node is offline, and provides reboot/shutdown controls with confirmation modals for online nodes.
* **Web-Based Node Editor:** Add, edit, and remove devices directly from the UI with built-in validation warnings when optional parameters (MAC address or ZeroTier IP) are omitted.
* **Cross-Platform Monitoring Agent (`agent.py`):** Minimal background service for Windows and Linux reporting real-time CPU/RAM load, top memory-consuming process, and on-demand desktop screenshots.
* **Custom Theme Builder:** Includes built-in dark and light modes, plus up to 10 user-defined color palettes stored locally in the browser (`localStorage`).

### Repository Structure

| Path | Description |
| :--- | :--- |
| `app.py` | Main Flask web server, API endpoints, status poller, and dynamic PNG favicon generator. |
| `templates/index.html` | Single-file frontend UI with localization (EN/RU), modals, and custom theme engine. |
| `agent.py` | Lightweight telemetry and remote control agent deployed on target Windows/Linux nodes. |
| `install.sh` | Automated installation and `systemd` service setup script for Debian/Ubuntu servers. |

### Installation

#### 1. Hub Server Setup (Debian / Ubuntu)
1. Clone the repository and enter the project directory:
   ```bash
   git clone https://github.com/tema1d3492/pc-control-hub.git
   cd pc-control-hub
   ```
2. Make the installer executable and run it (installs `python3-flask`, `python3-psutil`, `wakeonlan`, `etherwake`, and configures a `systemd` unit on port `80`):
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
3. On first launch, `config.json` is generated automatically with a random `agent_token`. Open the dashboard in your browser via the server's IP address and add your devices using the **"+ Add PC"** button.

#### 2. Target Node Agent Setup (`agent.py`)
The agent is required on managed machines for hardware telemetry, desktop screenshots, and remote power actions.

1. Copy `agent.py` to the target machine and replace `TOKEN` with the `agent_token` value from your server's `config.json`.
2. Install the required dependencies:
   * **Windows:**
     ```cmd
     pip install flask psutil mss pillow
     ```
   * **Linux (Debian / Ubuntu):**
     ```bash
     sudo apt update && sudo apt install python3-flask python3-psutil scrot -y
     ```
3. Configure permissions and run `agent.py` in the background (listens on port `5050` by default):
   * **Windows:** Create a Task Scheduler task executing `pythonw.exe agent.py` at startup or logon with **"Run with highest privileges"** enabled. Ensure Wake-on-LAN is enabled in network adapter properties and Fast Startup is disabled (`powercfg /h off` or via Control Panel).
   * **Linux:** Configure a `systemd` service (set `Environment=DISPLAY=:0` for X11 screenshots), allow passwordless reboot/shutdown in `/etc/sudoers.d/`, and enable magic packet wake-up via `ethtool` / `nmcli`.

### Built With & Third-Party Tools
* [Flask](https://github.com/pallets/flask)
* [psutil](https://github.com/giampaolo/psutil)
* [python-mss](https://github.com/BoboTiG/python-mss)
* [Pillow (PIL)](https://github.com/python-pillow/Pillow)
* [scrot](https://github.com/resurrecting-open-source-projects/scrot)
* [Moonlight Game Streaming](https://github.com/moonlight-stream)
* [Copyparty](https://github.com/9001/copyparty)
* [ZeroTier](https://github.com/zerotier/ZeroTierOne)

### License
Distributed under the **MIT License**. See `LICENSE` for more information.

---

## Русский

> **Примечание:** В процессе проектирования и разработки данного проекта использовалась нейросеть.

### Обзор проекта
**PC Control Hub** — это легковесный веб-интерфейс для централизованного управления парком домашних ПК, рабочих станций и локальных серверов. Проект разработан как нетребовательная к ресурсам альтернатива тяжелым системам мониторинга (потребляет менее 40 МБ ОЗУ и не требует установки СУБД).

Сервер выступает в роли единой точки входа и сетевого справочника: он не проксирует тяжелый трафик через себя, а инициирует прямые P2P-подключения для локальных клиентов (RDP, Moonlight) и автоматически переключает адресацию между локальной сетью (LAN) и виртуальным туннелем (ZeroTier) в зависимости от того, по какому IP открыт интерфейс.

### Основной функционал
* **Автоопределение сети:** автоматический выбор маршрутизации (LAN или ZeroTier) на основе IP-адреса, по которому пользователь обратился к веб-хабу.
* **Прямой запуск P2P-клиентов:** генерация готовых `.rdp`-файлов, окно подключения Moonlight с копированием IP в один клик и переход в веб-менеджер файлов Copyparty.
* **Умное управление питанием:** отправка пакетов Wake-on-LAN (через `etherwake` / `wakeonlan`) для выключенных машин, автоматическое скрытие кнопки перезагрузки у офлайн-узлов, а также перезагрузка и выключение с окном подтверждения для активных ПК.
* **Редактор узлов в браузере:** добавление, редактирование и удаление карточек ПК через веб-интерфейс с автоматическим предупреждением об ограничениях при отсутствии MAC-адреса или ZeroTier IP.
* **Кроссплатформенный агент (`agent.py`):** фоновый сервис для Windows и Linux, отдающий загрузку CPU/RAM, самый ресурсоемкий процесс и скриншот рабочего стола по запросу.
* **Конструктор тем:** встроенные темная и светлая палитры, а также создание и хранение до 10 пользовательских цветовых схем в `localStorage` браузера.

### Структура репозитория

| Путь | Назначение |
| :--- | :--- |
| `app.py` | Основной веб-сервер на Flask, API-маршруты, опрос статусов и генератор PNG-иконки. |
| `templates/index.html` | Единый шаблон интерфейса с локализацией (EN/RU), модальными окнами и движком тем. |
| `agent.py` | Легковесный агент телеметрии и управления для установки на управляемые ПК (Windows/Linux). |
| `install.sh` | Скрипт автоматической установки зависимостей и настройки службы `systemd` для Debian/Ubuntu. |

### Установка

#### 1. Настройка управляющего сервера (Debian / Ubuntu)
1. Клонируйте репозиторий и перейдите в каталог проекта:
   ```bash
   git clone https://github.com/tema1d3492/pc-control-hub.git
   cd pc-control-hub
   ```
2. Сделайте скрипт установки исполняемым и запустите его (установит `python3-flask`, `python3-psutil`, `wakeonlan`, `etherwake` и запустит службу `systemd` на порту `80`):
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
3. При первом запуске автоматически создастся файл `config.json` со сгенерированным ключом `agent_token`. Откройте веб-интерфейс по IP-адресу сервера и добавьте ваши машины через кнопку **«+ Добавить ПК»**.

#### 2. Настройка агента на управляемых ПК (`agent.py`)
Агент необходим на целевых компьютерах для сбора телеметрии, захвата скриншотов экрана и удаленного управления питанием.

1. Скопируйте `agent.py` на управляемый ПК и впишите в переменную `TOKEN` значение `agent_token` из `config.json` сервера.
2. Установите зависимости в соответствии с ОС:
   * **Windows:**
     ```cmd
     pip install flask psutil mss pillow
     ```
   * **Linux (Debian / Ubuntu):**
     ```bash
     sudo apt update && sudo apt install python3-flask python3-psutil scrot -y
     ```
3. Настройте права и запустите `agent.py` в фоновом режиме (по умолчанию используется порт `5050`):
   * **Windows:** создайте задачу в Планировщике заданий (Task Scheduler) с запуском `pythonw.exe agent.py` при старте системы или входе пользователя с галочкой **«Выполнять с наивысшими правами»**. Включите пробуждение по магическому пакету в свойствах сетевого адаптера и отключите «Быстрый запуск» (Fast Startup).
   * **Linux:** настройте фоновую службу `systemd` (для захвата экрана в X11 укажите `Environment=DISPLAY=:0`), разрешите `reboot`/`poweroff` без пароля в `/etc/sudoers.d/` и активируйте режим `Wake-on: g` через `nmcli` или `ethtool`.

### Используемые библиотеки и инструменты
* [Flask](https://github.com/pallets/flask)
* [psutil](https://github.com/giampaolo/psutil)
* [python-mss](https://github.com/BoboTiG/python-mss)
* [Pillow (PIL)](https://github.com/python-pillow/Pillow)
* [scrot](https://github.com/resurrecting-open-source-projects/scrot)
* [Moonlight Game Streaming](https://github.com/moonlight-stream)
* [Copyparty](https://github.com/9001/copyparty)
* [ZeroTier](https://github.com/zerotier/ZeroTierOne)
