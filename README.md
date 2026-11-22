# HK–TH TradeEscrow

HK–TH TradeEscrow is a local demo of tokenised-deposit escrow for Hong Kong–Thailand trade. The Flask console uses synthetic trade, document and compliance data. It shows how shipment, document matching and compliance checks determine whether simulated funds are released or held.

## Run locally

Use Python 3.11 or later. From the project folder, run the commands for your operating system.

**macOS or Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m ui_flask.app
```

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ui_flask.app
```

Open [the TradeEscrow console](http://127.0.0.1:5050/) in your browser. Press Ctrl+C in the terminal to stop the server.

## Try the demo

In the player at the bottom of the console, choose the normal release, document mismatch or AML alert scenario and press Play. To jump to the end, choose a scenario under **Simulation controls**, select **Reset ledger with this scenario**, then select **Skip to end**. Use **Viewing as** to switch participant views.

The console is designed for one operator on localhost. The participant selector simulates a participant's role for the demo. All transactions and funds are simulated.
