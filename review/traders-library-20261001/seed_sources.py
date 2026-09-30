from pathlib import Path
import hashlib,json,shutil
BASE=Path(__file__).resolve().parent
OUT=BASE/'trading'
DATA=[]
GPL_COMMIT='60c93d3711d222b8f2db96160defe568429348e0'
MIT_COMMIT='6d14308f8ce42b2d60ec6c80eb224e8f4ffb3a79'
GPL_REPO='everget/tradingview-pinescript-indicators'
MIT_REPO='jamesbachini/Pine-Script-Examples'
MIT='''MIT License

Copyright (c) 2023 James Bachini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def add(path,sha,text,name,category,purpose_en,purpose_ja,mechanism_en,mechanism_ja,settings_en,settings_ja,caution_en,caution_ja,license='GPL-3.0-only',kind='Indicator'):
    b=text.encode();assert blob(b)==sha,(path,sha,blob(b),len(b))
    repo,commit=(MIT_REPO,MIT_COMMIT) if license=='MIT' else (GPL_REPO,GPL_COMMIT)
    id=('bachini-' if license=='MIT' else 'everget-')+Path(path).stem.replace('_','-')
    dest=OUT/'sources'/id/Path(path).name;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_bytes(b)
    licpath='MIT-James-Bachini.txt' if license=='MIT' else 'GPL-3.0.txt'
    DATA.append(dict(id=id,name=name,platforms=['TradingView'],kind=kind,category=category,license=license,provider='James Bachini' if license=='MIT' else 'Alex Orekhov (everget)',repo=repo,commit=commit,path=path,blob_sha1=sha,sha256=hashlib.sha256(b).hexdigest(),license_file=licpath,source_url=f'https://github.com/{repo}/blob/{commit}/{path}',local_source=f'sources/{id}/{Path(path).name}',distribution='bundled',license_review='File-level notice and pinned license checked; original bytes verified',compiled=False,runtime_tested=False,check_date='2026-10-01',text={'en':dict(purpose=purpose_en,mechanism=mechanism_en,settings=settings_en,caution=caution_en),'ja':dict(purpose=purpose_ja,mechanism=mechanism_ja,settings=settings_ja,caution=caution_ja)}))

add('sma.ps','9e706450f26935fc7a4ca3071eef924b8494d75f','''//@version=6
indicator("Simple Moving Average", shorttitle="SMA", overlay=true)
length = input.int(200, minval=1, title="Length")
smaValue = ta.sma(close, length)
plot(smaValue, title="SMA", color=color.blue)''','Simple Moving Average','Trend','A minimal trend baseline and a readable first Pine indicator.','トレンドの基準線とPine学習の最初の一本に。','Plots the arithmetic mean of closing prices over the selected number of bars. It neither places orders nor produces a backtest.','指定本数の終値の単純平均を表示します。注文やバックテストは行いません。','Length defaults to 200 bars, not 200 days. Compare the line with price and change only the period first.','初期値は200本です。200日ではありません。まず期間だけを変え、価格との位置関係を比較します。','The average lags price. A price cross alone is not a validated trading edge.','平均線は価格に遅れて動きます。価格との交差だけで有効な売買ルールとは判断できません。',license='MIT')
add('crossover.ps','e8b2522031b8a4415570f072b4a5f244a96c73d3','''//@version=6
strategy("Moving Average Cross", overlay=true)
shortLength = input.int(30, minval=1, title="Short Moving Average Length")
longLength = input.int(200, minval=1, title="Long Moving Average Length")
shortMA = ta.sma(close, shortLength)
longMA = ta.sma(close, longLength)
plot(shortMA, title="Short Moving Average", color=color.red)
plot(longMA, title="Long Moving Average", color=color.blue)
longCondition = ta.crossover(shortMA, longMA)
shortCondition = ta.crossunder(shortMA, longMA)
if (longCondition)
    strategy.entry("Long", strategy.long)
if (shortCondition)
    strategy.close("Long")
if (shortCondition)
    strategy.entry("Short", strategy.short)
if (longCondition)
    strategy.close("Short")''','Moving Average Cross','Trend','Study a complete long/short moving-average crossover backtest.','移動平均線の交差で売買する両方向ストラテジーの検証用。','Uses 30- and 200-bar simple moving averages. Crossovers request a long entry and close the short; crossunders do the reverse. Inspect the order list because reversals and explicit closes interact.','30本と200本の単純移動平均を使います。上抜けで買いと売りの決済、下抜けで売りと買いの決済を要求します。反転注文と明示的な決済が重なるため注文一覧も確認します。','Set short and long periods. In Strategy Tester, set capital, order size, commission and slippage before comparing runs.','短期・長期の期間を設定。ストラテジーテスターで資金、数量、手数料、スリッページを設定してから比較します。','No protective stop-loss is implemented. TradingView simulated orders are not a broker-connected automated system.','保護用の損切り注文は実装されていません。TradingView上のシミュレーションであり、証券会社に接続した自動売買ではありません。',license='MIT',kind='Strategy')
add('breakout_sniper.ps','1646139246e11f689dc8ff61658ad539a33bfc84','''//@version=6
strategy("Breakout Sniper", overlay=true)
lookback_period = input.int(365, "Lookback Period", minval=1)
hold = input.int(30, 'Holding Period', minval=1)

highest_high = ta.highest(high, lookback_period)
lowest_low = ta.lowest(low, lookback_period)

