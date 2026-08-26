# criptoproject — Bot autônomo de compra/venda de Bitcoin

Bot que monitora o preço do BTC em uma exchange e executa compras/vendas
automaticamente com base em uma estratégia técnica (cruzamento de médias
móveis + RSI), com stop-loss, take-profit e modo simulado (dry-run).

⚠️ **Trading automatizado envolve risco real de perda de capital.** Este
projeto é um ponto de partida técnico, não uma recomendação de investimento.
Comece sempre em modo `DRY_RUN=true` e/ou testnet.

## Como funciona a estratégia

- **Compra**: quando a média móvel curta cruza para cima da média longa
  (golden cross) e o RSI ainda não está sobrecomprado — indício de reversão
  de baixa para alta.
- **Venda**: quando a média curta cruza para baixo da longa (death cross),
  ou o RSI indica sobrecompra, ou o preço atinge o stop-loss / take-profit
  definidos.

Todos os parâmetros (períodos das médias, RSI, stop-loss, take-profit,
timeframe, valor por operação) são configuráveis via `.env`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edite o `.env`:

1. Crie uma API key na exchange escolhida (`EXCHANGE_ID`, padrão `binance`)
   com permissão **apenas de trade spot** — nunca habilite saque (withdrawal).
2. Cole `API_KEY` e `API_SECRET` no `.env` (nunca commite esse arquivo — já
   está no `.gitignore`).
3. Mantenha `USE_TESTNET=true` e `DRY_RUN=true` enquanto estiver validando.

## Validando antes de operar com dinheiro real

1. **Backtest** com dados históricos reais, sem precisar de API key:
   ```bash
   python backtest.py
   ```
2. **Testnet + dry-run**: rode o bot de verdade contra dados ao vivo, mas
   sem enviar ordens:
   ```bash
   python main.py
   ```
3. **Testnet + ordens reais (fake money)**: `DRY_RUN=false`, `USE_TESTNET=true`.
4. **Produção**: só depois de validar os passos acima, `USE_TESTNET=false`
   com uma API key de produção e um valor pequeno em `TRADE_AMOUNT_QUOTE`.

## Testes

```bash
pytest
```

## Notificações (opcional)

Preencha `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no `.env` para receber
alertas de compra/venda no Telegram. Deixe em branco para desativar.

## Estrutura

```
main.py             # ponto de entrada, roda o loop autônomo
backtest.py          # valida a estratégia com dados históricos
src/config.py         # carrega parâmetros do .env
src/exchange_client.py# wrapper sobre ccxt (dados de mercado + ordens)
src/strategy.py        # indicadores (SMA, RSI) e regra de sinal buy/sell/hold
src/trader.py           # loop principal: decide e executa
src/state.py             # persiste a posição aberta em state.json
src/notifier.py           # notificações via Telegram
tests/test_strategy.py     # testes da lógica de sinal
```

## Chaves de API necessárias

- **Obrigatória**: API key + secret da exchange (`EXCHANGE_ID` no `.env`).
  Compatível com qualquer exchange suportada pela lib
  [ccxt](https://github.com/ccxt/ccxt) (Binance, Kraken, Bitso, Coinbase
  Advanced Trade, etc.) — basta trocar `EXCHANGE_ID`.
- **Opcional**: token de bot do Telegram, para notificações.
