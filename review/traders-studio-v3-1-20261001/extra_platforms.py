from pathlib import Path
import json,zipfile,hashlib,html
R=Path(__file__).resolve().parent;P=R/'public/trading';V=R/'private'
cat=json.loads((P/'assets/catalog.json').read_text());full=json.loads((V/'catalog-full.json').read_text())
freq='''# --- Do not remove these libs ---
from freqtrade.strategy import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class Simple(IStrategy):
    """

    author@: Gert Wohlgemuth

    idea:
        this strategy is based on the book, 'The Simple Strategy' and can be found in detail here:

        https://www.amazon.com/Simple-Strategy-Powerful-Trading-Futures-ebook/dp/B00E66QPCG/ref=sr_1_1?ie=UTF8&qid=1525202675&sr=8-1&keywords=the+simple+strategy
    """

    INTERFACE_VERSION: int = 3
    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.01
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.25

    # Optimal timeframe for the strategy
    timeframe = '5m'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=7)

        # required for graphing
        bollinger = qtpylib.bollinger_bands(dataframe['close'], window=12, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['bb_middleband'] = bollinger['mid']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                        (dataframe['macd'] > 0)  # over 0
                        & (dataframe['macd'] > dataframe['macdsignal'])  # over signal
                        & (dataframe['bb_upperband'] > dataframe['bb_upperband'].shift(1))  # pointed up
                        & (dataframe['rsi'] > 70)  # optional filter, need to investigate
                )
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # different strategy used for sell points, due to be able to duplicate it to 100%
        dataframe.loc[
            (
                (dataframe['rsi'] > 80)
            ),
            'exit_long'] = 1
        return dataframe
'''
lean='''# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from AlgorithmImports import *

### <summary>
### Basic template algorithm simply initializes the date range and cash. This is a skeleton
### framework you can use for designing an algorithm.
### </summary>
### <meta name="tag" content="using data" />
### <meta name="tag" content="using quantconnect" />
### <meta name="tag" content="trading and orders" />
class BasicTemplateAlgorithm(QCAlgorithm):
    \'\'\'Basic template algorithm simply initializes the date range and cash\'\'\'

    def initialize(self):
        \'\'\'Initialise the data and resolution required, as well as the cash and start-end dates for your algorithm. All algorithms must initialized.\'\'\'

        self.set_start_date(2013,10, 7)  #Set Start Date
        self.set_end_date(2013,10,11)    #Set End Date
        self.set_cash(100000)           #Set Strategy Cash
        # Find more symbols here: http://quantconnect.com/data
        self.add_equity("SPY", Resolution.MINUTE)
        self.debug("numpy test >>> print numpy.pi: " + str(np.pi))

    def on_data(self, data):
        \'\'\'OnData event is the primary entry point for your algorithm. Each new data point will be pumped in here.

        Arguments:
            data: Slice object keyed by symbol containing the stock data
        \'\'\'
        if not self.portfolio.invested:
            self.set_holdings("SPY", 1)
'''
bt='''#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import MovingAverageBase, Average


class MovingAverageSimple(MovingAverageBase):
    \'\'\'
    Non-weighted average of the last n periods

    Formula:
      - movav = Sum(data, period) / period

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Simple_moving_average
    \'\'\'
    alias = ('SMA', 'SimpleMovingAverage',)
    lines = ('sma',)

    def __init__(self):
        # Before super to ensure mixins (right-hand side in subclassing)
        # can see the assignment operation and operate on the line
        self.lines[0] = Average(self.data, period=self.p.period)

        super(MovingAverageSimple, self).__init__()
'''
entries=[
('freqtrade-simple','Freqtrade Simple','Freqtrade','Strategy','Gert Wohlgemuth / Freqtrade contributors','freqtrade/freqtrade-strategies','f3340ce11f5bdf62f598522e64d1f5638eaa13f5','user_data/strategies/berlinguyinca/Simple.py','Simple.py','GPL-3.0','GPL-3.0.txt',freq,
 ['MACD・RSI・ボリンジャーバンドを組み合わせるFreqtrade用ストラテジーです。','MACDが正かつシグナルより上、バンド上限が前の足より高く、RSIが70超で買い条件。RSIが80超で決済条件を立てます。初期値は5分足・ROI1%・損切り25%です。','対応するFreqtrade環境とTA-Lib・pandasを用意し、Simple.pyをuser_data/strategiesへ保存。クラス名Simpleを指定してバックテストを行い、dry-run設定で検証します。','掲載コードを実行していません。ROI・損切りの数値は作者の初期値であり推奨値ではありません。設定ファイルで上書きされる項目もあります。依存ライブラリと価格データは同梱していません。'],
 ['Study a Freqtrade strategy using MACD, RSI and Bollinger bands.','A long entry requires positive MACD above its signal, a rising upper band, and RSI above 70. RSI above 80 sets an exit signal. Defaults include 5-minute candles, 1% ROI and a 25% stop loss.','Use a compatible Freqtrade environment with its required TA-Lib and pandas dependencies. Put Simple.py in user_data/strategies, select the Simple class, backtest first and evaluate only in configured dry-run mode.','Not executed or performance-tested. Defaults are not recommendations; configuration can override them. Runtime dependencies and market data are not included.']),
('lean-basic-template','LEAN Basic Template','QuantConnect / LEAN','Template','QuantConnect Corporation','QuantConnect/Lean','41c6e603e5671ca7b5d3de0cbe13b3c4b109bba4','Algorithm.Python/BasicTemplateAlgorithm.py','BasicTemplateAlgorithm.py','Apache-2.0','Apache-2.0.txt',lean,
 ['QuantConnect／LEANでアルゴリズムを作るための基本ひな形です。','検証期間と資金を設定し、SPYの1分足を読み込みます。保有がないとき、SPYに全額配分する注文を要求する単純な例です。売買優位性を実装した完成戦略ではありません。','LEANのPythonプロジェクト内で利用します。AlgorithmImportsとLEANの実行環境、対象期間のデータが必要です。元のサンプルを別名で保存し、バックテスト用に期間・配分を変更して確認します。','通常のPythonだけで実行するコードではありません。実行・バックテスト未実施。全額配分の初期例を実口座の設定として採用しないでください。商用クラウドや有料データは同梱・契約していません。'],
 ['Learn the initialization and data-event structure of a LEAN Python algorithm.','The sample configures dates and cash, adds minute-resolution SPY data, and requests a full SPY allocation when the portfolio is not invested. It is a template, not a validated trading edge.','Use inside a LEAN Python project with AlgorithmImports and the required data. Keep a separate copy and change dates and allocation for a controlled backtest.','Not standalone Python; LEAN is required. No backtest or live execution was performed. The sample full-allocation setting is not a recommendation. No paid cloud or data subscription is included.']),
('backtrader-sma','Backtrader Simple Moving Average','Backtrader','Indicator','Daniel Rodriguez','mementum/backtrader','b853d7c90b6721476eb5a5ea3135224e33db1f14','backtrader/indicators/sma.py','sma.py','GPL-3.0-or-later','GPL-3.0.txt',bt,
 ['Backtraderの移動平均インジケーターを構成するソースです。','MovingAverageBaseを継承し、Averageで指定期間の非加重平均を計算します。SMAとSimpleMovingAverageという別名で参照できます。売買注文は出しません。','Backtraderのパッケージ構造の中で読む実装です。通常の戦略ではbt.indicators.SimpleMovingAverage(data, period=...)を使います。改変はパッケージの複製で行い、sma.pyだけを単独実行しないでください。','MovingAverageBaseとAverageへの相対インポートがあるため、この1ファイルだけでは動きません。Backtrader環境とデータは別途必要です。実行・描画・数値比較は未検証です。'],
 ['Read the source of Backtrader’s simple moving-average indicator.','MovingAverageSimple extends MovingAverageBase and assigns an Average over the chosen period. It exposes SMA and SimpleMovingAverage aliases and places no orders.','Use within the Backtrader package. Strategies normally call bt.indicators.SimpleMovingAverage(data, period=...). Study or modify a separate package checkout rather than running this file alone.','Relative imports require MovingAverageBase and Average from Backtrader. Dependencies and data are not bundled. No runtime, plot or numerical comparison was performed.'])]
