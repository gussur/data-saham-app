from flask import Flask, render_template, request, Response
import pandas as pd
import yfinance as yf
from io import StringIO
import gspread
from google.oauth2.service_account import Credentials
import os

app = Flask(__name__)

# Fungsi untuk koneksi ke Google Sheets
def simpan_ke_sheets(df, sheet_name):
    try:
        # Mengambil file kunci rahasia yang kita taruh di Render tadi
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        # Path ini harus sesuai dengan Filename Secret File di Render
        creds = Credentials.from_service_account_file('google-key.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # Membuka Google Sheets berdasarkan Nama File
        sheet = client.open(sheet_name).sheet1
        
        # Jika sheet kosong, tulis header-nya
        if not sheet.get_all_values():
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
            df = stock.history(period="1d") # Ambil data hari terakhir saja untuk dikirim ke Sheets
            
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
        return '<div style="text-align:center;margin-top:50px;">❌ Data tidak ditemukan. <a href="/">Kembali</a></div>', 400

    final_df = pd.concat(all_data, ignore_index=True)

    # --- BAGIAN KIRIM KE GOOGLE SHEETS ---
    # GANTI 'Data Saham Saya' dengan nama file Google Sheets kamu!
    sukses_sheets = simpan_ke_sheets(final_df, 'data saham')
    # -------------------------------------

    # Tetap berikan opsi download CSV sebagai backup
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
