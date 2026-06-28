HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZARVPN | پنل مدیریت هوشمند</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vazirmatn@3.3.0/Vazirmatn-font-face.css">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Vazirmatn, sans-serif; }
        body { background-color: #e0e8f6; color: #3c4858; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 600px; }
        
        /* Neumorphism Design */
        .card {
            background: #e0e8f6;
            border-radius: 24px;
            box-shadow: 9px 9px 16px #be9999, -9px -9px 16px #ffffff;
            padding: 25px;
            margin-bottom: 25px;
        }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .user-profile { display: flex; align-items: center; gap: 15px; }
        .avatar { width: 55px; height: 55px; border-radius: 50%; border: 3px solid #e0e8f6; box-shadow: 4px 4px 8px #bec8d6, -4px -4px 8px #ffffff; }
        
        .title { font-size: 20px; font-weight: bold; color: #1a2332; }
        .subtitle { font-size: 14px; color: #758398; margin-top: 5px; }
        
        /* Quick Stats */
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .stat-box { background: #e0e8f6; border-radius: 16px; box-shadow: inset 4px 4px 8px #bec8d6, inset -4px -4px 8px #ffffff; padding: 15px; text-align: center; }
        .stat-value { font-size: 18px; font-weight: bold; color: #2d3748; margin-top: 5px; }
        
        /* Inputs & Buttons */
        input, select {
            width: 100%; padding: 12px 15px; border: none; background: #e0e8f6;
            border-radius: 12px; box-shadow: inset 3px 3px 6px #bec8d6, inset -3px -3px 6px #ffffff;
            margin-top: 8px; margin-bottom: 15px; outline: none; color: #2d3748;
        }
        button {
            width: 100%; padding: 14px; border: none; background: #e0e8f6; color: #2b6cb0;
            font-weight: bold; border-radius: 14px; box-shadow: 5px 5px 10px #bec8d6, -5px -5px 10px #ffffff;
            cursor: pointer; transition: all 0.2s ease;
        }
        button:active { box-shadow: inset 3px 3px 6px #bec8d6, inset -3px -3px 6px #ffffff; }
        .btn-danger { color: #e53e3e; }
        
        .item-list { margin-top: 15px; display: flex; flex-direction: column; gap: 12px; }
        .item-row { display: flex; justify-content: space-between; align-items: center; background: #e0e8f6; padding: 12px 18px; border-radius: 14px; box-shadow: 3px 3px 6px #bec8d6, -3px -3px 6px #ffffff; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card header">
            <div class="user-profile">
                <div class="avatar" style="background: url('https://www.w3schools.com/howto/img_avatar.png') center/cover;"></div>
                <div>
                    <div class="title">مدیریت کل سیستم</div>
                    <div class="subtitle">ربات زار وی‌پی‌ان پلاس</div>
                </div>
            </div>
            <div style="font-size: 24px;">⚡</div>
        </div>

        <div class="card">
            <div class="title" style="margin-bottom: 15px;">📊 دسترسی و آمارهای سریع</div>
            <div class="stats-grid">
                <div class="stat-box"><div>تعداد کل کاربران</div><div class="stat-value">{total_users} نفر</div></div>
                <div class="stat-box"><div>سرورهای متصل</div><div class="stat-value">{total_servers} سرور</div></div>
            </div>
        </div>

        <div class="card">
            <div class="title">🖥️ اتصال پنل ثنایی جدید</div>
            <form action="/admin/add-server" method="post" style="margin-top: 15px;">
                <label>نام سرور:</label><input type="text" name="name" placeholder="مثلا آلمان ۱" required>
                <label>آدرس پنل (با پورت):</label><input type="url" name="url" placeholder="http://178.105.165.200:2054" required>
                <label>نام کاربری پنل:</label><input type="text" name="username" required>
                <label>کلمه عبور پنل:</label><input type="password" name="password" required>
                <button type="submit">➕ تست اتصال و ذخیره سرور</button>
            </form>
            
            <div class="item-list">
                <h3>سرورهای فعلی:</h3>
                {servers_html}
            </div>
        </div>

        <div class="card">
            <div class="title">📦 ساخت پکیج فروشی جدید</div>
            <form action="/admin/add-package" method="post" style="margin-top: 15px;">
                <label>نام پکیج:</label><input type="text" name="name" placeholder="پکیج VIP یکماهه" required>
                <label>حجم (گیگابایت):</label><input type="number" name="size_gb" required>
                <label>زمان (روز):</label><input type="number" name="days" required>
                <label>قیمت (تومان):</label><input type="number" name="price" required>
                <button type="submit">📦 ثبت و انتشار پکیج در ربات</button>
            </form>
            
            <div class="item-list">
                <h3>پکیج‌های فعلی ربات:</h3>
                {packages_html}
            </div>
        </div>
    </div>
</body>
</html>
"""

