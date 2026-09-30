"""Pinned, byte-verified MetaTrader source. No compilation or trading execution."""
from pathlib import Path
import json, hashlib
BASE=Path(__file__).resolve().parent
OUT=BASE/'trading'
DATA=[x for x in json.loads((BASE/'bundled_catalog.json').read_text()) if x['id'] != 'earnforex-spike-trader']

def blob(b):
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def save_original(name,sha,text):
    # Match the original byte encoding and newline form, never alter source logic.
    for nl in ('\r\n','\n'):
        normalized=text.replace('\r\n','\n').replace('\n',nl)
        for enc in ('utf-8','cp1252','utf-16'):
            b=normalized.encode(enc)
            if blob(b)==sha:
                p=OUT/'sources'/'earnforex-spike-trader'/name
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(b)
                return {'path':name,'local_source':p.relative_to(OUT).as_posix(),'blob_sha1':sha,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'encoding':enc}
    raise ValueError('Source bytes do not match pinned Git blob: '+name)

FILES=[]
FILES.append(save_original('SpikeTrader.mq4','c34bf926f03e9efa3682d7eb9c0da42ba3fcace3','''//+------------------------------------------------------------------+
//|                                                  SpikeTrader.mq4 |
//|                             Copyright © 2012-2022, EarnForex.com |
//|                                       https://www.earnforex.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright © 2012-2022, EarnForex"
#property link      "https://www.earnforex.com/metatrader-expert-advisors/Spike-Trader/"
#property version   "1.01"
#property strict

#property description "Trades on spikes that are:"
#property description "1) Higher/lower than N preceding bars;"
#property description "2) Higher/lower than the previous bar by X percent;"
#property description "3) Close in bottom or upper third/half of the bar."

input group "Main"
input int Hold = 11; // Hold: Position holding time in bars.
input int BarsNumber = 3; // BarsNumber: N preceding bars to check.
input double PercentageDifference = 0.003; // PercentageDifference1: X percentage for bar comparison.
input double ThirdOrHalf = 0.5; // ThirdOrHalf: Top/bottom share of a bar to close in.
input group "Money management"
input double Lots = 0.1;
input group "Miscellaneous"
input int Slippage = 30;
input string OrderCommentary = "Spike Trader";
input int Magic = 173923183;

int LastBars = 0;
int Timer = 0;

void OnTick()
{
    if ((!IsTradeAllowed()) || (IsTradeContextBusy()) || (!IsConnected()) || ((!MarketInfo(Symbol(), MODE_TRADEALLOWED)) && (!IsTesting()))) return;

    //Wait for the new Bar in a chart.
    if (LastBars == Bars) return;
    else LastBars = Bars;

    if (Timer == 1) ClosePrev();
    if (Timer > 0) Timer--;

    CheckEntry();
}

//+------------------------------------------------------------------+
//| Check for entry conditions and trade if necessary.               |
//+------------------------------------------------------------------+
void CheckEntry()
{
    // Empty bar.
    if (High[1] - Low[1] == 0) return;
    
    if (CheckSellEntry())
    {
        // If found a BUY order, close it and open a SELL. Otherwise, only reset timer.
        if (ClosePrev(OP_SELL)) fSell();
        Timer = Hold;
    }
    else if (CheckBuyEntry())
    {
        // If found a SELL order, close it and open a BUY. Otherwise, only reset timer.
        if (ClosePrev(OP_BUY)) fBuy();
        Timer = Hold;
    }
}

bool CheckSellEntry()
{
    // If the bar isn't higher than at least one of the previous bars - return false.
    for (int i = 2; i < BarsNumber + 2; i++)
        if (High[1] <= High[i]) return false;

    // If not higher than the previous bar by required percentage difference - return false.
    if ((High[1] - High[2]) / High[2] < PercentageDifference) return false;
    
    // If closed above the lower third/half - return false.
    if ((Close[1] - Low[1]) / (High[1] - Low[1]) > ThirdOrHalf) return false;

    // Passed all tests.
    return true;
}

bool CheckBuyEntry()
{
    // If the bar isn't lower than at least one of the previous bars - return false.
    for (int i = 2; i < BarsNumber + 2; i++)
        if (Low[1] >= Low[i]) return false;

    // If not lower than the previous bar by required percentage difference - return false.
    if ((Low[2] - Low[1]) / Low[2] < PercentageDifference) return false;
    
    // If closed below the upper third/half - return false.
    if ((High[1] - Close[1]) / (High[1] - Low[1]) > ThirdOrHalf) return false;

    // Passed all tests.
    return true;
}

//+------------------------------------------------------------------+
//| Close previous position.                                         |
//| order_type - skip positions of this directions.                  |
//+------------------------------------------------------------------+
bool ClosePrev(int order_type = -1)
{
    int total = OrdersTotal();
    for (int i = total - 1; i >= 0; i--)
    {
        if (OrderSelect(i, SELECT_BY_POS) == false) continue;
        if ((OrderSymbol() == Symbol()) && (OrderMagicNumber() == Magic))
        {
            if (OrderType() == OP_BUY)
            {
                if (order_type == OP_BUY) return false;
                RefreshRates();
                if (!OrderClose(OrderTicket(), OrderLots(), Bid, Slippage))
                {
                    int e = GetLastError();
                    Print("OrderClose Error: ", e);
                }
                return true;
            }
            else if (OrderType() == OP_SELL)
            {
                if (order_type == OP_SELL) return false;
                RefreshRates();
                if (!OrderClose(OrderTicket(), OrderLots(), Ask, Slippage))
                {
                    int e = GetLastError();
                    Print("OrderClose Error: ", e);
                }
                return true;
            }
        }
    }
    return true;
}

//+------------------------------------------------------------------+
//| Sell                                                             |
//+------------------------------------------------------------------+
int fSell()
{
    RefreshRates();
    int result = OrderSend(Symbol(), OP_SELL, Lots, Bid, Slippage, 0, 0, OrderCommentary, Magic);
    if (result == -1)
    {
        int e = GetLastError();
        Print("OrderSend Error: ", e);
    }
    else return result;
    return 0;
}

//+------------------------------------------------------------------+
//| Buy                                                              |
//+------------------------------------------------------------------+
int fBuy()
{
    RefreshRates();
    int result = OrderSend(Symbol(), OP_BUY, Lots, Ask, Slippage, 0, 0, OrderCommentary, Magic);
    if (result == -1)
    {
        int e = GetLastError();
        Print("OrderSend Error: ", e);
    }
    else return result;
    return 0;
}
//+------------------------------------------------------------------+'''))
FILES.append(save_original('SpikeTrader.mq5','f67c52875cf3ca804fc97b225fe370a2af651e1e','''//+------------------------------------------------------------------+
//|                                                  SpikeTrader.mq5 |
//|                             Copyright © 2012-2022, EarnForex.com |
//|                                       https://www.earnforex.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright © 2012-2022, EarnForex"
#property link      "https://www.earnforex.com/metatrader-expert-advisors/Spike-Trader/"
#property version   "1.01"

#property description "Trades on spikes that are:"
#property description "1) Higher/lower than N preceding bars;"
#property description "2) Higher/lower than the previous bar by X percent;"
#property description "3) Close in bottom or upper third/half of the bar."

#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>

input group "Main"
input int Hold = 11; // Hold: Position holding time in bars.
input int BarsNumber = 3; // BarsNumber: N preceding bars to check.
input double PercentageDifference = 0.003; // PercentageDifference1: X percentage for bar comparison.
input double ThirdOrHalf = 0.5; // ThirdOrHalf: Top/bottom share of a bar to close in.
input group "Money management"
input double Lots = 0.1;
input group "Miscellaneous"
input int Slippage = 30;
input string OrderCommentary = "Spike Trader";

int LastBars = 0;
int Timer = 0;

CTrade *Trade;
CPositionInfo PositionInfo;

void OnInit()
{
    // Initialize the Trade class object.
    Trade = new CTrade;
    Trade.SetDeviationInPoints(Slippage);
}

void OnDeinit(const int reason)
{
    delete Trade;
}

void OnTick()
{
    //Wait for the new Bar in a chart.
    if (LastBars == Bars(_Symbol, _Period)) return;
    else LastBars = Bars(_Symbol, _Period);

    if (Timer == 1) Trade.PositionClose(_Symbol);
    if (Timer > 0) Timer--;

    CheckEntry();
}

//+------------------------------------------------------------------+
//| Check for entry conditions and trade if necessary.               |
//+------------------------------------------------------------------+
void CheckEntry()
{
    MqlRates rates[];
    ArraySetAsSeries(rates, true);
    int copied = CopyRates(_Symbol, _Period, 1, BarsNumber + 1, rates);
    if (copied != BarsNumber + 1) Print("Error copying price data ", GetLastError());

    // Empty bar.
    if (rates[0].high - rates[0].low == 0) return;

    if (CheckSellEntry(rates))
    {
        if (PositionInfo.Select(_Symbol))
        {
            // If same direction - just reset the timer.
            if (PositionInfo.PositionType() == POSITION_TYPE_SELL)
            {
                Timer = Hold;
                return;
            }
            else Trade.PositionClose(_Symbol);
        }
        double Bid = SymbolInfoDouble(Symbol(), SYMBOL_BID);
        Trade.PositionOpen(_Symbol, ORDER_TYPE_SELL, Lots, Bid, 0, 0, OrderCommentary);
        Timer = Hold;
    }
    else if (CheckBuyEntry(rates))
    {
        if (PositionInfo.Select(_Symbol))
        {
            // If same direction - just reset the timer.
            if (PositionInfo.PositionType() == POSITION_TYPE_BUY)
            {
                Timer = Hold;
                return;
            }
            else Trade.PositionClose(_Symbol);
        }
        double Ask = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
        Trade.PositionOpen(_Symbol, ORDER_TYPE_BUY, Lots, Ask, 0, 0, OrderCommentary);
        Timer = Hold;
    }
}

bool CheckSellEntry(MqlRates &rates[])
{
    // If the bar isn't higher than at least one of the previous bars - return false.
    for (int i = 1; i < BarsNumber + 1; i++)
        if (rates[0].high <= rates[i].high) return false;

    // If not higher than the previous bar by required percentage difference - return false.
    if ((rates[0].high - rates[1].high) / rates[1].high < PercentageDifference) return false;
    
    // If closed above the lower third/half - return false.
    if ((rates[0].close - rates[0].low) / (rates[0].high - rates[0].low) > ThirdOrHalf) return false;

    return true;
}

bool CheckBuyEntry(MqlRates &rates[])
{
    // If the bar isn't lower than at least one of the previous bars - return false.
    for (int i = 1; i < BarsNumber + 1; i++)
        if (rates[0].low >= rates[i].low) return false;

    // If not lower than the previous bar by required percentage difference - return false.
    if ((rates[1].low - rates[0].low) / rates[1].low < PercentageDifference) return false;

    // If closed below the upper third/half - return false.
    if ((rates[0].high - rates[0].close) / (rates[0].high - rates[0].low) > ThirdOrHalf) return false;

    return true;
}
//+------------------------------------------------------------------+'''))
# The distribution license text is the exact upstream Apache 2.0 text.
a=Path('/usr/share/common-licenses/Apache-2.0').read_bytes()
# Debian's copy has one extra leading newline. A cryptographic equality check
# is required before this text is used, rather than assuming equivalence.
for candidate in (a,a[1:]):
    if blob(candidate)=='261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64':
        (OUT/'licenses'/'Apache-2.0.txt').write_bytes(candidate)
        break
