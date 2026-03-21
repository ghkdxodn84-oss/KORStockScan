import os
import numpy as np
import pandas as pd
from sqlalchemy import text

from ml_v2_common import engine, AI_PICKS_PATH, AI_PRED_PATH, zfill_code

INITIAL_CAPITAL = 10_000_000
MAX_POSITIONS = 5
FEE_RATE = 0.0023

# regime별 익절/손절
TP_BULL = 0.045
SL_BULL = 0.030
TP_BEAR = 0.035
SL_BEAR = 0.025

def load_signals(use_picks=True):
    path = AI_PICKS_PATH if use_picks and os.path.exists(AI_PICKS_PATH) else AI_PRED_PATH
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Date']).dt.normalize()
    df['Code'] = zfill_code(df['Code'])
    return df

def load_prices_for_signals(signals: pd.DataFrame) -> pd.DataFrame:
    min_date = signals['Date'].min().strftime('%Y-%m-%d')
    max_date = (signals['Date'].max() + pd.Timedelta(days=10)).strftime('%Y-%m-%d')
    codes = tuple(signals['Code'].unique())

    if len(codes) == 1:
        code_str = f"('{codes[0]}')"
    else:
        code_str = str(codes)

    query = f"""
        SELECT quote_date, stock_code, open_price, high_price, low_price, close_price
        FROM daily_stock_quotes
        WHERE quote_date >= '{min_date}'
          AND quote_date <= '{max_date}'
          AND stock_code IN {code_str}
        ORDER BY quote_date ASC, stock_code ASC
    """
    with engine.connect() as conn:
        px = pd.read_sql(text(query), conn)

    px['quote_date'] = pd.to_datetime(px['quote_date']).dt.normalize()
    px['stock_code'] = zfill_code(px['stock_code'])
    return px

def resolve_exit(open_p, high_p, low_p, close_p, tp_price, sl_price, hold_day, max_hold=3):
    # 갭 우선
    if open_p >= tp_price:
        return open_p, 'TP_GAP'
    if open_p <= sl_price:
        return open_p, 'SL_GAP'

    hit_tp = high_p >= tp_price
    hit_sl = low_p <= sl_price

    # 같은 날 둘 다 맞으면 보수적으로 SL 처리
    if hit_tp and hit_sl:
        return sl_price, 'AMBIG_SL_FIRST'
    if hit_tp:
        return tp_price, 'TP'
    if hit_sl:
        return sl_price, 'SL'
    if hold_day >= max_hold:
        return close_p, 'TIME'
    return None, None

