"""Pinned source snapshots. Never execute third-party trading code."""
from seed_sources import *

add('oscillators/awesome_oscillator.pine','4c41997084b4a75ac9ee9d29b1d3db3a66d52888','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Awesome Oscillator script may be freely distributed under the terms of GPL-3.0 license.
study("Awesome Oscillator", shorttitle="AO")

fastLength = input(title="Fast Length", type=integer, defval=5)
slowLength = input(title="Slow Length", type=integer, defval=34)

ao = sma(hl2, fastLength) - sma(hl2, slowLength)

aoColor = ao >= 0 ? (ao[1] < ao ? #26A69A : #B2DFDB) : (ao[1] < ao ? #FFCDD2 : #EF5350)
plot(ao, title="AO", style=columns, color=aoColor, transp=0)
''','Awesome Oscillator','Momentum','Compare short and long midpoint-price momentum.','高値・安値の中間価格から短期と長期の勢いを比較。','Subtracts the slow SMA of hl2 from the fast SMA; histogram colors encode the sign and whether the value is increasing.','中間価格の短期単純移動平均から長期平均を引き、正負と前バーからの増減で色分けします。','Fast Length 5; Slow Length 34. Compare zero crossings and direction changes against the underlying chart.','初期値は短期5・長期34。ゼロラインと増減を実際の価格の動きと照合します。','A rising histogram below zero is still negative momentum by this measure. No order execution or alerts are implemented here.','ゼロより下で上向いても、この指標の値はまだマイナスです。この版に発注やアラート機能はありません。')
add('oscillators/accelerator_oscillator.pine','21a846663e510987eca549db6920cdeeb6c16168','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Accelerator Oscillator script may be freely distributed under the terms of GPL-3.0 license.
study("Accelerator Oscillator", shorttitle="AC")

fastLength = input(title="Fast Length", type=integer, defval=5)
slowLength = input(title="Slow Length", type=integer, defval=34)
smoothLength = input(title="Smoothing Length", type=integer, defval=5)

ao = sma(hl2, fastLength) - sma(hl2, slowLength)

ac = ao - sma(ao, smoothLength)

acColor = ac >= 0 ? (ac[1] < ac ? #26A69A : #B2DFDB) : (ac[1] < ac ? #FFCDD2 : #EF5350)
plot(ac, title="AC", style=columns, color=acColor, transp=0)
''','Accelerator Oscillator','Momentum','Study momentum changes relative to a smoothed baseline.','勢いが平滑化した基準からどの程度変化したかを表示。','Calculates Awesome Oscillator from midpoint SMAs, then subtracts an SMA of that oscillator. It is a momentum residual, not a direct price forecast.','中間価格の平均差からAwesome Oscillatorを求め、その平均をさらに引きます。勢いの差を示すもので、将来価格を計算するものではありません。','Fast 5; Slow 34; Smoothing 5. Start with the defaults and change one length at a time in replay.','短期5・長期34・平滑化5。リプレイで一つずつ期間を変え、反応とダマシの違いを比較します。','Short smoothing can produce frequent sign changes. Histogram color alone is not a complete trading system.','平滑化期間を短くすると正負の切り替わりが増えます。色だけでは損切り・決済を含む売買システムになりません。')
add('oscillators/coppock_curve.pine','aef373703a2f05ae61580c36f112258b1c0b58b3','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Coppock Curve script may be freely distributed under the terms of GPL-3.0 license.
study("Coppock Curve")

length = input(title="Smoothing Length", type=integer, defval=10)
longRocLength = input(title="Long ROC Length", type=integer, defval=14)
shortRocLength = input(title="Short ROC Length", type=integer, defval=11)
src = input(title="Source", type=source, defval=close)

coppock = wma(roc(src, longRocLength) + roc(src, shortRocLength), length)

coppockColor = coppock > 0 ? #0ebb23 : red

plot(coppock, title="Coppock", linewidth=2, color=coppockColor, transp=0)
hline(0, title="Zero Level", linestyle=dotted)
''','Coppock Curve','Momentum','Combine two rates of change into a smoother momentum curve.','二つの変化率を合成し、平滑化したモメンタムを表示。','Adds the 14-bar and 11-bar percentage rates of change, then applies a 10-bar weighted moving average.','14バーと11バーの価格変化率を足し、10バーの加重移動平均を適用します。','Smoothing 10; long ROC 14; short ROC 11. All lengths refer to chart bars, not automatically to months.','平滑化10・長期変化率14・短期変化率11。期間の単位は表示中のバーで、常に月数を表すわけではありません。','Longer settings introduce delay. A zero crossing is descriptive, not proof of a durable trend or a tested return.','期間を長くすると遅れます。ゼロ越えは継続的なトレンドや運用成績の証明ではありません。')
add('oscillators/disparity_index.pine','b339d6e040428a50d32b5aa456d5e24625db4c38','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Disparity Index script may be freely distributed under the terms of the GPL-3.0 license.
study("Disparity Index", shorttitle="DI")

length = input(title="Length", type=integer, minval=1, defval=14)
src = input(title="Source", type=source, defval=close)

di = 100 * (src - sma(src, length)) / sma(src, length)

diColor = di >= 0.0 ? #0ebb23 : #ff0000
plot(di, title="Disparity Index", linewidth=2, color=diColor, transp=0)

hline(0, title="Zero Level", linestyle=dotted, color=#989898)
''','Disparity Index','Mean reversion','Measure the percentage gap between price and its moving average.','価格と移動平均の乖離を百分率で把握。','Calculates 100 × (source − SMA) / SMA and colors the result around zero.','100 ×（価格−単純移動平均）÷単純移動平均を計算し、ゼロを境に色を変えます。','Length 14; source close. Compare the distribution of deviations within the same instrument and timeframe before choosing thresholds.','初期値は期間14・終値。閾値を決める前に、同じ銘柄・時間足で乖離の分布を比較します。','A large deviation can persist in a trend. A zero moving average creates a zero denominator; no stop or trade logic is included.','強いトレンドでは乖離が続くことがあります。平均がゼロの系列では分母がゼロになります。発注や損切りの機能はありません。')
add('oscillators/forecast_oscillator.pine','996c8840a1ed25e32b84d91baa3cb3689de40142','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Forecast Oscillator script may be freely distributed under the terms of the GPL-3.0 license.
study("Forecast Oscillator", shorttitle="FOSC")

length = input(title="Length", type=integer, minval=1, defval=14)
src = input(title="Source", type=source, defval=close)

fosc = 100 * (src - linreg(src, length, 0)) / src

foscColor = fosc >= 0.0 ? #0ebb23 : #ff0000

plot(fosc, title="FOSC", linewidth=2, color=foscColor, transp=0)

hline(0, title="Zero Level", linestyle=dotted, color=#989898)
''','Forecast Oscillator','Mean reversion','Compare price with the current endpoint of a rolling linear regression.','現在価格とローリング回帰線の終点の差を比較。','Shows 100 × (source − current regression endpoint) / source. Despite its name, the script does not produce a future price target.','100 ×（価格−現在の回帰線終点）÷価格を表示します。名称にForecastとありますが、将来の価格目標は出しません。','Length 14 and close are defaults. Compare sign changes and deviation size with the actual price path.','初期値は期間14・終値。正負の変化と乖離幅を実際の値動きと照合します。','The denominator is the source price. Regression fit and a positive oscillator do not establish predictive accuracy.','分母は入力価格です。回帰への適合や値のプラスだけでは予測精度を証明できません。')
add('oscillators/center_of_gravity_oscillator.pine','fa70862e086b00ca1d456ab1ca58207b51eca9e7','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// CG Oscillator script may be freely distributed under the terms of the GPL-3.0 license.
study("CG Oscillator", shorttitle="CGO")

length = input(title="Length", type=integer, minval=1, defval=10)
applyFilling = input(title="Apply Filling ?", type=bool, defval=false)
src = input(title="Source", type=source, defval=hl2)

numeratorSum = 0.0
denominatorSum = 0.0

for i = 0 to length - 1
	numeratorSum := numeratorSum + (i + 1) * nz(src[i])
	denominatorSum := denominatorSum + nz(src[i])

cgo = -numeratorSum / denominatorSum

cgoPlot = plot(cgo, title="CGO", color=#3d85c6, transp=0)
cgoPrevPlot = plot(cgo[1], title="CGO Prev", color=#ff3e7d, transp=0)

fillColor = applyFilling ? (cgo > cgo[1] ? #0ebb23 : #cc0000) : color(white, 100)
fill(cgoPlot, cgoPrevPlot, color=fillColor, transp=0)
''','Center of Gravity Oscillator','Momentum','Explore a price-weighted oscillator against its prior-bar trigger.','価格で重み付けしたオシレーターと前バーの値を比較。','Divides the negative sum of price × bar distance by the sum of prices. The second line is the oscillator one bar earlier.','価格×バー距離の合計にマイナスを付け、価格合計で割ります。もう一本は一つ前のバーの値です。','Length 10; source hl2; optional fill. Compare line crosses in replay instead of treating the smooth historical view as a trade log.','期間10・中間価格が初期値。塗りつぶしは任意です。過去の滑らかな表示を売買実績と扱わず、リプレイで交差を比較します。','The sum-of-prices denominator must not be zero. No explicit fixed overbought/oversold thresholds are supplied.','価格合計がゼロの系列には注意が必要です。固定の買われすぎ・売られすぎ水準は設定されていません。')
add('oscillators/derivative_oscillator.pine','09809137771ba719fbc7496323f7788874c45767','''//@version=4
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Derivative Oscillator script may be freely distributed under the terms of GPL-3.0 license.
study("Derivative Oscillator", shorttitle="DOSC")

rsiLength = input(title="RSI Length", type=input.integer, defval=14)
ema1Length = input(title="1st EMA Smoothing Length", type=input.integer, defval=5)
ema2Length = input(title="2nd EMA Smoothing Length", type=input.integer, defval=3)
smaLength = input(title="3rd SMA Smoothing Length", type=input.integer, defval=9)
signalLength = input(title="Signal Length", type=input.integer, defval=9)
src = input(title="Source", type=input.source, defval=close)

smoothedRSI = ema(ema(rsi(src, rsiLength), ema1Length), ema2Length)
dosc = smoothedRSI - sma(smoothedRSI, smaLength)
signal = sma(dosc, signalLength)

doscColor = dosc >= 0 ? dosc[1] < dosc ? #26A69A : #B2DFDB : dosc[1] < dosc ? #FFCDD2 : #EF5350
plot(dosc, title="DOSC", style=plot.style_columns, linewidth=2, color=doscColor, transp=0)
plot(signal, title="Signal", linewidth=2, color=color.black, transp=0)
''','Derivative Oscillator','Momentum','Observe changes in a twice-smoothed RSI.','二段階で平滑化したRSIの変化を確認。','Smooths RSI with EMA 5 then EMA 3, subtracts a 9-bar SMA, and overlays another 9-bar signal SMA.','RSIをEMA5、EMA3の順で平滑化し、SMA9を引いた値と、そのSMA9のシグナル線を表示します。','RSI 14; smoothing 5/3/9; signal 9. Keep lengths positive and compare sensitivity versus delay.','RSI14・平滑化5/3/9・シグナル9。期間は正の値にし、反応の速さと遅れを比較します。','The black signal line may be hard to see on dark charts; change its style color in TradingView. This is not a strategy backtest.','黒いシグナル線は暗い背景で見えにくいため、TradingViewのスタイル設定で色を調整します。ストラテジーやバックテストではありません。')
add('oscillators/dorsey_inertia.pine','e31b950da9ba4c31bb416ee2ed995fd6f74db9c9','''//@version=3
// Copyright (c) 2019-present, Alex Orekhov (everget)
// Dorsey Inertia script may be freely distributed under the terms of GPL-3.0 license.
study("Dorsey Inertia", shorttitle="Inertia")

stdevLength = input(title="Standard Deviation Length", type=integer, defval=21)
rviSmoothLength = input(title="RVI Smoothing Length", type=integer, defval=14)
smoothLength = input(title="Inertia Smoothing Length", type=integer, defval=14)

// Relative Volatility Index (1993)
rviOriginal(src, stdevLength, smoothLength) =>
	stdev = stdev(src, stdevLength)
	upSum = ema(change(src) >= 0 ? stdev : 0, smoothLength)
	downSum = ema(change(src) >= 0 ? 0 : stdev, smoothLength)
	100 * upSum / (upSum + downSum)

rvi = avg(rviOriginal(high, stdevLength, rviSmoothLength), rviOriginal(low, stdevLength, rviSmoothLength))
inertia = linreg(rvi, smoothLength, 0)

inertiaColor = inertia > 50 ? #0ebb23 : red

plot(inertia, title="Inertia", linewidth=2, color=inertiaColor, transp=0)
hline(50, title="Middle Level", linestyle=dotted)
''','Dorsey Inertia','Volatility','Separate directional volatility and smooth it into a relative-strength curve.','方向別のボラティリティを平滑化して相対的な強弱を表示。','Calculates a Relative Volatility Index separately on highs and lows, averages them, then takes a rolling regression endpoint.','高値と安値それぞれのRelative Volatility Indexを平均し、ローリング回帰線の終点を求めます。','Standard deviation 21; RVI smoothing 14; inertia smoothing 14. The reference level is 50.','標準偏差21・RVI平滑化14・慣性平滑化14。基準線は50です。','RVI here means Relative Volatility Index, not Relative Vigor Index. Flat series can make the volatility denominator zero.','ここでのRVIはRelative Volatility Indexで、Relative Vigor Indexとは別物です。変化のない系列では分母がゼロになる場合があります。')
add('oscillators/ehlers_cyber_cycle.pine','073ad6f97ecdd9b3ec340d8d5c86d4d03a4953f1','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Ehlers Cyber Cycle script may be freely distributed under the terms of the GPL-3.0 license.
study("Ehlers Cyber Cycle", shorttitle="ECC")

length = input(title="Length", type=integer, minval=1, defval=14)
alpha = input(title="Alpha", type=float, step=0.1, defval=0.7)
applyFilling = input(title="Apply Filling ?", type=bool, defval=false)
src = input(title="Source", type=source, defval=close)

smooth = (src + 2 * nz(src[1]) + 2 * nz(src[2]) + nz(src[3])) / 6

ecc = 0.0
ecc := pow(1 - alpha / 2, 2) * (smooth - 2 * nz(smooth[1]) + nz(smooth[2])) + 2 * (1 - alpha) * nz(ecc[1]) - pow(1 - alpha, 2) * nz(ecc[2])

eccPlot = plot(ecc, title="ECC", color=#3d85c6, transp=0)
eccPrevPlot = plot(ecc[1], title="Trigger", color=#ff3e7d, transp=0)

fillColor = applyFilling ? (ecc > ecc[1] ? #0ebb23 : #cc0000) : color(white, 100)
fill(eccPlot, eccPrevPlot, color=fillColor, transp=0)
''','Ehlers Cyber Cycle','Research','Inspect a recursive cycle filter and its one-bar trigger.','再帰型サイクルフィルターと1バー前のトリガーを比較。','Applies a four-price smoothing kernel and a second-difference recursive filter controlled by Alpha. The trigger is the prior-bar filter value.','4価格の加重平滑化に二階差分と再帰処理を組み合わせます。Alphaが係数を決め、トリガーには1バー前の値を使います。','Alpha defaults to 0.7. The Length input defaults to 14 but is not used in this source calculation.','Alphaの初期値は0.7。Lengthは初期値14ですが、この原本の計算では使われていません。','Known issue: changing Length has no effect. The unconstrained Alpha input can produce unstable settings. Historical initialization can affect early values.','既知の問題：Lengthを変えても計算は変わりません。Alphaには範囲制約がなく、不安定な設定になり得ます。初期化は序盤の値にも影響します。')
(BASE/'bundled_catalog.json').write_text(json.dumps(DATA,ensure_ascii=False,indent=2),encoding='utf-8')
print('Verified total Pine source snapshots:',len(DATA))