keys=['purpose','mechanism','settings','caution']
for id,name,platform,kind,author,repo,commit,path,namefile,license,licfile,source,ja,en in entries:
 if any(d['id']==id for d in cat):continue
 d=dict(id=id,name=name,platforms=[platform],kind=kind,category='Development' if kind=='Template' else 'Trend',license=license,author=author,version='Python / '+platform,mode='free',sourceAccess='verified-email-required',compiled=False,runtime_tested=False,origin='curated',text={'ja':dict(zip(keys,ja)),'en':dict(zip(keys,en))})
 q=V/'sources'/id;q.mkdir(exist_ok=True);(q/namefile).write_text(source,encoding='utf-8')
 prov=dict(repository=repo,commit=commit,source_url=f'https://github.com/{repo}/blob/{commit}/{path}',license_url=f'https://github.com/{repo}/blob/{commit}/LICENSE',license=license,author=author,review='Pinned license grant and source inspected; original notices retained; UTF-8 text export, source logic unchanged; external runtime not redistributed',sha256=hashlib.sha256(source.encode()).hexdigest(),check_date='2026-10-01',compiled=False,runtime_tested=False)
 (V/'provenance'/f'{id}.json').write_text(json.dumps(prov,indent=2,ensure_ascii=False))
 lic=(V/'licenses'/licfile).read_text()
 with zipfile.ZipFile(V/'downloads'/f'{id}.zip','w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('source/'+namefile,source.encode());z.writestr('LICENSE.txt',lic);z.writestr('PROVENANCE.json',json.dumps(prov,indent=2,ensure_ascii=False));z.writestr('README-BSV.txt','\n\n'.join(ja+en))
 f={**d,**prov,'provider':author,'download':f'downloads/{id}.zip','files':[{'path':namefile,'local_source':f'sources/{id}/{namefile}','platform':platform,'encoding':'utf-8'}],'license_file':'licenses/'+licfile}
 if repo=='QuantConnect/Lean':
  computed=hashlib.sha1(b'blob '+str(len(source.encode())).encode()+b'\0'+source.encode()).hexdigest()
  assert computed=='86990a4c42522f8b342765b656363fbf4e97d112',computed
  f['blob_sha1']=computed
 if repo=='mementum/backtrader':
  computed=hashlib.sha1(b'blob '+str(len(source.encode())).encode()+b'\0'+source.encode()).hexdigest()
  assert computed=='0207131eefe2ef48a1630fcbbc8a13bba1a6a28a',computed
  f['blob_sha1']=computed
 cat.append(d);full.append(f)
 template=(P/'items/spotware-sample-sma.html').read_text().replace('cTrader Sample SMA',html.escape(name)).replace('data-item="spotware-sample-sma"','data-item="'+id+'"')
 (P/'items'/f'{id}.html').write_text(template)
(V/'catalog-full.json').write_text(json.dumps(full,indent=2,ensure_ascii=False));(P/'assets/catalog.json').write_text(json.dumps(cat,indent=2,ensure_ascii=False))
platforms=json.loads((P/'assets/platforms.json').read_text())
(P/'assets/catalog.js').write_text('window.TRADERS_CATALOG='+json.dumps(cat,ensure_ascii=False).replace('<','\\u003c')+';\nwindow.TRADERS_PLATFORMS='+json.dumps(platforms,ensure_ascii=False)+';')
print('SOURCE PROGRAMS',len(cat),'PLATFORMS',sorted(set(x for d in cat for x in d['platforms'])))