else:
    raise ValueError('Apache license bytes do not match upstream')

DATA.append({
'id':'earnforex-spike-trader','name':'Spike Trader','platforms':['MT4','MT5'],'kind':'Expert Advisor','category':'Price action',
'license':'Apache-2.0','provider':'EarnForex','repo':'EarnForex/Spike-Trader','commit':'abc322e8da3c7fc9c701d056f01a70ebe4e20cd5',
'path':'SpikeTrader.mq4','files':FILES,'local_source':FILES[0]['local_source'],'blob_sha1':FILES[0]['blob_sha1'],'sha256':FILES[0]['sha256'],
'license_file':'licenses/Apache-2.0.txt','license_blob_sha1':'261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64',
'source_url':'https://github.com/EarnForex/Spike-Trader/tree/abc322e8da3c7fc9c701d056f01a70ebe4e20cd5',
'distribution':'bundled','license_review':'Pinned author repository license, copyright and complete relevant source/dependency declarations checked; original bytes verified. No separate NOTICE in pinned tree.',
'compiled':False,'runtime_tested':False,'check_date':'2026-10-01','risk_level':'Research only',
'dependencies':{'en':'MT4: no external includes found. MT5: standard terminal Trade/Trade.mqh and Trade/PositionInfo.mqh, not redistributed in this bundle.','ja':'MT4版は外部インクルードなし。MT5版はターミナル標準のTrade/Trade.mqhとTrade/PositionInfo.mqhが必要です。標準ライブラリはこの配布物に含めません。'},
'notices':{'en':'Original © 2012–2022 EarnForex. Both platform variants are one catalogue item. No binaries, account data, or credentials are included.','ja':'原著作権は© 2012–2022 EarnForex。MT4・MT5の2版を1件として数えます。実行形式・口座データ・認証情報は含みません。'},
'known_issues':{
'en':['No broker-side stop-loss or take-profit is placed: both values are zero in entry calls.','MT5 selects and closes by symbol without a magic-number filter. It may interfere with manual or other-EA positions on the same symbol.','MT5 logs a CopyRates failure but continues indexing the array. Insufficient history can cause an error.','The hold timer exists only in memory and resets on reattachment/restart. Repeated same-direction signals reset the timer.','MT4 ClosePrev can return true after a close failure; MT5 does not check trade result codes. A failed close is not guaranteed to prevent a new entry.'],
'ja':['新規注文で損切り・利確の価格に0を渡しており、サーバー側の保護注文は入りません。','MT5版は銘柄だけでポジションを選択・決済し、マジックナンバーを絞り込みません。同じ銘柄の手動注文や他EAへ干渉する可能性があります。','MT5版はCopyRatesの取得失敗を記録しても処理を止めず、配列へアクセスします。履歴不足時にエラーになり得ます。','保有タイマーはメモリー内だけで保持され、再起動や付け直しで初期化されます。同方向シグナルが出ると再設定されます。','MT4版は決済失敗後もClosePrevがtrueを返す経路があり、MT5版も注文結果を確認しません。決済できなかった場合の新規注文停止は保証されません。']},
'static':{'dll':False,'webrequest':False,'external_imports':False,'order_execution':True,'scope':'Keyword and direct code inspection only; not a security or runtime certification.'},
 'text':{
'en':{'purpose':'Study a counter-spike trading rule with separate MT4 and MT5 source implementations. Research and isolated demo use only.','mechanism':'On a new chart bar, tests whether the last completed bar extended beyond the preceding highs or lows, exceeded a relative-price threshold, and closed back inside a defined share of its range. It trades against that spike, reverses on an opposite signal, and uses an in-memory bar timer to close positions.','settings':'Original defaults: Hold 11 bars; BarsNumber 3; PercentageDifference 0.003 (0.3%); ThirdOrHalf 0.5; Lots 0.1; Slippage 30 points. These are upstream defaults, not a recommended setup. Compile the matching platform file and test only in an isolated demo environment after reading the known issues.','caution':'The author warns this EA can lose all funds. The original code lacks a protective stop, and the MT5 variant can manage unrelated same-symbol positions. This bundle preserves the original for study; it is not a live-ready product or an endorsement of its historic backtest claims.'},
'ja':{'purpose':'急な高安更新に逆方向で入る条件を、MT4・MT5それぞれの原本で学ぶEA。研究・隔離したデモ環境用です。','mechanism':'新しいバーで直前の確定バーを調べ、過去高安の更新・一定比率以上の伸び・値幅の内側への戻りを判定します。スパイクに逆方向で入り、反対シグナルで反転。メモリー内のバー数タイマーで決済します。','settings':'原本の初期値はHold 11バー・BarsNumber 3・PercentageDifference 0.003（0.3%）・ThirdOrHalf 0.5・Lots 0.1・Slippage 30ポイント。推奨設定ではありません。対応する版をコンパイルし、既知の問題を読んでから隔離したデモ環境で試します。','caution':'作者は全資金を失う可能性を警告しています。原本に保護ストップがなく、MT5版は同一銘柄の他ポジションにも干渉し得ます。研究用に原本を保持した配布で、実運用向け製品や過去のバックテスト成績の推奨ではありません。'}}})
(BASE/'bundled_catalog.json').write_text(json.dumps(DATA,ensure_ascii=False,indent=2),encoding='utf-8')
print('Verified MetaTrader originals:', [(f['path'],f['bytes'],f['encoding']) for f in FILES])
print('Catalogue items:',len(DATA))
