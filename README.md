# Fuck RKN

## Installation

1. **Clone the repo and submodules. The cd into the directory:**
   ```bash
   git clone https://github.com/paqx/fuck-rkn.git
   git submodule update --init --recursive --remote --no-fetch --depth=1
   cd fuck-rkn/
   ```

2. **Create and activate a Python virtual environment:**:
    ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Install browser engines for Playwright with dependencies:**
   ```sh
   playwright install-deps
   playwright install
   ```
