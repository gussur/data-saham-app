from flask import Flask, render_template, request, Response
import pandas as pd
import yfinance as yf
from io import StringIO

app = Flask(__name__)

@app.route('/')
def index():
    # Menampilkan halaman web awal
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    # 1. Ambil input dari user (contoh: "BBCA.JK, BBRI.JK")
    tickers_input = request.form.get('tickers')
    
    # Bersihkan spasi dan pisahkan berdasarkan koma
    tickers = [t.strip().upper() for t in tickers_input.split(',')]
    
    all_data = []
    
    # 2. Looping untuk mengambil data setiap saham
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # Ambil data historis 1 bulan terakhir (bisa diubah sesuai kebutuhan)
            df = stock.history(period="1mo") 
            
            if not df.empty:
                df.reset_index(inplace=True) # Jadikan tanggal sebagai kolom biasa
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d') # Rapikan format tanggal
                df['Symbol'] = ticker # Tambahkan kolom Symbol
                
                # Susun ulang kolom agar Symbol ada di depan
                cols = ['Symbol', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                df = df[cols]
                
                all_data.append(df)
        except Exception as e:
            print(f"Gagal mengambil data {ticker}: {e}")

    # Jika tidak ada data sama sekali
    if not all_data:

    return """
    <div style="text-align:center; margin-top:50px; font-family:Arial;">
        <h3>❌ Gagal mengambil data.</h3>
        <p>Pastikan kode saham benar dan gunakan akhiran .JK (contoh: BBCA.JK).</p>
        <a href="/">Kembali ke Home</a>
    </div>
    """, 400

    # 3. Gabungkan semua data saham menjadi 1 tabel besar
    final_df = pd.concat(all_data, ignore_index=True)

    # 4. Ubah menjadi file CSV dan siapkan untuk didownload
    output = StringIO()
    final_df.to_csv(output, index=False)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=data_saham_gabungan.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)
