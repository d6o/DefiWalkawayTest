# Protocol logos (transparent PNG)

For the talk slides. Trademarks belong to their owners; used here only to identify the protocols tested.

- `final/`: transparent PNGs at their source resolution (200–512 px).
- `square-256/`: the same logos centered on a uniform 256×256 transparent canvas (for grids).
- `preview.png`: all 16 on a checkerboard and on a dark background.
- `raw/`, `trustwallet/`, `llamatoken/`: originals as downloaded.

| Protocol | File | Source | Processing |
|----------|------|--------|------------|
| Aave | aave.png | Trust Wallet assets (AAVE token) | none (round badge, transparent corners) |
| Compound | compound.png | Trust Wallet (COMP) | none |
| Curve | curve.png | Trust Wallet (CRV) | white background removed (edge flood fill) |
| Ethena | ethena.png | Trust Wallet (ENA) | none |
| ether.fi | etherfi.png | DefiLlama protocol icon | white background removed |
| Falcon Finance | falcon-finance.png | Trust Wallet (**USDf** token mark) | none |
| Fluid | fluid.png | Trust Wallet (FLUID) | white background removed |
| Kelp | kelp.png | DefiLlama token icon (**rsETH** mark; DefiLlama's Kelp protocol icon was a placeholder) | none |
| Lido | lido.png | Trust Wallet (LDO) | white background removed |
| Maple | maple.png | DefiLlama protocol icon | converted from WebP (already transparent) |
| Morpho | morpho.png | Trust Wallet (MORPHO) | none |
| Pendle | pendle.png | Trust Wallet (PENDLE) | none |
| Rocket Pool | rocket-pool.png | Trust Wallet (RPL) | none |
| Sky | sky.png | Trust Wallet (SKY) | none |
| Spark | spark.png | DefiLlama token icon (**SPK** mark) | converted from WebP |
| Uniswap | uniswap.png | Trust Wallet (UNI) | none |

Sources: `https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/ethereum/assets/<address>/logo.png`,
`https://icons.llamao.fi/icons/protocols/<slug>`, `https://token-icons.llamao.fi/icons/tokens/1/<address>`.
Background removal: `magick in.png -alpha set -bordercolor white -border 1 -fuzz 8% -fill none -draw "color 0,0 floodfill" -shave 1x1 out.png`
(only removes background connected to the edges).