plot(highest_high, 'HIGH', color=#CC000088)
plot(lowest_low, 'HIGH', color=#00CC0088)

breakout = high >= highest_high
breakdown = low <= lowest_low

if (breakout)
    strategy.entry("Long", strategy.long)
if ta.barssince(breakout) > hold
    strategy.close("Long", comment="close long")
if (breakdown)
    strategy.entry("Short", strategy.short)
if ta.barssince(breakdown) > hold
    strategy.close("Short", comment="close short")''','Breakout Sniper','Breakout','Explore rolling high/low breakouts and signal-based exits.','過去の高安を使うブレイクアウトと、シグナル経過本数による決済の検証用。','The rolling extreme includes the current bar. Reaching that extreme triggers an entry request. The holding counter measures bars since the latest breakout signal, not bars since entry.','現在足を含む範囲の高値・安値への到達で注文を要求します。保有期間のカウントは建値の足からではなく、直近シグナルからの経過本数です。','Lookback starts at 365 bars and Holding Period at 30 bars. Test a shorter sample visually before increasing history.','参照期間は365本、保有期間入力は30本が初期値。短い期間で注文位置を目視してから履歴を広げます。','No stop-loss. Repeated signals reset the exit counter. The lower plot is also labelled HIGH in the original code.','損切りはありません。シグナルが繰り返されると決済カウントがリセットされます。原本では下側の線もHIGH表記です。',license='MIT',kind='Strategy')
add('price_channels.ps','180ecd079dae089b952175f164ffd4a7b2bca61c','''//@version=6
strategy("Price Channels", overlay=true)
fairvalue = input.int(21, 'Exponential Moving Average', minval=1)
hold = input.int(30, 'Holding Period', minval=1)
mult = input.float(2, 'Multiplier', minval=0.1, step = 0.1)
atr = ta.atr(14)
ma = ta.ema(close, fairvalue)

resistance = ma + (atr * mult)
support = ma - (atr * mult)

plot(ma, 'Average', color=#AAAAAA88)
plot(support, 'Support', color=#00DD0088)
plot(resistance, 'Resistance', color=#DD000088)

if ta.crossover(close, support)
    strategy.entry("Long", strategy.long)
if ta.barssince(ta.crossover(close, support)) > hold
    strategy.close("Long", comment="close 30 days")
if ta.crossover(close, resistance)
    strategy.close("Long", comment="close overvalued")''','Price Channels','Mean reversion','Backtest a long-only return inside an EMA/ATR channel.','EMAとATRのチャネル内へ戻る動きを買いのみで検証。','Builds a channel around EMA(21) using ATR(14) times two. A close crossing above the lower band requests a long. Crossing the upper band or elapsed signal time requests an exit.','EMA21を中心にATR14の2倍幅のチャネルを描きます。終値の下限上抜けで買い、上限上抜けやシグナル後の経過本数で決済を要求します。','EMA length, Holding Period and Multiplier are inputs. ATR length is fixed at 14 in this source.','EMA期間、保有期間、倍率が設定項目。ATR期間は原本のコード内で14に固定されています。','No short entries or stop-loss. The comment says days, but the holding parameter counts chart bars.','売りエントリーと損切りはありません。コメントはdaysですが、保有期間はチャートの本数です。',license='MIT',kind='Strategy')
add('fear_greed.ps','d5798ebcc0703fa7272c585a2023a4dd401eac90','''//@version=6
indicator("Fear and Greed Index", shorttitle="FGI", overlay=true)
extreme_fear = input.int(-40, "Extreme Fear")
extreme_greed = input.int(100, "Extreme Greed")
rsi = ta.rsi(close, 14)
fair_value = ta.ema(close, 14)
fv_indicator = (close / fair_value)
vol_high = ta.highest(volume, 90)
vol_low = ta.lowest(volume, 90)
vol_indicator = 1 + (volume / ((vol_high + vol_low) / 2))
stdev = ta.stdev(close, 14)
stdev_indicator = 1 + (stdev / close)
fgi = (rsi - 50) * fv_indicator * vol_indicator * stdev_indicator
bgcolor(fgi <= extreme_fear ? color.new(color.red, 90) : na)
bgcolor(fgi >= extreme_greed ? color.new(color.lime, 90) : na)''','Fear and Greed — Price/Volume Model','Momentum','Highlight extremes in a locally calculated price/volume score.','価格と出来高から独自計算したスコアの極端値を色で表示。','Combines centered RSI, price/EMA ratio, relative volume and relative standard deviation. It does not fetch the CNN or Alternative.me fear-and-greed index.','中心化したRSI、価格とEMAの比、相対出来高、標準偏差を掛け合わせます。CNNやAlternative.meの恐怖・強欲指数を取得するものではありません。','Extreme Fear starts at -40; Extreme Greed at 100. First check that the selected feed supplies usable volume.','恐怖側は-40、強欲側は100が初期値。使用する配信元に有効な出来高があることを先に確認します。','Missing or zero volume can invalidate the score. Values are feed-specific; no probability is implied.','出来高が欠落またはゼロだとスコアが成立しない場合があります。配信元で値が変わり、確率を示す数値ではありません。',license='MIT')
add('gaussian_regression.ps','5fa1cde84b1a8ef579db6798cf4b5b8493b46b61','''//@version=6
indicator("Gaussian Process Regression", shorttitle="GPR", overlay = true, max_lines_count = 300)
lookback_period = input.int(100, 'Lookback Period', minval=0)
prediction_horizon = input.int(30, 'Prediction Horizon', minval=0)
length_scale = input.float(10., 'Length Scale', minval=1)
noise_variance = input.float(0.1, step = 0.01, minval = 0)

radial_basis_function(x1, x2, scale) => math.exp(-math.pow(x1 - x2, 2) / (2.0 * math.pow(scale, 2)))

// Create a kernel matrix using the Radial Basis Function
create_kernel_matrix(training_set, test_set, scale) =>
    kernel_matrix = matrix.new<float>(training_set.size(), test_set.size())
    row_index = 0
    for train_point in training_set
        col_index = 0
        for test_point in test_set
            kernel_value = radial_basis_function(train_point, test_point, scale)
            kernel_matrix.set(row_index, col_index, kernel_value)
            col_index += 1
        row_index += 1
    kernel_matrix

var identity_matrix = matrix.new<int>(lookback_period, lookback_period, 0)
var matrix<float> prediction_kernel = na

// Set up initial training and test indices, noise matrix & compute the prediction kernel
if barstate.isfirst
    training_indices = array.new<int>(0)
    test_indices = array.new<int>(0)
    for i = 0 to lookback_period-1
        for j = 0 to lookback_period-1
            identity_matrix.set(i, j, i == j ? 1 : 0)
        training_indices.push(i)
    for i = 0 to lookback_period+prediction_horizon-1
        test_indices.push(i)
    noise_matrix = identity_matrix.mult(noise_variance * noise_variance)
    training_kernel = create_kernel_matrix(training_indices, training_indices, length_scale).sum(noise_matrix)
    training_kernel_inv = training_kernel.pinv()
    cross_kernel = create_kernel_matrix(training_indices, test_indices, length_scale)
    prediction_kernel := cross_kernel.transpose().mult(training_kernel_inv)

// Prepare the training outputs by subtracting the moving average from the close price.
current_index = bar_index
moving_average = ta.sma(close, lookback_period)
training_outputs = array.new<float>(0)
for i = 0 to lookback_period-1
    training_outputs.unshift(close[i] - moving_average)
predicted_means = prediction_kernel.mult(training_outputs)

// Loop through the predicted means to determine regression and forecast points
index_offset = -lookback_period+2
regression_points = array.new<chart.point>(0)
forecast_points = array.new<chart.point>(0)
for predicted_mean in predicted_means
    if index_offset == 1
        forecast_points.push(chart.point.from_index(current_index+index_offset, predicted_mean + moving_average))
        regression_points.push(chart.point.from_index(current_index+index_offset, predicted_mean + moving_average))
    else if index_offset > 1
        forecast_points.push(chart.point.from_index(current_index+index_offset, predicted_mean + moving_average))
    else
        regression_points.push(chart.point.from_index(current_index+index_offset, predicted_mean + moving_average))
    index_offset += 1
polyline.delete(polyline.new(regression_points, line_color = #FF00FF88, line_width = 10)[1])
polyline.delete(polyline.new(forecast_points, line_color = #FFFF0088, line_width = 10)[1])
''','Gaussian Process Regression','Research','Inspect a rolling regression curve and model projection.','ローリング回帰曲線とモデルによる延長線を研究。','Uses an RBF kernel, a pseudoinverse and a rolling vector of demeaned closes. It redraws the fitted and projected polylines as new bars arrive.','RBFカーネル、擬似逆行列、平均を引いた終値の配列で計算します。新しい足ごとに回帰線と予測線を描き直します。','Start with a positive lookback, the default 100 bars and 30-bar horizon. Length Scale controls smoothness; noise input is squared in the matrix.','参照期間はゼロにせず、まず初期値100本・予測30本を使用。Length Scaleは滑らかさに関わり、noise入力は行列内で二乗されます。','Redrawn historical fits are not historical trading signals. Projection is not forecast accuracy evidence. Zero lookback and very large matrices can fail.','描き直された過去の曲線は当時の売買シグナルではありません。延長線が当たる証拠にはならず、参照期間ゼロや過大な行列はエラー要因です。',license='MIT')

add('movings/arnaud_legoux_moving_average.pine','38d3524d05cda0a60907bb741d57bad08d1d3daf','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Arnaud Legoux Moving Average script may be freely distributed under the terms of the GPL-3.0 license.
study("Arnaud Legoux Moving Average", shorttitle="ALMA", overlay=true)

length = input(title="Length", type=integer, minval=1, defval=9)
offset = input(title="Offset", type=float, defval=0.85)
sigma = input(title="Sigma", type=float, defval=6)
src = input(title="Source", type=source, defval=close)

plot(alma(src, length, offset, sigma), title="ALMA", linewidth=2, color=#e69138, transp=0)
''','Arnaud Legoux Moving Average','Trend','Compare a smooth ALMA trend line with a standard average.','通常の移動平均とALMAの滑らかさ・追従性を比較。','Calls Pine’s ALMA function on the chosen price series. Offset and Sigma adjust the weighting profile.','選択した価格系列にPineのALMA関数を適用。OffsetとSigmaで重みの分布を調整します。','Length 9, Offset 0.85 and Sigma 6 are the original defaults.','原本の初期値はLength 9、Offset 0.85、Sigma 6です。','This is Pine v3 source. Keep its version header; conversion to a newer version requires a separate compile check.','Pine v3の原本です。バージョン行を維持し、新版への変換後は別途コンパイル確認が必要です。')
add('bands_and_channels/acceleration_bands.pine','298e46c21c2cf486d04719a18c55e86390ba893d','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Acceleration Bands script may be freely distributed under the terms of the GPL-3.0 license.
study(title="Acceleration Bands", shorttitle="AB", overlay=true)

length = input(title="Length", type=integer, defval=20)
factor = input(title="Factor", type=float, defval=0.001, step=0.0001)
src = input(title="Source", type=source, defval=close)

mult = 4000 * factor * (high - low) / (high + low)

upperBandSrc = high * (1 + mult)
upperBand = sma(upperBandSrc, length)

basis = sma(src, length)

lowerBandSrc = low * (1 - mult)
lowerBand = sma(lowerBandSrc, length)

upperBandPlot = plot(upperBand, title="Upper", linewidth=1, color=#138484, transp=0)

plot(basis, title="Basis", linewidth=1, color=#741b47, transp=0)

lowerBandPlot = plot(lowerBand, title="Lower", linewidth=1, color=#138484, transp=0)

fill(upperBandPlot, lowerBandPlot, title="Background", color=color(#ffd966, 84))
''','Acceleration Bands','Volatility','See a high/low envelope whose width responds to relative range.','相対的な高安差で幅が変わる価格帯を表示。','Expands high and low by a factor of their range relative to their sum, then smooths each boundary with an SMA.','高値と安値の和に対する値幅の比で上下を広げ、各境界を単純移動平均で平滑化します。','Length 20 and Factor 0.001 are the defaults. Change width independently from smoothing length.','初期値は期間20、Factor 0.001。線の幅と平滑化期間を分けて比較します。','Band contact is not automatically a reversal signal. The high-plus-low denominator assumes an appropriate price series.','バンド接触は反転を保証しません。高値＋安値を分母にするため、ゼロ近辺や負値を含む系列では注意が必要です。')
add('bands_and_channels/interquartile_range_bands.pine','869977a9d22f34afc636965e1a6c439636f8caf8','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Interquartile Range Bands script may be freely distributed under the terms of GPL-3.0 license.
study("Interquartile Range Bands", shorttitle="IQRB", overlay=true)

length = input(title="Length", type=integer, minval=1, defval=14)
mult = input(title="Multiplier", type=float, minval=0, step=0.1, defval=1.5)
src = input(title="Source", type=source, defval=close)

q1 = percentile_nearest_rank(src, length, 25)
median= percentile_nearest_rank(src, length, 50)
q3 = percentile_nearest_rank(src, length, 75)

iqr = q3 - q1

upperBand = q3 + mult * iqr
lowerBand = q1 - mult * iqr

upperBandPlot = plot(upperBand, title="Upper", color=#138484, transp=0)
plot(median, title="Median", color=#741b47, transp=0)
lowerBandPlot = plot(lowerBand, title="Lower", color=#138484, transp=0)
fill(upperBandPlot, lowerBandPlot, title="Background", color=color(#ffd966, 84))
''','Interquartile Range Bands','Volatility','Study outliers against a rolling median and quartiles.','移動する中央値と四分位数で価格の外れを観察。','Calculates nearest-rank 25th, 50th and 75th percentiles. The outer bands extend Q1 and Q3 by a multiple of Q3 minus Q1.','直近系列の25・50・75パーセンタイルを計算。第1・第3四分位から四分位範囲の倍率分だけ外へ広げます。','Length 14 and Multiplier 1.5 are the defaults.','期間14、倍率1.5が初期値です。','A short window yields stepped estimates. Statistical outliers are not a guarantee that price will revert.','短い窓では値が段階的に変わります。統計上の外れ値でも価格が戻るとは限りません。')
add('bands_and_channels/kirshenbaum_bands.pine','92211b24212c1e1b58e3c5ea655fb085908c1440','''//@version=3
// Copyright (c) 2019-present, Alex Orekhov (everget)
// Kirshenbaum Bands script may be freely distributed under the terms of the GPL-3.0 license.
study("Kirshenbaum Bands", shorttitle="KB", overlay=true)

length = input(title="Length", type=integer, defval=30)
regressionLength = input(title="Regression Length", type=integer, defval=20)
mult = input(title="Multiplier", type=float, step=0.1, defval=1.75)
src = input(title="Source", type=source, defval=close)

regression = linreg(src, regressionLength, 0)
stderror = mult * sqrt(sma(pow(src - regression, 2), regressionLength))

basis = ema(src, length)
upper = basis + stderror
lower = basis - stderror

plot(basis, title="Basis", color=#351c75, transp=0)
upperBandPlot = plot(upper, title="Upper", color=#45818e, transp=0)
lowerBandPlot = plot(lower, title="Lower", color=#45818e, transp=0)
fill(upperBandPlot, lowerBandPlot, title="Background", color=color(#ffd966, 84))
''','Kirshenbaum Bands','Volatility','Compare regression-error bands with an EMA trend baseline.','EMAの基準線に回帰誤差の幅を加えたバンドを比較。','An EMA forms the center. The width is a scaled root mean square of residuals against a rolling linear regression.','中央はEMA。移動線形回帰からの残差の二乗平均平方根に倍率を掛けて幅を決めます。','EMA Length 30, Regression Length 20 and Multiplier 1.75 are defaults.','EMA期間30、回帰期間20、倍率1.75が初期値です。','This plotted width is not a calibrated statistical confidence interval or a probability of reversal.','描画される幅は、確率が校正された信頼区間や反転確率ではありません。')
add('bands_and_channels/mean_absolute_deviation_bands.pine','7c4a3c05489dd9646c9b23fa4aa748cb8631fe05','''//@version=4
// Copyright (c) 2020-present, Alex Orekhov (everget)
// Mean Absolute Deviation Bands script may be freely distributed under the terms of the GPL-3.0 license.
study("Mean Absolute Deviation Bands", shorttitle="MADB", overlay=true)

length = input(title="Length", defval=20, minval=2)
mult = input(title="Bands Multiplier", defval=2.0, type=input.float, step=0.1)
src = input(title="Source", defval=close)

basis = sma(src, length)
dev = mult * dev(src, length)
upper = basis + dev
lower = basis - dev

plot(basis, title="Basis", color=#351c75, transp=0)
upperPlot = plot(upper, title="Upper", color=#45818e, transp=0)
lowerPlot = plot(lower, title="Lower", color=#45818e, transp=0)
fill(upperPlot, lowerPlot, title="MADB Background", color=color.new(#ffd966, 84))
''','Mean Absolute Deviation Bands','Volatility','Use average absolute deviation instead of standard deviation for band width.','標準偏差の代わりに平均絶対偏差を使うバンド。','Plots an SMA plus and minus the mean absolute deviation multiplied by a width setting.','単純移動平均の上下に、平均絶対偏差×倍率の幅を表示します。','Length 20 and Bands Multiplier 2.0 are defaults. Compare with a standard-deviation band over the same window.','初期値は期間20、倍率2.0。同じ期間の標準偏差バンドと比べる用途に使えます。','MAD here means mean absolute deviation, not median absolute deviation.','ここでのMADは平均絶対偏差であり、中央値絶対偏差ではありません。')
add('bands_and_channels/moving_average_channel.pine','dd7d52b02fcc095090abaea43a3a452dfcb510de','''//@version=4
// Copyright (c) 2017-present, Alex Orekhov (everget)
// Moving Average Channel script may be freely distributed under the terms of the GPL-3.0 license.
study("Moving Average Channel", shorttitle="MAC", overlay=true)

upperSrc = input(title="Upper Source", type=input.source, defval=high)
upperLength = input(title="Upper Length", type=input.integer, defval=20)
upperOffset = input(title="Upper Offset", type=input.integer, defval=0)

upper = sma(upperSrc, upperLength)
upperPlot = plot(upper, title="Upper", color=#3c78d8, offset=upperOffset, transp=0)

lowerSrc = input(title="Lower Source", type=input.source, defval=low)
lowerLength = input(title="Lower Length", type=input.integer, defval=20)
lowerOffset = input(title="Lower Offset", type=input.integer, defval=0)

lower = sma(lowerSrc, lowerLength)
lowerPlot = plot(lower, title="Lower", color=#f57c00, offset=lowerOffset, transp=0)

fill(upperPlot, lowerPlot, title="Background", color=color.new(#ffd966, 90))

barColor = close > upper ? color.lime : close < lower ? color.red : color.gray
barcolor(barColor, title="Bar Color")
''','Moving Average Channel','Trend','Locate price above, inside or below a smoothed high/low channel.','高値・安値の平均で作るチャネルに対する価格位置を表示。','The upper and lower boundaries have separate SMA sources, periods and visual offsets. Candle colors compare close with the unshifted calculated boundaries.','上限・下限それぞれに平均する価格、期間、描画シフトを設定。足の色はシフトしていない計算値と終値を比較します。','Both periods default to 20 and offsets to zero. Keep offsets at zero for a direct visual comparison with candle colors.','上下とも期間20、シフト0が初期値。足の色と位置を直接比較する場合はシフト0を保ちます。','A visual offset moves a drawing; it does not add future information. Colors and shifted lines can appear misaligned.','描画シフトは未来の情報を追加しません。シフトした線と足の色は位置がずれて見える場合があります。')
add('bands_and_channels/stoller_average_range_channels.pine','a9035eb28b38295d5c612f965a06417cc7f1062d','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Stoller Average Range Channels (STARC) Bands script may be freely distributed under the terms of the GPL-3.0 license.
study("Stoller Average Range Channels (STARC) Bands", shorttitle="STARC", overlay=true)

length = input(title="Length", type=integer, minval=1, defval=6)
maInput = input(title="MA", defval="SMA", options=["EMA", "SMA", "VWMA", "WMA"])
atrLength = input(title="ATR Length", type=integer, minval=1, defval=15)
mult = input(title="Multiplier", type=float, step=0.1, defval=1.33)
src = input(title="Source", type=source, defval=close)

basis = iff(maInput == "EMA", ema(src, length),
	 iff(maInput == "SMA", sma(src, length),
	 iff(maInput == "VWMA", vwma(src, length),
	 iff(maInput == "WMA", wma(src, length),
	 na))))

upperBand = basis + atr(length) * mult
lowerBand = basis - atr(length) * mult

plot(upperBand, title="Upper", linewidth=2, color=blue, transp=0)
plot(basis, title="Basis", linewidth=2, color=#6d1e7f, transp=0)
plot(lowerBand, title="Lower", linewidth=2, color=red, transp=0)
''','STARC Bands — Original Source','Volatility','Study an ATR envelope with a choice of moving-average baseline.','基準線の種類を選べるATRチャネルの原本。','The center supports SMA, EMA, VWMA or WMA. Width uses ATR(length) times Multiplier in the actual source.','中央はSMA・EMA・VWMA・WMAから選択。実際の原本の幅計算はATR(length)×倍率です。','Length defaults to 6 and Multiplier to 1.33. The separate ATR Length input defaults to 15 but is unused.','期間6、倍率1.33が初期値。別のATR Length入力は初期値15ですが計算に使われていません。','Known source defect: changing ATR Length has no effect. The original is preserved for inspection, not silently fixed.','既知の不具合：ATR Lengthを変えても結果に反映されません。検証用に原本を保持し、無断で修正版に置き換えていません。')
add('bands_and_channels/vortex_bands.pine','a3f91038e7b75fd58828cb10df228a266308224d','''//@version=4
// Copyright (c) 2020-present, Alex Orekhov (everget)
// Vortex Bands script may be freely distributed under the terms of the GPL-3.0 license.
study("Vortex Bands", shorttitle="VB", overlay=true)

length = input(title="Length", type=input.integer, defval=20)
mult = input(title="Multiplier", type=input.float, step=0.1, defval=2)
src = input(title="Source", type=input.source, defval=hlc3)
barColoringType = input(title="Bar Coloring", defval="None", options=["None", "Upper > Lower", "Close Above/Below Basis", "Close Inside Cloud", "Wicks Inside Cloud"])

_ema(src, alpha) =>
    out = src
    out := alpha * out + (1 - alpha) * nz(out[1], out)
    out

_mnma(src, length) =>
    alpha = 2 / (length + 1)
    ema1 = _ema(src, alpha)
    ema2 = _ema(ema1, alpha)
    out = ((2 - alpha) * ema1 - ema2) / (1 - alpha)
    out

basis = _mnma(src, length)
dev = mult * _mnma(src - basis, length)

upper = basis + dev
lower = basis - dev

plot(basis, title="Basis", color=color.maroon, transp=0)
upperBandPlot = plot(upper, title="Upper", linewidth=2, color=color.blue)
lowerBandPlot = plot(lower, title="Lower", linewidth=2, color=color.orange)
fill(upperBandPlot, lowerBandPlot, title="Background", color=color.new(#ffd966, 90))

barColor =
     barColoringType == "Upper > Lower" ? (upper > lower ? color.lime : color.red) :
     barColoringType == "Close Above/Below Basis" ? (close > basis ? color.lime : color.red) :
     barColoringType == "Close Inside Cloud" ? (min(upper, lower) < close and close < max(upper, lower) ? color.lime : color.red) :
     barColoringType == "Wicks Inside Cloud" ? (min(upper, lower) < low and high < max(upper, lower) ? color.lime : color.red) :
     na

barcolor(barColor, title="Bar Color")
''','Vortex Bands','Trend','Inspect a signed-deviation cloud with optional candle coloring.','符号付きの偏差を使う雲と、足の色分けを観察。','A two-stage exponential filter forms the basis and smooths the signed source-minus-basis difference. The two boundaries can cross.','二段の指数平滑化で中心線と価格差を計算。差の符号を残すため上下の境界線が交差する場合があります。','Length 20, Multiplier 2 and Source HLC3 are defaults. Select a coloring rule separately.','期間20、倍率2、HLC3が初期値。色分けルールは別に選択します。','This is not a standard deviation envelope or the VI+/VI− Vortex oscillator. Length 1 creates a zero denominator.','標準偏差バンドやVI+/VI−のVortexオシレーターではありません。期間1では分母がゼロになります。')
add('movings/double_exponential_moving_average.pine','877d564547af98e2ce09a91a9bb7b044258b0e76','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Double Exponential Moving Average script may be freely distributed under the terms of the GPL-3.0 license.
study("Double Exponential Moving Average", shorttitle="DEMA", overlay=true)

length = input(title="Length", type=integer, minval=1, defval=14)
src = input(title="Source", type=source, defval=close)

dema(src, length) =>
	ema1 = ema(src, length)
	ema2 = ema(ema1, length)
	dema = 2 * ema1 - ema2

plot(dema(src, length), title="DEMA", linewidth=2, color=#6d1e7f, transp=0)
''','Double Exponential Moving Average','Trend','Compare DEMA with a conventional EMA at the same period.','同じ期間のEMAとDEMAの反応差を比較。','Calculates 2×EMA(source) minus EMA(EMA(source)). It is not simply an EMA applied twice.','2×EMAからEMAのEMAを引きます。単にEMAを二回掛ける計算ではありません。','Original length is 14; Source defaults to Close.','原本の期間は14、価格は終値が初期値です。','Reducing lag can also amplify overshoot and false turns.','遅れが減っても、行き過ぎや細かな反転が増える場合があります。')
add('movings/double_weighted_moving_average.pine','7cc13e1877bcaaa01dd56321727c598279c88fce','''//@version=3
// Copyright (c) 2019-present, Alex Orekhov (everget)
// Double Weighted Moving Average script may be freely distributed under the terms of the GPL-3.0 license.
study("Double Weighted Moving Average", shorttitle="DWMA", overlay=true)

length = input(title="Length", type=integer, defval=10)
highlightMovements = input(title="Highlight Movements ?", type=bool, defval=true)
src = input(title="Source", type=source, defval=close)

dwma = wma(wma(src, length), length)

dwmaColor = highlightMovements ? (dwma > dwma[1] ? green : red) : #6d1e7f
plot(dwma, title="DWMA", linewidth=2, color=dwmaColor, transp=0)
''','Double Weighted Moving Average','Trend','Smooth a price series with two sequential weighted averages.','加重移動平均を二段に掛けて価格を平滑化。','Applies WMA twice with the same length and optionally colors the result by its one-bar slope.','同じ期間のWMAを二回適用し、必要に応じて一つ前の足との傾きで色分けします。','Length starts at 10; Highlight Movements is enabled. Use a positive length.','期間10、傾きの色分けが初期設定。期間は正の値を使います。','This DWMA differs from Distance Weighted Moving Average, which shares the abbreviation.','同じ略称のDistance Weighted Moving Averageとは別の計算です。')
add('movings/ahrens_moving_average.pine','9ed91f942a776c0837c9e6bcb41a796fd64f508f','''//@version=4
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Ahrens Moving Average script may be freely distributed under the terms of the GPL-3.0 license.
study("Ahrens Moving Average", shorttitle="AHMA", overlay=true)

length = input(title="Length", type=input.integer, defval=9)
src = input(title="Source", type=input.source, defval=close)
highlight = input(title="Highlight ?", type=input.bool, defval=true)

ahma = 0.0
ahma1 = nz(ahma[1])
ahma := ahma1 + (src - (ahma1 + nz(ahma[length])) / 2) / length

ahmaColor = highlight ? ahma > ahma[1] ? color.green : color.red : #6d1e7f
plot(ahma, title="AHMA", linewidth=2, color=ahmaColor, transp=0)
''','Ahrens Moving Average','Trend','Explore a recursive average with a delayed-average correction.','過去の平均値を使って補正する再帰型平均線の研究用。','Updates the previous average using the current source and the midpoint of the previous and length-bars-old average.','前回値と指定本数前の平均の中間点を基準に、現在の価格を使って平均値を更新します。','Length defaults to 9. Keep it positive and allow a substantial warm-up period.','期間9が初期値。正の期間を使い、十分な計算準備期間を取ります。','Zero initialization and loaded history affect early values; changing history can change the warm-up segment.','ゼロ初期化と読み込んだ履歴が初期値に影響します。履歴を増やすと開始付近の値が変わる場合があります。')
add('movings/adaptive_rsi_moving_average.pine','191cf355a1744ed469cd9a5e506d0646be31085a','''//@version=4
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Adaptive RSI Moving Average script may be freely distributed under the terms of the GPL-3.0 license.
study("Adaptive RSI Moving Average", shorttitle="ARSIMA", overlay=true)

length = input(title="Length", type=input.integer, defval=14)
src = input(title="Source", type=input.source, defval=close)
highlight = input(title="Highlight ?", type=input.bool, defval=true)

alpha = 2 * abs(rsi(src, length) / 100 - 0.5)

arsima = 0.0
arsima := alpha * src + (1 - alpha) * nz(arsima[1])

arsimaColor = highlight ? arsima > arsima[1] ? color.green : color.red : #6d1e7f
plot(arsima, title="ARSIMA", linewidth=2, color=arsimaColor, transp=0)
''','Adaptive RSI Moving Average','Trend','Study a trend line whose response changes with RSI distance from 50.','RSIが50から離れるほど反応を変える平均線を研究。','The smoothing weight is 2×abs(RSI/100−0.5). RSI near 50 yields a small weight; stronger directional readings increase it.','平滑化係数は2×abs(RSI/100−0.5)。RSIが50付近では小さく、片側へ偏るほど大きくなります。','Length defaults to 14; price source is configurable. Allow the recursive calculation to warm up.','期間14が初期値で、入力価格を変更できます。再帰計算の準備期間を取ります。','The average begins from zero in the original. An adaptive response is not evidence of better forecasting.','原本はゼロから初期化します。適応的な反応でも予測力が高い証拠にはなりません。')
add('movings/distance_weighted_moving_average.pine','76acac31ccf16e7ccdf6112a36918140526274cc','''//@version=3
// Copyright (c) 2019-present, Alex Orekhov (everget)
// Distance Weighted Moving Average script may be freely distributed under the terms of the GPL-3.0 license.
study("Distance Weighted Moving Average", shorttitle="DWMA", overlay=true)

length = input(title="Length", type=integer, defval=14)
highlightMovements = input(title="Highlight Movements ?", type=bool, defval=true)
src = input(title="Source", type=source, defval=close)

sum = 0.0
weightSum = 0.0

calcWeight(src, length, i) =>
    distanceSum = 0.0
    for j = 0 to length - 1
        distanceSum := distanceSum + abs(nz(src[i]) - nz(src[j]))
    1 / distanceSum

for i = 0 to length - 1
    weight = calcWeight(src, length, i)
    sum := sum + nz(src[i]) * weight
    weightSum := weightSum + weight

dwma = sum / weightSum

dwmaColor = highlightMovements ? (dwma > dwma[1] ? green : red) : #6d1e7f
plot(dwma, title="DWMA", linewidth=2, color=dwmaColor, transp=0)
''','Distance Weighted Moving Average','Research','Inspect an average weighted by price proximity rather than time.','時系列の新しさではなく価格同士の近さで加重する平均。','Each sample receives inverse total absolute distance to all other samples in the window; weighted prices are then normalized.','各価格と窓内の全価格との絶対差合計の逆数を重みにし、加重合計を正規化します。','Length defaults to 14. Keep windows modest because the nested loops scale quadratically.','期間14が初期値。二重ループで計算量が増えるため期間を過度に大きくしません。','Known edge case: identical prices or Length 1 produce zero distances and division by zero.','既知の境界条件：同じ価格が並ぶ場合や期間1では、距離ゼロによるゼロ除算が起こります。')
add('movings/elastic_volume_weighted_moving_average.pine','c4d09a7a7fee58380096f9b56ac22ff2080e5255','''//@version=4
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Elastic Volume Weighted Moving Average script may be freely distributed under the terms of the GPL-3.0 license.
study("Elastic Volume Weighted Moving Average", shorttitle="EVWMA", overlay=true)

length = input(title="Length", type=input.integer, defval=14)
src = input(title="Source", type=input.source, defval=close)
highlight = input(title="Highlight ?", type=input.bool, defval=true)

volumeSum = sum(volume, length)

evwma = 0.0
evwma := ((volumeSum - volume) * nz(evwma[1]) + volume * src) / volumeSum

evwmaColor = highlight ? evwma > evwma[1] ? color.green : color.red : #6d1e7f
plot(evwma, title="EVWMA", linewidth=2, color=evwmaColor, transp=0)
''','Elastic Volume Weighted Moving Average','Volume','Let relative current-bar volume control a recursive average.','直近出来高に占める現在足の比率で平均線の反応を変える。','Blends the previous average and current price using current volume divided by the rolling volume total.','現在出来高÷期間合計出来高を使い、前回の平均と現在価格を配分します。','Length 14 is the default. Confirm volume availability before interpreting the result.','期間14が初期値。結果を読む前に出来高が存在するか確認します。','Zero or missing volume can break the calculation. FX/CFD volume may be broker-specific tick volume, not consolidated traded volume.','出来高ゼロや欠落で計算できない場合があります。FX・CFDでは集約売買高ではなく配信元固有のティック出来高の場合があります。')
add('movings/alpha_decreasing_exponential_moving_average.pine','e799dbe5f78ae2a9b9f6924e9d0a445447dd323f','''//@version=4
// Copyright (c) 2019-present, Alex Orekhov (everget)
// Alpha-Decreasing Exponential Moving Average script may be freely distributed under the terms of the GPL-3.0 license.
study("Alpha-Decreasing Exponential Moving Average", shorttitle="ADEMA", overlay=true)

alpha = 2 / (int(bar_index) + 1)

ema = close
ema := alpha * ema + (1 - alpha) * nz(ema[1], ema)

plot(ema, title="ADEMA", linewidth=2, color=color.orange)
''','Alpha-Decreasing EMA','Research','Explore an average whose smoothing weight shrinks across loaded history.','読み込んだ履歴の経過とともに平滑化係数が小さくなる平均。','Uses alpha=2/(bar_index+1) instead of a fixed lookback period. The weight therefore depends on where chart history starts.','固定期間の代わりにalpha=2/(bar_index+1)を使用。チャート履歴の開始位置が係数に影響します。','There are no input settings in this original. Compare charts with different loaded history to understand the dependence.','原本に設定項目はありません。履歴の長さが異なるチャートで計算の依存性を比較します。','Not a fixed-period EMA. Reloaded or expanded history can change the entire trajectory.','固定期間のEMAではありません。履歴の再読込・追加により軌跡全体が変化する可能性があります。')
add('movings/ehlers_super_smoother_filter.pine','ca57d8231844027fd01096ff109ca19e051f6831','''//@version=3
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Ehlers Super Smoother Filter script may be freely distributed under the terms of the GPL-3.0 license.
study("Ehlers Super Smoother Filter", shorttitle="ESSF", overlay=true)

length = input(title="Length", type=integer, minval=1, defval=15)
numberOfPoles = input(title="Number of Poles", type=integer, defval=2, options=[2, 3])
src = input(title="Source", type=source, defval=close)

PI = 2 * asin(1)

get2PoleSSF(src, length) =>
	arg = sqrt(2) * PI / length
	a1 = exp(-arg)
	b1 = 2 * a1 * cos(arg)
	c2 = b1
	c3 = -pow(a1, 2)
	c1 = 1 - c2 - c3

	ssf = 0.0
	ssf := c1 * src + c2 * nz(ssf[1]) + c3 * nz(ssf[2])

get3PoleSSF(src, length) =>
	arg = PI / length
	a1 = exp(-arg)
	b1 = 2 * a1 * cos(1.738 * arg)
	c1 = pow(a1, 2)

	coef2 = b1 + c1
	coef3 = -(c1 + b1 * c1)
	coef4 = pow(c1, 2)
	coef1 = 1 - coef2 - coef3 - coef4

	ssf = 0.0
	ssf := coef1 * src + coef2 * nz(ssf[1]) + coef3 * nz(ssf[2]) + coef4 * nz(ssf[3])

essf = numberOfPoles == 2
		 ? get2PoleSSF(src, length)
		 : get3PoleSSF(src, length)

plot(essf, title="ESSF", linewidth=2, color=#741b47, transp=0)
''','Ehlers Super Smoother','Trend','Compare two- and three-pole recursive smoothing on price.','2極・3極の再帰フィルターによる価格の平滑化を比較。','Derives recursive filter coefficients from the selected length and pole count, using current input and previous outputs.','期間と極数から再帰係数を求め、現在の価格と過去の出力から線を計算します。','Length 15 and two poles are defaults; the three-pole option changes the recurrence.','初期値は期間15・2極。3極を選ぶと再帰式が変わります。','Initial output uses zero-filled missing values. Discard warm-up before evaluating a filter-based strategy.','欠損する過去値はゼロで埋めます。戦略評価では開始直後の準備期間を除いて確認します。')
add('movings/butterworth_filter.pine','5b51f1087c90382a99c1abedf0757cf8388060d5','''//@version=4
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Butterworth Filter script may be freely distributed under the terms of the GPL-3.0 license.
study("Butterworth Filter", shorttitle="BF", overlay=true)

length = input(title="Length", type=input.integer, minval=1, defval=14)
poles = input(title="Poles", type=input.integer, defval=2, options=[2, 3])
src = input(title="Source", type=input.source, defval=close)
highlight = input(title="Highlight ?", type=input.bool, defval=true)

PI = 2 * asin(1)

_bf2(src, length) =>
	a = exp(-sqrt(2) * PI / length)
	b = 2 * a * cos(sqrt(2) * PI / length)

	src1 = nz(src[1], src)
	src2 = nz(src[2], src1)

	bf = 0.0
	bf1 = nz(bf[1], src)
	bf2 = nz(bf[2], bf1)

	bf :=
		 b * bf1 -
		 pow(a, 2) * bf2 +
		 (1 - b + pow(a, 2)) / 4 * (src + 2 * src1 + src2)
	bf

_bf3(src, length) =>
	a = exp(-PI / length)
	b = 2 * a * cos(1.738 * PI / length)
	c = pow(a, 2)

	src1 = nz(src[1], src)
	src2 = nz(src[2], src1)
	src3 = nz(src[3], src2)

	bf = 0.0
	bf1 = nz(bf[1], src)
	bf2 = nz(bf[2], bf1)
	bf3 = nz(bf[3], bf2)

	bf :=
		 (b + c) * bf1 -
		 (c + b * c) * bf2 +
		 pow(c, 2) * bf3 +
		 (1 - b + c) * (1 - c) / 8 * (src + 3 * src1 + 3 * src2 + src3)
	bf

bf = poles == 2
	 ? _bf2(src, length)
	 : _bf3(src, length)

bfColor = highlight ? bf > bf[1] ? color.green : color.red : #6d1e7f
plot(bf, title="BF", linewidth=2, color=bfColor, transp=0)
''','Butterworth Filter','Trend','Study a recursive low-pass filter with slope coloring.','傾きの色分け付き再帰ローパスフィルターを研究。','Combines weighted recent inputs and previous outputs using two- or three-pole Butterworth-style coefficients.','直近の入力価格と過去の出力値を、2極または3極の係数で組み合わせます。','Length 14, two poles and highlighting enabled are defaults.','初期値は期間14・2極・傾き色分け有効です。','Smoothing creates delay; color changes on an unfinished bar may change with price.','平滑化には遅れがあります。未確定足の色は価格更新で変化する場合があります。')
add('movings/adaptive_laguerre_filter.pine','cecfb72f710af00b6f480b17d113c7f77fb3a5bc','''//@version=4
// Copyright (c) 2018-present, Alex Orekhov (everget)
// Adaptive Laguerre Filter script may be freely distributed under the terms of the GPL-3.0 license.
study("Adaptive Laguerre Filter", shorttitle="ALF", overlay=true)

length = input(title="Length", type=input.integer, defval=14)
medianLength = input(title="Median Length", type=input.integer, defval=5)
src = input(title="Source", type=input.source, defval=close)
highlight = input(title="Highlight ?", type=input.bool, defval=true)
awaitBarConfirmation = input(title="Await Bar Confirmation ?", type=input.bool, defval=true)

_median(src, length) =>
	percentile_nearest_rank(src, length, 50)

alf = 0.0

diff = abs(src - nz(alf[1], src))

HH = 0.0
HH := diff

LL = 0.0
LL := diff

for i = 0 to length - 1
	if nz(diff[i]) > HH
		HH := nz(diff[i])
		HH

	if nz(diff[i]) < LL
		LL := nz(diff[i])
		LL

alpha = 0.0
alpha := HH - LL != 0.0 ? _median((diff - LL) / (HH - LL), medianLength) : nz(alpha[1], 2 / (length + 1))
alpha2 = 1 - alpha

L0 = 0.0
L0 := alpha * src + alpha2 * nz(L0[1], src)

L1 = 0.0
L1 := nz(L0[1], src) + alpha2 * (nz(L1[1], src) - L0)

L2 = 0.0
L2 := nz(L1[1], src) + alpha2 * (nz(L2[1], src) - L1)

L3 = 0.0
L3 := nz(L2[1], src) + alpha2 * (nz(L3[1], src) - L2)

alf := (L0 + 2 * L1 + 2 * L2 + L3) / 6

await = awaitBarConfirmation ? barstate.isconfirmed : true

alfColor = highlight ? (alf > alf[1] and await ? color.green : color.red) : #6d1e7f
plot(alf, title="ALF", linewidth=2, color=alfColor, transp=0)

alertCond = alfColor != alfColor[1] and await
alertcondition(alertCond, title="Color Change", message="ALF has changed its color!")
''','Adaptive Laguerre Filter','Trend','Explore adaptive smoothing with a configurable color-change alert.','適応型平滑化と色変化アラートを検証。','Normalizes recent price-to-filter differences, takes a median-derived weight, and runs four recursive Laguerre stages.','価格とフィルターの差を正規化し、その中央値から係数を求め、四段の再帰計算を行います。','Length 14, Median Length 5 and Await Bar Confirmation enabled are defaults. Create the alert explicitly in TradingView.','期間14、中央値期間5、確定待ち有効が初期値。アラート自体はTradingViewで作成します。','The confirmation option gates color/alerts, not the underlying live calculation. It is not a blanket non-repainting certification.','確定待ちは色とアラートの条件に作用し、計算自体を固定しません。非リペイントを全面保証する機能ではありません。')
add('highlighters/range_candles.pine','675861b7bcbff76b8523d2044f0c307a978e1715','''//@version=4
// Copyright (c) 2020-present, Alex Orekhov (everget)
// Range Candles script may be freely distributed under the terms of the GPL-3.0 license.
study("Range Candles", overlay=true)

var color bullColor = input(title="Bull Color", defval=#26a69a)
var color bearColor = input(title="Bear Color", defval=#ef5350)
candleColor = close >= open ? bullColor : bearColor

plotcandle(
	 open,
	 high,
	 low,
	 close,
	 title="",
	 color=candleColor,
	 bordercolor=candleColor,
	 wickcolor=candleColor
	 )
''','Range Candles — OHLC Renderer','Chart tools','Use a small source example for consistent candle, border and wick colors.','足・枠・ヒゲの色を揃える小さな描画サンプル。','Redraws the existing chart OHLC. Close greater than or equal to Open selects the bullish color. It does not construct range bars.','チャートにあるOHLCを描き直します。終値が始値以上なら陽線色を使用。値幅足を生成するコードではありません。','Only bullish and bearish colors are inputs. Check overlap with the chart’s original candles.','設定は陽線色・陰線色のみ。元のチャート足との重なりを確認します。','Despite the title, this is a candle renderer, not a new range-chart calculation or trading signal.','名前にRangeとありますが、ローソク足の描画サンプルで、値幅チャートの計算や売買シグナルではありません。')

if __name__=='__main__':
    g=Path('/usr/share/common-licenses/GPL-3').read_bytes();assert blob(g)=='f288702d2fa16d3cdf0035b15a9fcbc552cd88e7'
    (OUT/'licenses/GPL-3.0.txt').write_bytes(g)
    assert blob(MIT.encode())=='0c89a10691806014181b818c55ac3b5784683a16'
    (OUT/'licenses/MIT-James-Bachini.txt').write_text(MIT)
    (BASE/'bundled_catalog.json').write_text(json.dumps(DATA,ensure_ascii=False,indent=2))
    print('Verified original source bytes:',len(DATA))
