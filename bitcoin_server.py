import os
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import requests
import time
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# HTML 템플릿
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>비트코인 실시간 매매 분석기</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; margin-bottom: 30px; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .status { text-align: center; margin-bottom: 20px; padding: 15px; border-radius: 10px; font-weight: bold; }
        .connected { background: rgba(0, 255, 136, 0.2); border: 1px solid #00ff88; }
        .error { background: rgba(255, 71, 87, 0.2); border: 1px solid #ff4757; }
        .price-display {
            text-align: center; margin-bottom: 30px; padding: 20px;
            background: rgba(255,255,255,0.1); border-radius: 15px; backdrop-filter: blur(10px);
        }
        .current-price {
            font-size: 3em; font-weight: bold; color: #00ff88;
            text-shadow: 0 0 20px rgba(0,255,136,0.5);
        }
        .price-change { font-size: 1.2em; margin-top: 10px; }
        .signals-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }
        .signal-card {
            background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px;
            backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);
        }
        .signal-title { font-size: 1.3em; margin-bottom: 15px; color: #ffd700; }
        .signal-value { font-size: 1.5em; font-weight: bold; margin-bottom: 10px; }
        .signal-status {
            padding: 8px 15px; border-radius: 20px; font-weight: bold;
            text-align: center; margin-top: 10px;
        }
        .buy-signal { background: linear-gradient(45deg, #00ff88, #00cc6a); color: #000; animation: pulse 2s infinite; }
        .sell-signal { background: linear-gradient(45deg, #ff4757, #ff3838); color: #fff; animation: pulse 2s infinite; }
        .hold-signal { background: linear-gradient(45deg, #ffa726, #ff9800); color: #000; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
        .chart-container { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; margin-bottom: 30px; backdrop-filter: blur(10px); }
        .analysis-summary { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 25px; text-align: center; backdrop-filter: blur(10px); }
        .final-recommendation { font-size: 2em; font-weight: bold; margin-bottom: 15px; padding: 20px; border-radius: 10px; }
        .recommendation-buy { background: linear-gradient(45deg, #00ff88, #00cc6a); color: #000; }
        .recommendation-sell { background: linear-gradient(45deg, #ff4757, #ff3838); color: #fff; }
        .recommendation-hold { background: linear-gradient(45deg, #ffa726, #ff9800); color: #000; }
        .update-time { text-align: center; margin-top: 20px; opacity: 0.7; }
        .live-indicator { display: inline-block; width: 12px; height: 12px; background: #00ff88; border-radius: 50%; margin-right: 8px; animation: blink 2s infinite; }
        @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0.3; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 비트코인 실시간 매매 분석기</h1>
        <div id="status" class="status"><span class="live-indicator"></span>서버 연결 확인 중...</div>
        <div class="price-display">
            <div class="current-price" id="currentPrice">연결 중...</div>
            <div class="price-change" id="priceChange">데이터 로딩 중...</div>
        </div>
        <div class="signals-grid">
            <div class="signal-card">
                <div class="signal-title">📈 RSI</div>
                <div class="signal-value" id="rsiValue">-</div>
                <div class="signal-status" id="rsiStatus">분석 중...</div>
            </div>
            <div class="signal-card">
                <div class="signal-title">📊 MACD</div>
                <div class="signal-value" id="macdValue">-</div>
                <div class="signal-status" id="macdStatus">분석 중...</div>
            </div>
            <div class="signal-card">
                <div class="signal-title">🌊 볼린저 밴드</div>
                <div class="signal-value" id="bbValue">-</div>
                <div class="signal-status" id="bbStatus">분석 중...</div>
            </div>
            <div class="signal-card">
                <div class="signal-title">📉 이동평균선</div>
                <div class="signal-value" id="maValue">-</div>
                <div class="signal-status" id="maStatus">분석 중...</div>
            </div>
            <div class="signal-card">
                <div class="signal-title">⚡ 스토캐스틱</div>
                <div class="signal-value" id="stochValue">-</div>
                <div class="signal-status" id="stochStatus">분석 중...</div>
            </div>
            <div class="signal-card">
                <div class="signal-title">📊 거래량</div>
                <div class="signal-value" id="volumeValue">-</div>
                <div class="signal-status" id="volumeStatus">분석 중...</div>
            </div>
        </div>
        <div class="chart-container">
            <canvas id="priceChart" width="400" height="200"></canvas>
        </div>
        <div class="analysis-summary">
            <div class="final-recommendation" id="finalRecommendation">분석 중...</div>
            <div id="analysisText">실시간 데이터를 분석하고 있습니다...</div>
        </div>
        <div class="update-time" id="updateTime">마지막 업데이트: -</div>
    </div>

    <script>
        let priceChart;
        
        function initChart() {
            const ctx = document.getElementById('priceChart').getContext('2d');
            priceChart = new Chart(ctx, {
                type: 'line', data: { labels: [], datasets: [{ label: 'BTC 가격 ($)', data: [],
                borderColor: '#00ff88', backgroundColor: 'rgba(0, 255, 136, 0.1)', borderWidth: 2, fill: true, tension: 0.4 }] },
                options: { responsive: true, scales: { y: { beginAtZero: false, grid: { color: 'rgba(255, 255, 255, 0.1)' },
                ticks: { color: 'white', callback: function(value) { return '$' + value.toLocaleString(); } } },
                x: { grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: 'white' } } },
                plugins: { legend: { labels: { color: 'white' } } } }
            });
        }

        async function fetchData() {
            try {
                const response = await fetch('/api/bitcoin');
                const data = await response.json();
                
                if (data.status === 'error') throw new Error(data.error);
                
                document.getElementById('status').className = 'status connected';
                document.getElementById('status').innerHTML = '<span class="live-indicator"></span><strong>✅ 실시간 연결됨</strong> - 바이낸스 & CoinGecko API';
                
                document.getElementById('currentPrice').textContent = '$' + data.current_price.toLocaleString();
                const changeText = (data.price_change_24h > 0 ? '+' : '') + data.price_change_24h.toFixed(2) + '%';
                document.getElementById('priceChange').textContent = '24시간: ' + changeText;
                document.getElementById('priceChange').style.color = data.price_change_24h > 0 ? '#00ff88' : '#ff4757';
                
                if (data.chart_data && priceChart) {
                    const prices = data.chart_data.map(p => p[1]);
                    const labels = data.chart_data.map((p, i) => i + 'h');
                    priceChart.data.labels = labels;
                    priceChart.data.datasets[0].data = prices;
                    priceChart.update('none');
                }
                
                if (data.analysis) updateAnalysis(data.analysis);
                document.getElementById('updateTime').textContent = '마지막 업데이트: ' + new Date().toLocaleTimeString();
                
            } catch (error) {
                document.getElementById('status').className = 'status error';
                document.getElementById('status').innerHTML = '<strong>❌ 연결 실패</strong><br>' + error.message;
                document.getElementById('currentPrice').textContent = '연결 실패';
            }
        }

        function updateAnalysis(analysis) {
            document.getElementById('rsiValue').textContent = analysis.rsi.value;
            document.getElementById('rsiStatus').textContent = analysis.rsi.signal;
            document.getElementById('rsiStatus').className = 'signal-status ' + analysis.rsi.class;
            
            document.getElementById('macdValue').textContent = analysis.macd.value;
            document.getElementById('macdStatus').textContent = analysis.macd.signal;
            document.getElementById('macdStatus').className = 'signal-status ' + analysis.macd.class;
            
            document.getElementById('bbValue').textContent = analysis.bb.value;
            document.getElementById('bbStatus').textContent = analysis.bb.signal;
            document.getElementById('bbStatus').className = 'signal-status ' + analysis.bb.class;
            
            document.getElementById('maValue').textContent = analysis.ma.value;
            document.getElementById('maStatus').textContent = analysis.ma.signal;
            document.getElementById('maStatus').className = 'signal-status ' + analysis.ma.class;
            
            document.getElementById('stochValue').textContent = analysis.stoch.value;
            document.getElementById('stochStatus').textContent = analysis.stoch.signal;
            document.getElementById('stochStatus').className = 'signal-status ' + analysis.stoch.class;
            
            document.getElementById('volumeValue').textContent = analysis.volume.value;
            document.getElementById('volumeStatus').textContent = analysis.volume.signal;
            document.getElementById('volumeStatus').className = 'signal-status ' + analysis.volume.class;
            
            document.getElementById('finalRecommendation').textContent = analysis.final.recommendation;
            document.getElementById('finalRecommendation').className = 'final-recommendation ' + analysis.final.class;
            document.getElementById('analysisText').textContent = analysis.final.text;
        }

        document.addEventListener('DOMContentLoaded', function() {
            initChart();
            fetchData();
            setInterval(fetchData, 30000);
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/bitcoin')
def get_bitcoin_data():
    try:
        # 1. CoinGecko API - 현재 가격
        price_response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true",
            timeout=10
        )
        price_data = price_response.json()
        
        current_price = price_data['bitcoin']['usd']
        price_change_24h = price_data['bitcoin']['usd_24h_change']
        volume_24h = price_data['bitcoin']['usd_24h_vol']
        
        # 2. CoinGecko API - 차트 데이터
        chart_response = requests.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1&interval=hourly",
            timeout=10
        )
        chart_data_full = chart_response.json()
        chart_data = chart_data_full['prices'][-24:]  # 최근 24시간
        
        # 3. 바이낸스 API - OHLCV 데이터
        try:
            binance_response = requests.get(
                "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100",
                timeout=5
            )
            binance_data = binance_response.json()
            
            prices = [float(candle[4]) for candle in binance_data]  # 종가
            volumes = [float(candle[5]) for candle in binance_data]  # 거래량
            highs = [float(candle[2]) for candle in binance_data]    # 고가
            lows = [float(candle[3]) for candle in binance_data]     # 저가
            
        except:
            # 바이낸스 실패시 CoinGecko 데이터 사용
            prices = [p[1] for p in chart_data_full['prices'][-50:]]
            volumes = [v[1] for v in chart_data_full['total_volumes'][-50:]]
            highs = [p * 1.002 for p in prices]  # 근사치
            lows = [p * 0.998 for p in prices]   # 근사치
        
        # 4. 기술적 분석 실행
        analysis = perform_technical_analysis(prices, volumes, highs, lows)
        
        return jsonify({
            'current_price': current_price,
            'price_change_24h': price_change_24h,
            'volume_24h': volume_24h,
            'chart_data': chart_data,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': f'API 연결 실패: {str(e)}',
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500
    except Exception as e:
        return jsonify({
            'error': f'데이터 처리 오류: {str(e)}',
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

def perform_technical_analysis(prices, volumes, highs, lows):
    """기술적 분석 수행"""
    if len(prices) < 30:
        return create_empty_analysis()
    
    # RSI 계산
    rsi_values = calculate_rsi(prices, 14)
    rsi_current = rsi_values[-1]
    
    if rsi_current < 30:
        rsi_signal = '🚀 매수 신호 (과매도)'
        rsi_class = 'buy-signal'
    elif rsi_current > 70:
        rsi_signal = '📉 매도 신호 (과매수)'
        rsi_class = 'sell-signal'
    else:
        rsi_signal = '보유 (중립)'
        rsi_class = 'hold-signal'
    
    # 이동평균선
    ma5 = calculate_ma(prices, 5)
    ma20 = calculate_ma(prices, 20)
    current_price = prices[-1]
    
    if current_price > ma5[-1] and ma5[-1] > ma20[-1]:
        ma_signal = '🚀 매수 신호 (상승)'
        ma_class = 'buy-signal'
    elif current_price < ma5[-1] and ma5[-1] < ma20[-1]:
        ma_signal = '📉 매도 신호 (하락)'
        ma_class = 'sell-signal'
    else:
        ma_signal = '보유 (혼조)'
        ma_class = 'hold-signal'
    
    # 볼린저 밴드
    bb_upper, bb_lower, bb_middle = calculate_bollinger_bands(prices, 20, 2)
    
    if current_price <= bb_lower[-1] * 1.01:
        bb_signal = '🚀 매수 신호 (하단)'
        bb_class = 'buy-signal'
    elif current_price >= bb_upper[-1] * 0.99:
        bb_signal = '📉 매도 신호 (상단)'
        bb_class = 'sell-signal'
    else:
        bb_signal = '보유 (중간)'
        bb_class = 'hold-signal'
    
    # MACD
    macd_line, signal_line = calculate_macd(prices)
    macd_current = macd_line[-1]
    signal_current = signal_line[-1]
    
    if macd_current > signal_current and macd_current > 0:
        macd_signal = '🚀 매수 신호'
        macd_class = 'buy-signal'
    elif macd_current < signal_current and macd_current < 0:
        macd_signal = '📉 매도 신호'
        macd_class = 'sell-signal'
    else:
        macd_signal = '보유'
        macd_class = 'hold-signal'
    
    # 스토캐스틱
    k_values, d_values = calculate_stochastic(highs, lows, prices, 14)
    k_current = k_values[-1]
    d_current = d_values[-1]
    
    if k_current < 20 and d_current < 20:
        stoch_signal = '🚀 매수 신호 (과매도)'
        stoch_class = 'buy-signal'
    elif k_current > 80 and d_current > 80:
        stoch_signal = '📉 매도 신호 (과매수)'
        stoch_class = 'sell-signal'
    else:
        stoch_signal = '보유'
        stoch_class = 'hold-signal'
    
    # 거래량
    avg_volume = sum(volumes[-10:]) / 10
    current_volume = volumes[-1]
    volume_ratio = current_volume / avg_volume
    
    if volume_ratio > 1.5:
        volume_signal = '🔥 거래량 급증'
        volume_class = 'buy-signal'
    else:
        volume_signal = '보통'
        volume_class = 'hold-signal'
    
    # 종합 분석
    signals = [rsi_class, ma_class, bb_class, macd_class, stoch_class]
    buy_count = signals.count('buy-signal')
    sell_count = signals.count('sell-signal')
    
    if buy_count >= 3:
        final_rec = '🚀 강력 매수 추천'
        final_class = 'recommendation-buy'
        final_text = f'{buy_count}개 매수 신호 감지! 적극 매수 고려'
    elif buy_count >= 2:
        final_rec = '📈 매수 고려'
        final_class = 'recommendation-buy'
        final_text = f'{buy_count}개 매수 신호. 신중한 매수'
    elif sell_count >= 3:
        final_rec = '📉 강력 매도 추천'
        final_class = 'recommendation-sell'
        final_text = f'{sell_count}개 매도 신호 감지! 적극 매도 고려'
    elif sell_count >= 2:
        final_rec = '⚠️ 매도 고려'
        final_class = 'recommendation-sell'
        final_text = f'{sell_count}개 매도 신호. 신중한 매도'
    else:
        final_rec = '⏸️ 관망 추천'
        final_class = 'recommendation-hold'
        final_text = '명확한 신호 부족. 관망 권장'
    
    return {
        'rsi': {'value': f'{rsi_current:.1f}', 'signal': rsi_signal, 'class': rsi_class},
        'ma': {'value': f'5MA: {ma5[-1]:.0f} / 20MA: {ma20[-1]:.0f}', 'signal': ma_signal, 'class': ma_class},
        'bb': {'value': f'상: {bb_upper[-1]:.0f} / 하: {bb_lower[-1]:.0f}', 'signal': bb_signal, 'class': bb_class},
        'macd': {'value': f'{macd_current:.2f}', 'signal': macd_signal, 'class': macd_class},
        'stoch': {'value': f'K: {k_current:.1f} / D: {d_current:.1f}', 'signal': stoch_signal, 'class': stoch_class},
        'volume': {'value': f'{current_volume/1000000:.1f}M ({volume_ratio:.1f}배)', 'signal': volume_signal, 'class': volume_class},
        'final': {'recommendation': final_rec, 'class': final_class, 'text': final_text}
    }

def create_empty_analysis():
    return {
        'rsi': {'value': '-', 'signal': '데이터 부족', 'class': 'hold-signal'},
        'ma': {'value': '-', 'signal': '데이터 부족', 'class': 'hold-signal'},
        'bb': {'value': '-', 'signal': '데이터 부족', 'class': 'hold-signal'},
        'macd': {'value': '-', 'signal': '데이터 부족', 'class': 'hold-signal'},
        'stoch': {'value': '-', 'signal': '데이터 부족', 'class': 'hold-signal'},
        'volume': {'value': '-', 'signal': '데이터 부족', 'class': 'hold-signal'},
        'final': {'recommendation': '⏸️ 데이터 로딩 중', 'class': 'recommendation-hold', 'text': '충분한 데이터를 수집하는 중입니다.'}
    }

def calculate_rsi(prices, period):
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    
    rsi = []
    for i in range(period-1, len(gains)):
        avg_gain = sum(gains[i-period+1:i+1]) / period
        avg_loss = sum(losses[i-period+1:i+1]) / period
        
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
    
    return rsi

def calculate_ma(prices, period):
    ma = []
    for i in range(period-1, len(prices)):
        ma.append(sum(prices[i-period+1:i+1]) / period)
    return ma

def calculate_bollinger_bands(prices, period, multiplier):
    ma = calculate_ma(prices, period)
    upper = []
    lower = []
    
    for i in range(period-1, len(prices)):
        std = (sum([(prices[j] - ma[i-period+1])**2 for j in range(i-period+1, i+1)]) / period) ** 0.5
        upper.append(ma[i-period+1] + std * multiplier)
        lower.append(ma[i-period+1] - std * multiplier)
    
    return upper, lower, ma

def calculate_macd(prices):
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    
    macd = [ema12[i] - ema26[i] for i in range(len(ema26))]
    signal = calculate_ema(macd, 9)
    
    return macd, signal

def calculate_ema(prices, period):
    ema = [prices[0]]
    multiplier = 2 / (period + 1)
    
    for i in range(1, len(prices)):
        ema.append((prices[i] * multiplier) + (ema[i-1] * (1 - multiplier)))
    
    return ema

def calculate_stochastic(highs, lows, closes, period):
    k = []
    
    for i in range(period-1, len(closes)):
        highest_high = max(highs[i-period+1:i+1])
        lowest_low = min(lows[i-period+1:i+1])
        
        if highest_high == lowest_low:
            k.append(50)
        else:
            k.append(((closes[i] - lowest_low) / (highest_high - lowest_low)) * 100)
    
    # %D는 %K의 3일 이동평균
    d = []
    for i in range(2, len(k)):
        d.append((k[i] + k[i-1] + k[i-2]) / 3)
    
    return k, d

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 비트코인 실시간 분석기 시작!")
    print(f"📊 서버가 포트 {port}에서 실행됩니다")
    print("⚠️  Ctrl+C로 종료")
    
    app.run(debug=False, host='0.0.0.0', port=port)
