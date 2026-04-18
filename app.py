from flask import Flask, render_template, request, Response
import pandas as pd
import yfinance as yf
from io import StringIO
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Fungsi untuk koneksi ke Google Sheets
def simpan_ke_sheets(df, sheet_name):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('google-key.json', scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open(sheet_name).sheet1
        
        # Mengecek apakah sheet benar-benar kosong
        existing_data = sheet.get_all_values()
        
        # Jika kosong (tidak ada data sama sekali), tulis header-nya di baris 1
        if len(existing_data) == 0:
            sheet.append_row(df.columns.tolist())
            
        # Tambahkan data baru di baris paling bawah
        sheet.append_rows(df.values.tolist())
        return True
    except Exception as e:
        print(f"Error Google Sheets: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    tickers_input = request.form.get('tickers')
    tickers = [t.strip().upper() for t in tickers_input.split(',')]
    all_data = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # KITA KEMBALIKAN KE 1 BULAN (1mo)
            df = stock.history(period="1mo") 
            
            if not df.empty:
                df.reset_index(inplace=True)
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                df['Symbol'] = ticker
                cols = ['Symbol', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                df = df[cols]
                all_data.append(df)
        except Exception as e:
            print(f"Gagal ambil {ticker}: {e}")

    if not all_data:
        return """
        <div style="text-align:center;margin-top:50px;font-family:Arial;">
            <h2>❌ Data tidak ditemukan.</h2>
            <p>Pastikan kode saham benar dan gunakan akhiran .JK (contoh: BBCA.JK).</p>
            <a href="/" style="text-decoration:none;color:#007bff;font-weight:bold;">⬅️ Kembali ke Home</a>
        </div>
        """, 400

    final_df = pd.concat(all_data, ignore_index=True)

    # --- NAMA SHEET SESUAI SCREENSHOT ---
    sukses_sheets = simpan_ke_sheets(final_df, 'data saham')
    # -------------------------------------

    output = StringIO()
    final_df.to_csv(output, index=False)
    
    pesan = "Berhasil disimpan ke Google Sheets!" if sukses_sheets else "Gagal simpan ke Sheets (Cek log), tapi CSV siap diunduh."
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-disposition": "attachment; filename=data_saham.csv",
            "X-Message": pesan
        }
    )

if __name__ == '__main__':
    app.run(debug=True)
