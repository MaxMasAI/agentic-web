Quick Start & GitHub Setup Guide
================================

Get started with Agentic Web Workstation in minutes via GitHub:

1. Clone Repository
-------------------
.. code-block:: bash

   git clone https://github.com/MaxMasAI/agentic-web.git
   cd agentic-web

2. Create & Activate Python Virtual Environment (venv)
-------------------------------------------------------
Creating an isolated virtual environment is strongly recommended:

On Windows (PowerShell / CMD):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: powershell

   python -m venv .venv
   .venv\Scripts\activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt

On Linux & macOS (Bash / Zsh):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt

*(Tip: Windows users can simply double-click ``install.bat`` and Linux/macOS users can run ``./install.sh``).*

3. Launching the App
--------------------
* **Full Stack (Voice Daemon + GUI)**: ``run.bat`` (Windows)
* **Direct Desktop GUI**: ``python app.py``

4. First Sign-In & Setup
------------------------
Open **⚙️ Settings -> API Keys & Authentication** and click **🚀 Sign In via Browser** under OpenRouter to connect your models with 1 click.
