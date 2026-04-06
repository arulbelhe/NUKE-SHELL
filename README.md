# Occam Logistics Bot (Windows 10)

A lightweight **paper-trading GUI bot** for prediction-market style workflows:

- Signal ingestion (mock stream included)
- EV filter
- Scaled Kelly sizing
- Risk caps
- Decision logging

> ⚠️ This project is for research/education and paper trading first. No profit guarantee.

## Quick start (Windows 10)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=src
python -m occam_bot.gui
```

## Strategy flow implemented

1. Scan signal feed
2. Estimate probability (`model_probability`)
3. Compute EV and Kelly fraction
4. Apply risk limits (`max_position_pct`, `min_liquidity`, `min_ev`)
5. Emit trade decision

## Next integrations

- Replace mock signal feed with real OSINT + model outputs.
- Add `polyterm` wallet mirror ingestion.
- Add `py-clob-client` execution adapter with explicit LIVE toggle.
