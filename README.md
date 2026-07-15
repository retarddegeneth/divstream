# DivStream

Real-World Asset dividend streaming on Robinhood Chain.

## network
robinhood_chain // chain_id: 4663

## links
https://divstream-production.up.railway.app/
https://x.com/divstreamrh

## mode
headless API + terminal UI on flask :8080

## run
```bash
pip install -r requirements.txt
python app.py
```

## endpoints
- POST `/` — create vault (symbol, token_address, mode, shares)
- POST `/events` — book dividend event
- POST `/payouts` — mark payout sent manually
- `/vaults` — vaults JSON
- `/events` — events JSON
- `/payouts` — payouts JSON

## modes
cash — stablecoin to wallet
reinvest — accumulate positions
hedge — partial conversion to stablecoin

## payout policy
manual daily for top vaults. admin books payouts JSON or onchain tx hash.

## color
Robin Neon #CCFF00 on black. exact robinhood chain brand.
