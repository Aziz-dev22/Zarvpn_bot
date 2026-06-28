#!/bin/bash

# رنگ‌ها برای زیباتر شدن محیط ترمینال
GREEN='\033[0,32m'
RED='\033[0,31m'
BLUE='\033[0,34m'
NC='\033[0m' # No Color

clear
echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}       ZarVPN Bot Management Toolkit (v1.0)       ${NC}"
echo -e "${BLUE}==================================================${NC}"
echo -e "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
echo -e "1) 🔄 ${GREEN}بروزرسانی ربات${NC} (بدون پاک شدن دیتابیس و تنظیمات)"
echo -e "2) 🗑️ ${RED}حذف کامل ربات${NC} (پاک کردن سورس و دیتابیس)"
echo -e "3) 🚀 ${GREEN}نصب مجدد کامل${NC} (حذف و نصب صفر تا صد سیستم)"
echo -e "4) ❌ انصراف"
echo -e "${BLUE}--------------------------------------------------${NC}"
read -p "عدد گزینه مورد نظر را وارد کنید [1-4]: " choice

case $choice in
    1)
        echo -e "\n${BLUE}[🔄] در حال دریافت آخرین تغییرات از گیت‌هاب...${NC}"
        cd ~/Zarvpn_bot
        # دریافت کدهای جدید از گیت‌هاب بدون دست زدن به دیتابیس (.db) و تنظیمات (.env)
        git reset --hard HEAD
        git pull origin main
        
        # فعال‌سازی محیط مجازی و آپدیت پکیج‌ها در صورت تغییر
        source .venv/bin/activate
        export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
        uv pip install -r requirements.txt
        
        echo -e "${GREEN}[✓] ربات با موفقیت آپدیت شد! در حال اجرا...${NC}"
        uv run python bot.py
        ;;
        
    2)
        read -p "⚠️ آیا مطمئن هستید که می‌خواهید ربات و تمام دیتابیس را کاملاً حذف کنید؟ [y/n]: " confirm
        if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
            echo -e "\n${RED}[🗑️] در حال حذف کامل پروژه و اطلاعات...${NC}"
            cd ~
            rm -rf Zarvpn_bot
            echo -e "${GREEN}[✓] ربات زار وی‌پی‌ان با موفقیت کاملاً از سرور شما حذف شد.${NC}"
        else
            echo -e "\n❌ عملیات لغو شد."
        fi
        ;;
        
    3)
        read -p "⚠️ با نصب مجدد، تمام اکانت‌ها و دیتابیس فعلی پاک خواهد شد. موافقید؟ [y/n]: " confirm_reinstall
        if [[ $confirm_reinstall == [yY] || $confirm_reinstall == [yY][eE][sS] ]]; then
            echo -e "\n${RED}[🗑️] در حال حذف نسخه قدیمی...${NC}"
            cd ~
            rm -rf Zarvpn_bot
            
            echo -e "${BLUE}[🚀] در حال دانلود و نصب مجدد نسخه صفر از گیت‌هاب...${NC}"
            git clone https://github.com/Aziz-dev22/Zarvpn_bot.git
            cd Zarvpn_bot
            
            uv venv --python 3.12
            source .venv/bin/activate
            export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
            uv pip install -r requirements.txt
            
            clear
            echo -e "${GREEN}[✓] نصب مجدد با موفقیت انجام شد! شروع تنظیمات اولیه...${NC}"
            uv run python bot.py
        else
            echo -e "\n❌ عملیات لغو شد."
        fi
        ;;
        
    4)
        echo -e "\n❌ خارج شدید."
        exit 0
        ;;
        
    *)
        echo -e "\n${RED}❌ گزینه نامعتبر است.${NC}"
        exit 1
        ;;
esac

