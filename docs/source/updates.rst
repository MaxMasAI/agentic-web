Software Updates & Releases
===========================

Keep your Agentic Web workspace up to date with the latest features, security patches, and model provider integrations.

Release Channels
----------------
- **Stable Channel**: Recommended for daily production workflows. Releases are thoroughly tested across Windows, macOS, and Linux.
- **Beta Channel**: Early access to new LLM models, visual agent builders, and experimental canvas tools.
- **Nightly Builds**: Cutting-edge developer builds with rapid bug fixes.

Checking for Updates
--------------------
You can verify and download updates automatically:
1. Navigate to **Settings > System & Updates**.
2. Click **Check for Updates**.
3. If an update is available, click **Download & Install**.

Updating via Command Line
-------------------------
On Linux / macOS:

.. code-block:: bash

   bash bin/clean.sh
   bash docs/update.sh

On Windows:

.. code-block:: bat

   bin\build_installer.bat
