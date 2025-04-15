from flask import Flask, render_template, request, send_file, url_for
from flask_babel import Babel, gettext as _
import mysql.connector
import pdfkit
import os
from datetime import datetime
import tempfile

app = Flask(__name__, template_folder='templates')
babel = Babel(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Vasee@2002',
    'database': 'credit_card_system'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Configure Babel settings
app.config.update(
    BABEL_DEFAULT_LOCALE='en',
    LANGUAGES = {
        'en': 'English',
        'ms': 'Bahasa Melayu',
        'zh': '中文'
    }
)

# Translations dictionary
translations = {
    'ms': {
        'Credit Card Statement': 'Penyata Kad Kredit',
        'Customer Information': 'Maklumat Pelanggan',
        'Name': 'Nama',
        'Account Number': 'Nombor Akaun',
        'Statement Date': 'Tarikh Penyata',
        'Address': 'Alamat',
        'Transaction History': 'Sejarah Transaksi',
        'Date': 'Tarikh',
        'Description': 'Keterangan',
        'Debit': 'Debit',
        'Credit': 'Kredit',
        'Balance': 'Baki'
    },
    'zh': {
        'Credit Card Statement': '信用卡对账单',
        'Customer Information': '客户信息',
        'Name': '姓名',
        'Account Number': '账号',
        'Statement Date': '对账单日期',
        'Address': '地址',
        'Transaction History': '交易记录',
        'Date': '日期',
        'Description': '说明',
        'Debit': '支出',
        'Credit': '存入',
        'Balance': '余额',
        'Supermarket': '超市',
        'Movie Tickets': '电影票',
        'Bonus Credit': '奖金存入',
        'Utility Bill': '水电费',
        'Salary Credit': '工资存入',
        'Park Ave': '公园大道',
        'Bangalore': '班加罗尔',
        'KA': '卡纳塔克邦'
    },
    'ta': {
        'Credit Card Statement': 'கடன் அட்டை அறிக்கை',
        'Customer Information': 'வாடிக்கையாளர் விவரங்கள்',
        'Name': 'பெயர்',
        'Account Number': 'கணக்கு எண்',
        'Statement Date': 'அறிக்கை தேதி',
        'Address': 'முகவரி',
        'Transaction History': 'பரிவர்த்தனை வரலாறு',
        'Date': 'தேதி',
        'Description': 'விவரம்',
        'Debit': 'பற்று',
        'Credit': 'வரவு',
        'Balance': 'இருப்பு',
        'Supermarket': 'சூப்பர்மார்க்கெட்',
        'Movie Tickets': 'திரைப்பட டிக்கெட்டுகள்',
        'Bonus Credit': 'போனஸ் வரவு',
        'Utility Bill': 'பயன்பாட்டு கட்டணம்',
        'Salary Credit': 'சம்பள வரவு',
        'Park Ave': 'பார்க் அவென்யூ',
        'Bangalore': 'பெங்களூரு',
        'KA': 'கர்நாடகா'
    }
}

def get_locale():
    return request.form.get('language', 'en')

babel.init_app(app, locale_selector=get_locale)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate_statement', methods=['POST'])
def generate_statement():
    account_number = request.form.get('account_number')
    language = request.form.get('language', 'en')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get translations for selected language
        current_translations = translations.get(language, {})
        
        cursor.execute("SELECT * FROM customers WHERE account_number = %s", (account_number,))
        customer = cursor.fetchone()
        
        if not customer:
            return "Customer not found", 404
            
        cursor.execute("""
            SELECT * FROM transactions 
            WHERE account_number = %s 
            ORDER BY transaction_date DESC
        """, (account_number,))
        transactions = cursor.fetchall()
        
        # Translate customer name and address if language is Chinese
        if language == 'zh' and customer:
            # Handle name translation
            if 'name' in customer:
                name_parts = customer['name'].split()
                if len(name_parts) == 2:
                    customer['name'] = f"{name_parts[1]}{name_parts[0]}"
            
            # Handle address translation
            address_parts = customer['address'].split(',')
            translated_parts = []
            for part in address_parts:
                part = part.strip()
                translated_part = current_translations.get(part, part)
                translated_parts.append(translated_part)
            customer['address'] = '，'.join(translated_parts)
        
        # Fix logo path - use absolute file system path
        logo_path = os.path.join(app.root_path, 'static', 'images', 'logo.png')
        
        html_content = render_template(
            'statement.html',
            customer=customer,
            transactions=transactions,
            generated_date=datetime.now(),
            language=language,
            t=current_translations
        )
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
        
        options = {
            'encoding': 'UTF-8',
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'quiet': None
        }
        
        pdfkit.from_string(html_content, temp_file.name, configuration=config, options=options)
        
        return send_file(temp_file.name, as_attachment=True, download_name=f'statement_{account_number}.pdf')
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)