def run_backtest():
    signals = load_signals(use_picks=True)
    if signals.empty:
        print("❌ 시그널 파일이 비어 있습니다.")
        return

    prices = load_prices_for_signals(signals)
    if prices.empty:
        print("❌ 가격 데이터가 없습니다.")
        return

    all_dates = sorted(prices['quote_date'].unique())
    signal_map = signals.groupby('Date')

    cash = INITIAL_CAPITAL
    portfolio = {}
    trade_log = []

    for i in range(1, len(all_dates)):
        today = all_dates[i]
        yesterday = all_dates[i - 1]

        today_px = prices[prices['quote_date'] == today].set_index('stock_code')
        yday_signal = signal_map.get_group(yesterday) if yesterday in signal_map.groups else pd.DataFrame()

        # --------------------------------------------------
        # 1) 기존 포지션 매도
        # --------------------------------------------------
        to_remove = []
        for code, pos in portfolio.items():
            if code not in today_px.index:
                continue

            row = today_px.loc[code]
            pos['days'] += 1

            tp = pos['buy_price'] * (1.0 + pos['tp'])
            sl = pos['buy_price'] * (1.0 - pos['sl'])

            exit_price, reason = resolve_exit(
                open_p=row['open_price'],
                high_p=row['high_price'],
                low_p=row['low_price'],
                close_p=row['close_price'],
                tp_price=tp,
                sl_price=sl,
                hold_day=pos['days'],
                max_hold=3
            )

            if exit_price is not None:
                gross = exit_price * pos['qty']
                sell_fee = gross * FEE_RATE
                cash += (gross - sell_fee)

                cost = pos['buy_price'] * pos['qty']
                cost_with_buy_fee = cost * (1.0 + FEE_RATE)
                pnl = (gross - sell_fee) - cost_with_buy_fee
                ret = pnl / cost_with_buy_fee

                trade_log.append({
                    'Signal_Date': pos['signal_date'],
                    'Buy_Date': pos['buy_date'],
                    'Sell_Date': today,
                    'Code': code,
                    'Bull_Regime': pos['bull_regime'],
                    'Meta_Score': pos['score'],
                    'Buy_Price': pos['buy_price'],
                    'Sell_Price': exit_price,
                    'Qty': pos['qty'],
                    'Days': pos['days'],
                    'Reason': reason,
                    'Return': ret
                })
                to_remove.append(code)

        for code in to_remove:
            del portfolio[code]

        # --------------------------------------------------
        # 2) 신규 진입 (어제 시그널 -> 오늘 시가)
        # --------------------------------------------------
        available_slots = MAX_POSITIONS - len(portfolio)
        if available_slots > 0 and not yday_signal.empty:
            yday_signal = yday_signal.sort_values('Meta_Score', ascending=False)

            for _, sig in yday_signal.head(available_slots).iterrows():
                code = sig['Code']
                if code in portfolio:
                    continue
                if code not in today_px.index:
                    continue

                buy_price = today_px.loc[code, 'open_price']
                if buy_price <= 0:
                    continue

                bull_regime = int(sig['Bull_Regime']) if 'Bull_Regime' in sig else 0
                tp = TP_BULL if bull_regime == 1 else TP_BEAR
                sl = SL_BULL if bull_regime == 1 else SL_BEAR

                total_asset = cash + sum(
                    (today_px.loc[c, 'close_price'] * p['qty']) if c in today_px.index else (p['buy_price'] * p['qty'])
                    for c, p in portfolio.items()
                )
                invest_amount = total_asset / MAX_POSITIONS

                qty = int(invest_amount // buy_price)
                if qty <= 0:
                    continue

                gross_cost = buy_price * qty
                buy_fee = gross_cost * FEE_RATE
                total_cost = gross_cost + buy_fee

                if cash >= total_cost:
                    cash -= total_cost
                    portfolio[code] = {
                        'signal_date': sig['Date'],
                        'buy_date': today,
                        'buy_price': buy_price,
                        'qty': qty,
                        'days': 0,
                        'tp': tp,
                        'sl': sl,
                        'bull_regime': bull_regime,
                        'score': sig['Meta_Score']
                    }

        # 루프 계속

    # ------------------------------------------------------
    # 3) 잔존 포지션 mark-to-market
    # ------------------------------------------------------
    last_date = all_dates[-1]
    last_px = prices[prices['quote_date'] == last_date].set_index('stock_code')

    final_stock_value = 0.0
    for code, pos in portfolio.items():
        if code in last_px.index:
            final_stock_value += last_px.loc[code, 'close_price'] * pos['qty']
        else:
            final_stock_value += pos['buy_price'] * pos['qty']

    final_total_asset = cash + final_stock_value
    roi = (final_total_asset / INITIAL_CAPITAL) - 1.0

    log_df = pd.DataFrame(trade_log)
    if log_df.empty:
        print("⚠️ 체결된 거래가 없습니다.")
        print(f"최종 자산: {final_total_asset:,.0f}원 | ROI: {roi:.2%}")
        return

    win_rate = (log_df['Return'] > 0).mean()
    avg_ret = log_df['Return'].mean()
    cum_ret = (1.0 + log_df['Return']).prod() - 1.0

    print("\n" + "=" * 60)
    print("📊 [Backtest V2 결과]")
    print("=" * 60)
    print(f"거래 수        : {len(log_df):,}")
    print(f"승률           : {win_rate:.2%}")
    print(f"평균 수익률     : {avg_ret:.2%}")
    print(f"복리 누적수익률 : {cum_ret:.2%}")
    print(f"최종 자산       : {final_total_asset:,.0f}원")
    print(f"자본 수익률 ROI : {roi:.2%}")
    print("-" * 60)
    print("[매도 사유]")
    print(log_df['Reason'].value_counts())
    print("=" * 60)

    save_path = os.path.join(os.path.dirname(AI_PICKS_PATH), 'backtest_trades_v2.csv')
    log_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"✅ 거래 로그 저장: {save_path}")

if __name__ == "__main__":
    run_backtest()