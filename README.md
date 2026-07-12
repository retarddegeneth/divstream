# div-router

Robinhood Chain dividend streaming protocol. never been done before.

## network
robinhood_chain // chain_id: 4663

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
reinvest — buy more token via uniswap v3
hedge — partial conversion to stablecoin

## contract
contracts/DividendVault.sol — erc4626-style shares + dividend routing

## payout policy
manual daily for top vaults. admin books payouts JSON or onchain tx hash.

## color
Robin Neon #CCFF00 on black. exact robinhood chain brand.
