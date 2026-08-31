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

## Paper trading (bot de compra/segura/vende com lucro mínimo)

`paper_main.py` é um segundo bot, independente do `main.py`, que **nunca
envia ordens reais** — usa preço real de mercado mas simula saldo, compra,
posição e venda em memória/disco (`paper_state.json`).

Regras:

- Usa o mesmo sinal de compra do bot principal (golden cross + RSI via
  `src/strategy.py`).
- Depois de comprado, só vende quando o **lucro líquido** (já descontando
  taxa de compra e de venda) atingir `MIN_PROFIT_PERCENT`. Nunca vende no
  prejuízo, não tem stop-loss, não faz martingale, não abre uma segunda
  posição enquanto a primeira estiver aberta.
- Enquanto o preço cai ou fica abaixo do mínimo necessário, mantém a posição
  aberta — por horas ou dias, sem limite de tempo.

Configuração no `.env`:

```bash
PAPER_TRADING=true
INITIAL_CAPITAL=3000
TRADE_PERCENT=30
MIN_PROFIT_PERCENT=0.5
BUY_FEE_PERCENT=0.1
SELL_FEE_PERCENT=0.1
```

Rodar:

```bash
python paper_main.py
```

`PAPER_TRADING=false` faz `paper_main.py` recusar iniciar — é só uma trava
de segurança extra, já que este bot nunca chama `create_market_buy`/`sell`
da exchange, mesmo com a flag em `true`.

### Acompanhar resultados

```bash
python paper_report.py
```

Mostra, sem enviar nenhuma ordem: preço atual, saldo, posição aberta (se
houver) com preço mínimo de venda e lucro não realizado, patrimônio total,
lucro realizado acumulado e taxa de acerto dos trades já fechados.

## Notificações (opcional)

Preencha `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no `.env` para receber
alertas de compra/venda no Telegram. Deixe em branco para desativar.

## Estrutura

```
main.py                  # ponto de entrada do bot ao vivo (SMA/RSI, stop-loss/take-profit)
paper_main.py             # ponto de entrada do bot de paper trading (nunca envia ordens reais)
backtest.py                # valida a estratégia com dados históricos
src/config.py                # carrega parâmetros do .env
src/exchange_client.py         # wrapper sobre ccxt (dados de mercado + ordens)
src/strategy.py                # indicadores (SMA, RSI) e regra de sinal buy/sell/hold
src/trader.py                  # loop do bot ao vivo: decide e executa
src/state.py                   # persiste a posição do bot ao vivo em state.json
src/paper_broker.py            # matemática pura de compra/venda/taxas/lucro mínimo (paper trading)
src/paper_state.py             # persiste conta/posição do paper trading em paper_state.json
src/paper_trader.py            # loop do paper trading: decide e simula execução
src/paper_report.py            # calcula o resumo (equity, pnl, taxa de acerto) para o relatório
paper_report.py                 # imprime o resumo do paper trading no console
src/notifier.py                # notificações via Telegram
tests/test_strategy.py         # testes da lógica de sinal
tests/test_paper_broker.py     # testes de compra/taxas/lucro mínimo/venda do paper trading
tests/test_paper_report.py     # testes do resumo (equity, pnl, taxa de acerto)
```

## Chaves de API necessárias

- **Obrigatória**: API key + secret da exchange (`EXCHANGE_ID` no `.env`).
  Compatível com qualquer exchange suportada pela lib
  [ccxt](https://github.com/ccxt/ccxt) (Binance, Kraken, Bitso, Coinbase
  Advanced Trade, etc.) — basta trocar `EXCHANGE_ID`.
- **Opcional**: token de bot do Telegram, para notificações.
