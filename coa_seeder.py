from .database import db
from .db_coa import ChartOfAccounts
from .db_currency import Currency
from typing import Dict, List, Optional, Tuple
import re

class SmartCOAEngine:
    """
    محرك ذكي لإنشاء شجرة حسابات متخصصة لكل قطاع
    بنظام قوي يعتمد على المعايير المحاسبية الدولية
    """
    
    # ==================== القالب الأساسي (إطار موحد) ====================
    STANDARD_FRAMEWORK = [
    # 1. الأصول (Assets) - 1000
    {"code": "1000", "name_ar": "الأصول", "name_en": "Assets", "type": "Asset", 
     "is_group": True, "parent_code": None, "level": 1},
    
    # 1.1 الأصول الثابتة - 1100
    {"code": "1100", "name_ar": "الأصول الثابتة", "name_en": "Fixed Assets", "type": "Asset", 
     "is_group": True, "parent_code": "1000", "level": 2},
    
    {"code": "1110", "name_ar": "أثاث", "name_en": "Furniture", "type": "Asset", 
     "is_group": True, "parent_code": "1100", "level": 3},
    {"code": "1120", "name_ar": "الأجهزة والمعدات", "name_en": "Equipment", "type": "Asset", 
     "is_group": True, "parent_code": "1100", "level": 3},
    {"code": "1130", "name_ar": "وسائل النقل", "name_en": "Transportation", "type": "Asset", 
     "is_group": True, "parent_code": "1100", "level": 3},
    {"code": "1140", "name_ar": "مباني", "name_en": "Buildings", "type": "Asset", 
     "is_group": True, "parent_code": "1100", "level": 3},
    {"code": "1150", "name_ar": "أراضي", "name_en": "Land", "type": "Asset", 
     "is_group": True, "parent_code": "1100", "level": 3},
    
    # 1.2 الأصول المتداولة - 1200
    {"code": "1200", "name_ar": "الأصول المتداولة", "name_en": "Current Assets", "type": "Asset", 
     "is_group": True, "parent_code": "1000", "level": 2},
    
    {"code": "1210", "name_ar": "الخزينة", "name_en": "Treasury", "type": "Asset", 
     "is_group": True, "parent_code": "1200", "level": 3},
    {"code": "1211", "name_ar": "الخزينة الأساسية", "name_en": "Main Treasury", "type": "Asset", 
     "is_group": False, "parent_code": "1210", "level": 4},
    
    {"code": "1220", "name_ar": "البنك", "name_en": "Bank", "type": "Asset", 
     "is_group": True, "parent_code": "1200", "level": 3},
    
    {"code": "1230", "name_ar": "المخزون", "name_en": "Inventory", "type": "Asset", 
     "is_group": True, "parent_code": "1200", "level": 3},
    
    {"code": "1240", "name_ar": "المدينون", "name_en": "Debtors", "type": "Asset", 
     "is_group": True, "parent_code": "1200", "level": 3},
    
    {"code": "1241", "name_ar": "العملاء", "name_en": "Clients", "type": "Asset", 
     "is_group": True, "parent_code": "1240", "level": 4},
    {"code": "12411", "name_ar": "POS Client", "name_en": "POS Client", "type": "Asset", 
     "is_group": False, "parent_code": "1241", "level": 5},
    
    {"code": "1242", "name_ar": "أطراف مدينة أخرى", "name_en": "Other Debtors", "type": "Asset", 
     "is_group": False, "parent_code": "1240", "level": 4},
    
    {"code": "1250", "name_ar": "عهد الموظفين", "name_en": "Employee Advances", "type": "Asset", 
     "is_group": True, "parent_code": "1200", "level": 3},
    
    {"code": "1260", "name_ar": "أوراق القبض", "name_en": "Receivables Notes", "type": "Asset", 
     "is_group": True, "parent_code": "1200", "level": 3},
    
    {"code": "1270", "name_ar": "عجز وزيادة الصندوق", "name_en": "Cash Short & Over", "type": "Asset", 
     "is_group": False, "parent_code": "1200", "level": 3},
    
    {"code": "1280", "name_ar": "تغيير عملة", "name_en": "Currency Exchange", "type": "Asset", 
     "is_group": False, "parent_code": "1200", "level": 3},
    
    {"code": "1290", "name_ar": "المشتريات", "name_en": "Purchases", "type": "Asset", 
     "is_group": False, "parent_code": "1200", "level": 3},
    
    # 2. الخصوم (Liabilities) - 2000
    {"code": "2000", "name_ar": "الخصوم", "name_en": "Liabilities", "type": "Liability", 
     "is_group": True, "parent_code": None, "level": 1},
    
    # 2.1 الخصوم المتداولة - 2100
    {"code": "2100", "name_ar": "الخصوم المتداولة", "name_en": "Current Liabilities", "type": "Liability", 
     "is_group": True, "parent_code": "2000", "level": 2},
    
    {"code": "2110", "name_ar": "الدائنون", "name_en": "Creditors", "type": "Liability", 
     "is_group": True, "parent_code": "2100", "level": 3},
    
    {"code": "2111", "name_ar": "الموردون", "name_en": "Suppliers", "type": "Liability", 
     "is_group": True, "parent_code": "2110", "level": 4},
    {"code": "21110", "name_ar": "اسم المورد التجاري", "name_en": "Trade Supplier", "type": "Liability", 
     "is_group": False, "parent_code": "2111", "level": 5},
    
    {"code": "2112", "name_ar": "شركات الشحن", "name_en": "Shipping Companies", "type": "Liability", 
     "is_group": True, "parent_code": "2110", "level": 4},
    {"code": "21120", "name_ar": "شحن مبيعات", "name_en": "Sales Shipping", "type": "Liability", 
     "is_group": False, "parent_code": "2112", "level": 5},
    
    {"code": "2113", "name_ar": "أطراف دائنة أخرى", "name_en": "Other Creditors", "type": "Liability", 
     "is_group": False, "parent_code": "2110", "level": 4},
    
    {"code": "2120", "name_ar": "أوراق الدفع", "name_en": "Payables Notes", "type": "Liability", 
     "is_group": True, "parent_code": "2100", "level": 3},
    
    {"code": "2130", "name_ar": "مجمع الإهلاك", "name_en": "Accumulated Depreciation", "type": "Liability", 
     "is_group": True, "parent_code": "2100", "level": 3},
    
    {"code": "2140", "name_ar": "أرصدة افتتاحية", "name_en": "Opening Balances", "type": "Liability", 
     "is_group": False, "parent_code": "2100", "level": 3},
    
    {"code": "2150", "name_ar": "القيمة المضافة المطلوبة", "name_en": "Required VAT", "type": "Liability", 
     "is_group": True, "parent_code": "2100", "level": 3},
    
    # 2.2 الخصوم طويلة الأجل - 2200
    {"code": "2200", "name_ar": "الخصوم طويلة الأجل", "name_en": "Long-term Liabilities", "type": "Liability", 
     "is_group": True, "parent_code": "2000", "level": 2},
    
    # 3. رأس المال وحقوق الملكية (Equity) - 3000
    {"code": "3000", "name_ar": "رأس المال وحقوق الملكية", "name_en": "Capital and Equity", "type": "Equity", 
     "is_group": True, "parent_code": None, "level": 1},
    
    # 4. الإيرادات (Revenue) - 4000
    {"code": "4000", "name_ar": "الإيرادات", "name_en": "Revenues", "type": "Revenue", 
     "is_group": True, "parent_code": None, "level": 1},
    
    # 4.1 إيرادات المبيعات - 4100
    {"code": "4100", "name_ar": "إيرادات المبيعات", "name_en": "Sales Revenue", "type": "Revenue", 
     "is_group": True, "parent_code": "4000", "level": 2},
    
    {"code": "4110", "name_ar": "المبيعات", "name_en": "Sales", "type": "Revenue", 
     "is_group": False, "parent_code": "4100", "level": 3},
    
    {"code": "4120", "name_ar": "مردودات المبيعات", "name_en": "Sales Returns", "type": "Revenue", 
     "is_group": False, "parent_code": "4100", "level": 3},
    
    # 4.2 إيرادات أخرى - 4200
    {"code": "4200", "name_ar": "إيرادات أخرى", "name_en": "Other Revenues", "type": "Revenue", 
     "is_group": True, "parent_code": "4000", "level": 2},
    
    {"code": "4210", "name_ar": "إيرادات أخرى", "name_en": "Other Revenues", "type": "Revenue", 
     "is_group": False, "parent_code": "4200", "level": 3},
    
    {"code": "4220", "name_ar": "أرباح وخسائر رأسمالية", "name_en": "Capital Gains/Losses", "type": "Revenue", 
     "is_group": False, "parent_code": "4200", "level": 3},
    
    # 5. المصروفات (Expenses) - 5000
    {"code": "5000", "name_ar": "المصروفات", "name_en": "Expenses", "type": "Expense", 
     "is_group": True, "parent_code": None, "level": 1},
    
    # 5.1 تكلفة المبيعات - 5100
    {"code": "5100", "name_ar": "تكلفة المبيعات", "name_en": "Cost of Sales", "type": "Expense", 
     "is_group": True, "parent_code": "5000", "level": 2},
    
    {"code": "5110", "name_ar": "تكلفة المبيعات", "name_en": "Cost of Sales", "type": "Expense", 
     "is_group": False, "parent_code": "5100", "level": 3},
    
    {"code": "5120", "name_ar": "شحن مشتريات", "name_en": "Purchases Shipping", "type": "Expense", 
     "is_group": False, "parent_code": "5100", "level": 3},
    
    {"code": "5130", "name_ar": "خصم مسموح به", "name_en": "Allowed Discount", "type": "Expense", 
     "is_group": False, "parent_code": "5100", "level": 3},
    
    # 5.2 مصروفات إدارية وعمومية - 5200
    {"code": "5200", "name_ar": "مصروفات إدارية وعمومية", "name_en": "Administrative Expenses", "type": "Expense", 
     "is_group": True, "parent_code": "5000", "level": 2},
    
    {"code": "5210", "name_ar": "إيجار", "name_en": "Rent", "type": "Expense", 
     "is_group": False, "parent_code": "5200", "level": 3},
    
    {"code": "5220", "name_ar": "كهرباء", "name_en": "Electricity", "type": "Expense", 
     "is_group": False, "parent_code": "5200", "level": 3},
    
    {"code": "5230", "name_ar": "هاتف وانترنت", "name_en": "Phone & Internet", "type": "Expense", 
     "is_group": False, "parent_code": "5200", "level": 3},
    
    {"code": "5240", "name_ar": "صيانة", "name_en": "Maintenance", "type": "Expense", 
     "is_group": False, "parent_code": "5200", "level": 3},
    
    {"code": "5250", "name_ar": "مياه", "name_en": "Water", "type": "Expense", 
     "is_group": False, "parent_code": "5200", "level": 3},
    
    {"code": "5260", "name_ar": "مصاريف حكومية", "name_en": "Government Expenses", "type": "Expense", 
     "is_group": False, "parent_code": "5200", "level": 3},
    
    # 5.3 مصروفات الإهلاك - 5300
    {"code": "5300", "name_ar": "مصروفات الإهلاك", "name_en": "Depreciation Expenses", "type": "Expense", 
     "is_group": True, "parent_code": "5000", "level": 2},
    
    # 5.4 مصروفات أخرى - 5400
    {"code": "5400", "name_ar": "مصروفات أخرى", "name_en": "Other Expenses", "type": "Expense", 
     "is_group": True, "parent_code": "5000", "level": 2},
    
    {"code": "5410", "name_ar": "مصروفات أخرى", "name_en": "Other Expenses", "type": "Expense", 
     "is_group": False, "parent_code": "5400", "level": 3},
    
    {"code": "5420", "name_ar": "الديون المعدومة", "name_en": "Bad Debts", "type": "Expense", 
     "is_group": False, "parent_code": "5400", "level": 3},
    
    {"code": "5430", "name_ar": "عجز وزيادة المخزون", "name_en": "Inventory Short & Over", "type": "Expense", 
     "is_group": False, "parent_code": "5400", "level": 3},
    
    {"code": "5440", "name_ar": "إعادة تقييم", "name_en": "Revaluation", "type": "Expense", 
     "is_group": False, "parent_code": "5400", "level": 3},
]
    # ==================== إضافات التخصصات ====================
    @classmethod
    def get_tech_software_extensions(cls) -> List[Dict]:
        """تكنولوجيا والبرمجيات مع مجموعات فرعية"""
        return [
        # أصول تكنولوجية - مجموعة جديدة
        {"code": "1160", "name_ar": "الأصول التكنولوجية", "name_en": "Technological Assets", 
         "type": "Asset", "is_group": True, "parent_code": "1100", "level": 3},
        
        {"code": "1161", "name_ar": "سيرفرات وأجهزة شبكات", "name_en": "Servers & Network Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1160", "level": 4},
        
        {"code": "1162", "name_ar": "تراخيص برمجيات رئيسية", "name_en": "Major Software Licenses", 
         "type": "Asset", "is_group": False, "parent_code": "1160", "level": 4},
        
        # إيرادات تكنولوجية - مجموعة جديدة
        {"code": "4230", "name_ar": "الإيرادات التكنولوجية", "name_en": "Technology Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4200", "level": 3},
        
        {"code": "4231", "name_ar": "إيرادات اشتراكات (SaaS)", "name_en": "Subscription Revenue (SaaS)", 
         "type": "Revenue", "is_group": False, "parent_code": "4230", "level": 4},
        
        {"code": "4232", "name_ar": "إيرادات تنفيذ وتخصيص", "name_en": "Implementation & Customization Fees", 
         "type": "Revenue", "is_group": False, "parent_code": "4230", "level": 4},
        
        {"code": "4233", "name_ar": "إيرادات صيانة ودعم", "name_en": "Maintenance & Support Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4230", "level": 4},
        
        {"code": "4234", "name_ar": "إيرادات تراخيص برمجيات", "name_en": "Software Licensing Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4230", "level": 4},
        
        {"code": "4235", "name_ar": "إيرادات الاستشارات التقنية", "name_en": "Technical Consulting Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4230", "level": 4},
        
        # تكاليف تكنولوجية - مجموعة جديدة
        {"code": "5140", "name_ar": "التكاليف التكنولوجية", "name_en": "Technology Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5100", "level": 3},
        
        {"code": "5141", "name_ar": "تكاليف السيرفرات السحابية", "name_en": "Cloud Server Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5140", "level": 4},
        
        {"code": "5142", "name_ar": "تكاليف تراخيص برمجيات تابعة لجهات خارجية", "name_en": "Third-party Software Licenses", 
         "type": "Expense", "is_group": False, "parent_code": "5140", "level": 4},
        
        {"code": "5143", "name_ar": "تكاليف الدعم الفني", "name_en": "Technical Support Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5140", "level": 4},
        
        {"code": "5144", "name_ar": "تكاليف ضمان الجودة والاختبار", "name_en": "QA & Testing Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5140", "level": 4},
        
        # مصروفات تكنولوجية - مجموعة جديدة
        {"code": "5270", "name_ar": "المصروفات التكنولوجية", "name_en": "Technology Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5200", "level": 3},
        
        {"code": "5271", "name_ar": "مصاريف حضور المؤتمرات التقنية", "name_en": "Tech Conference Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5270", "level": 4},
        
        {"code": "5272", "name_ar": "مصاريف استضافة مواقع وتطبيقات", "name_en": "Hosting & Application Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5270", "level": 4},
        
        {"code": "5273", "name_ar": "مصاريف تطوير وإنتاج البرمجيات", "name_en": "Software Development Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5270", "level": 4},
        
        {"code": "5274", "name_ar": "مصاريف أبحاث وتطوير (R&D)", "name_en": "Research & Development (R&D)", 
         "type": "Expense", "is_group": False, "parent_code": "5270", "level": 4},
    ]
    
    
    @classmethod
    def get_construction_extensions(cls) -> List[Dict]:
        """إنشاءات ومقاولات"""
        return [
        # ============ الأصول الثابتة - المقاولات (تحت 1100) ============
        {"code": "1170", "name_ar": "معدات الإنشاءات", "name_en": "Construction Equipment", 
         "type": "Asset", "is_group": True, "parent_code": "1100", "level": 3},
        
        {"code": "1171", "name_ar": "معدات ثقيلة", "name_en": "Heavy Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1170", "level": 4},
        
        {"code": "1172", "name_ar": "معدات خفيفة", "name_en": "Light Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1170", "level": 4},
        
        {"code": "1173", "name_ar": "أدوات وأجهزة قياس", "name_en": "Tools & Measuring Devices", 
         "type": "Asset", "is_group": False, "parent_code": "1170", "level": 4},
        
        {"code": "1174", "name_ar": "مركبات الموقع", "name_en": "Site Vehicles", 
         "type": "Asset", "is_group": False, "parent_code": "1170", "level": 4},
        
        # ============ الأصول المتداولة - المقاولات (تحت 1200) ============
        {"code": "12100", "name_ar": "مستخلصات وأعمال تحت التنفيذ", "name_en": "Billings & Work in Progress", 
         "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
        
        {"code": "12101", "name_ar": "مستخلصات معتمدة للتحصيل", "name_en": "Approved Billings", 
         "type": "Asset", "is_group": False, "parent_code": "12100", "level": 4},
        
        {"code": "12102", "name_ar": "مستخلصات تحت الاعتماد", "name_en": "Billings Pending Approval", 
         "type": "Asset", "is_group": False, "parent_code": "12100", "level": 4},
        
        {"code": "12103", "name_ar": "أعمال تحت التنفيذ (WIP)", "name_en": "Work in Progress (WIP)", 
         "type": "Asset", "is_group": False, "parent_code": "12100", "level": 4},
        
        {"code": "12110", "name_ar": "مخزونات المقاولات", "name_en": "Construction Inventory", 
         "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
        
        {"code": "12111", "name_ar": "مواد بناء في الموقع", "name_en": "Construction Materials on Site", 
         "type": "Asset", "is_group": False, "parent_code": "12110", "level": 4},
        
        {"code": "12112", "name_ar": "مواد بناء في المخزن الرئيسي", "name_en": "Construction Materials in Main Storage", 
         "type": "Asset", "is_group": False, "parent_code": "12110", "level": 4},
        
        {"code": "12113", "name_ar": "مواد قيد التوريد", "name_en": "Materials in Transit", 
         "type": "Asset", "is_group": False, "parent_code": "12110", "level": 4},
        
        # ============ الخصوم - المقاولات (تحت 2100) ============
        {"code": "2160", "name_ar": "موردو الإنشاءات", "name_en": "Construction Suppliers", 
         "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
        
        {"code": "2161", "name_ar": "موردون مواد بناء", "name_en": "Construction Materials Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "2160", "level": 4},
        
        {"code": "2162", "name_ar": "موردون معدات وأدوات", "name_en": "Equipment & Tools Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "2160", "level": 4},
        
        {"code": "2163", "name_ar": "مقاولو باطن", "name_en": "Subcontractors", 
         "type": "Liability", "is_group": True, "parent_code": "2160", "level": 4},
        
        {"code": "21631", "name_ar": "مقاولو هيكل خرساني", "name_en": "Concrete Structure Subcontractors", 
         "type": "Liability", "is_group": False, "parent_code": "2163", "level": 5},
        
        {"code": "21632", "name_ar": "مقاولو تشطيبات", "name_en": "Finishing Subcontractors", 
         "type": "Liability", "is_group": False, "parent_code": "2163", "level": 5},
        
        {"code": "21633", "name_ar": "مقاولو كهرباء", "name_en": "Electrical Subcontractors", 
         "type": "Liability", "is_group": False, "parent_code": "2163", "level": 5},
        
        {"code": "21634", "name_ar": "مقاولو سباكة", "name_en": "Plumbing Subcontractors", 
         "type": "Liability", "is_group": False, "parent_code": "2163", "level": 5},
        
        {"code": "2170", "name_ar": "ضمانات ومحتجَزات", "name_en": "Retention & Warranty Liabilities", 
         "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
        
        {"code": "2171", "name_ar": "محتجَز ضمانات الموردين", "name_en": "Supplier Retention", 
         "type": "Liability", "is_group": False, "parent_code": "2170", "level": 4},
        
        {"code": "2172", "name_ar": "محتجَز ضمانات العملاء", "name_en": "Customer Retention", 
         "type": "Liability", "is_group": False, "parent_code": "2170", "level": 4},
        
        {"code": "2173", "name_ar": "ضمانات أداء", "name_en": "Performance Bonds", 
         "type": "Liability", "is_group": False, "parent_code": "2170", "level": 4},
        
        {"code": "2174", "name_ar": "ضمانات صيانة", "name_en": "Maintenance Bonds", 
         "type": "Liability", "is_group": False, "parent_code": "2170", "level": 4},
        
        # ============ الإيرادات - المقاولات (تحت 4000) ============
        {"code": "4300", "name_ar": "إيرادات الإنشاءات والمقاولات", "name_en": "Construction & Contracting Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4000", "level": 2},
        
        {"code": "4310", "name_ar": "إيرادات عقود إنشائية رئيسية", "name_en": "Main Construction Contracts", 
         "type": "Revenue", "is_group": True, "parent_code": "4300", "level": 3},
        
        {"code": "4311", "name_ar": "إيرادات بناء مباني سكنية", "name_en": "Residential Building Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4310", "level": 4},
        
        {"code": "4312", "name_ar": "إيرادات بناء مباني تجارية", "name_en": "Commercial Building Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4310", "level": 4},
        
        {"code": "4313", "name_ar": "إيرادات مشاريع بنية تحتية", "name_en": "Infrastructure Projects Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4310", "level": 4},
        
        {"code": "4320", "name_ar": "إيرادات أعمال الصيانة والتشغيل", "name_en": "Maintenance & Operation Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4300", "level": 3},
        
        {"code": "4321", "name_ar": "إيرادات صيانة دورية", "name_en": "Regular Maintenance Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4320", "level": 4},
        
        {"code": "4322", "name_ar": "إيرادات إصلاحات طارئة", "name_en": "Emergency Repair Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4320", "level": 4},
        
        {"code": "4330", "name_ar": "إيرادات الخدمات الهندسية", "name_en": "Engineering Services Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4300", "level": 3},
        
        {"code": "4331", "name_ar": "إيرادات التصميم والاستشارات الهندسية", "name_en": "Design & Engineering Consulting", 
         "type": "Revenue", "is_group": False, "parent_code": "4330", "level": 4},
        
        {"code": "4332", "name_ar": "إيرادات إعداد دراسات الجدوى", "name_en": "Feasibility Studies Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4330", "level": 4},
        
        {"code": "4333", "name_ar": "إيرادات الإشراف الهندسي", "name_en": "Engineering Supervision Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4330", "level": 4},
        
        # ============ التكاليف - المقاولات (تحت 5000) ============
        {"code": "5150", "name_ar": "تكاليف الإنشاءات والمقاولات", "name_en": "Construction & Contracting Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
        
        {"code": "5160", "name_ar": "تكاليف مواد البناء", "name_en": "Construction Materials Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5150", "level": 3},
        
        {"code": "5161", "name_ar": "تكلفة مواد البناء المستخدمة", "name_en": "Construction Materials Used", 
         "type": "Expense", "is_group": False, "parent_code": "5160", "level": 4},
        
        {"code": "5162", "name_ar": "تكلفة مواد التشطيبات", "name_en": "Finishing Materials Cost", 
         "type": "Expense", "is_group": False, "parent_code": "5160", "level": 4},
        
        {"code": "5163", "name_ar": "تكلفة المواد الكهربائية والسباكة", "name_en": "Electrical & Plumbing Materials", 
         "type": "Expense", "is_group": False, "parent_code": "5160", "level": 4},
        
        {"code": "5170", "name_ar": "تكاليف العمالة المباشرة", "name_en": "Direct Labor Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5150", "level": 3},
        
        {"code": "5171", "name_ar": "تكلفة عمالة الموقع المباشرة", "name_en": "Direct Site Labor", 
         "type": "Expense", "is_group": False, "parent_code": "5170", "level": 4},
        
        {"code": "5172", "name_ar": "تكلفة مشرفي الموقع", "name_en": "Site Supervisors Cost", 
         "type": "Expense", "is_group": False, "parent_code": "5170", "level": 4},
        
        {"code": "5173", "name_ar": "تكلفة المهندسين الميدانيين", "name_en": "Field Engineers Cost", 
         "type": "Expense", "is_group": False, "parent_code": "5170", "level": 4},
        
        {"code": "5180", "name_ar": "تكاليف مقاولي الباطن", "name_en": "Subcontractor Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5150", "level": 3},
        
        {"code": "5181", "name_ar": "تكلفة مقاولي الهيكل الخرساني", "name_en": "Concrete Structure Subcontractors", 
         "type": "Expense", "is_group": False, "parent_code": "5180", "level": 4},
        
        {"code": "5182", "name_ar": "تكلفة مقاولي التشطيبات", "name_en": "Finishing Subcontractors", 
         "type": "Expense", "is_group": False, "parent_code": "5180", "level": 4},
        
        {"code": "5183", "name_ar": "تكلفة مقاولي الكهرباء", "name_en": "Electrical Subcontractors", 
         "type": "Expense", "is_group": False, "parent_code": "5180", "level": 4},
        
        {"code": "5184", "name_ar": "تكلفة مقاولي السباكة", "name_en": "Plumbing Subcontractors", 
         "type": "Expense", "is_group": False, "parent_code": "5180", "level": 4},
        
        {"code": "5190", "name_ar": "تكاليف المعدات والتشغيل", "name_en": "Equipment & Operation Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5150", "level": 3},
        
        {"code": "5191", "name_ar": "تكلفة تأجير المعدات", "name_en": "Equipment Rental Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5190", "level": 4},
        
        {"code": "5192", "name_ar": "تكلفة وقود المعدات", "name_en": "Equipment Fuel Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5190", "level": 4},
        
        {"code": "5193", "name_ar": "تكلفة النقل والمواصلات للموقع", "name_en": "Site Transportation Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5190", "level": 4},
        
        {"code": "5194", "name_ar": "تكلفة تشغيل المعدات", "name_en": "Equipment Operation Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5190", "level": 4},
        
        # ============ المصروفات - المقاولات (تحت 5000) ============
        {"code": "5280", "name_ar": "مصاريف إدارية - مقاولات", "name_en": "Administrative Expenses - Contracting", 
         "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
        
        {"code": "5290", "name_ar": "مصاريف موقعية وإشرافية", "name_en": "Site & Supervision Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5280", "level": 3},
        
        {"code": "5291", "name_ar": "مصاريف السلامة والأمن في الموقع", "name_en": "Site Safety & Security", 
         "type": "Expense", "is_group": False, "parent_code": "5290", "level": 4},
        
        {"code": "5292", "name_ar": "مصاريف إيجار مواقع مؤقتة", "name_en": "Temporary Site Rental", 
         "type": "Expense", "is_group": False, "parent_code": "5290", "level": 4},
        
        {"code": "5293", "name_ar": "مصاريف مكاتب موقعية", "name_en": "Site Office Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5290", "level": 4},
        
        {"code": "5294", "name_ar": "مصاريف إسكان عمال", "name_en": "Workers Housing Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5290", "level": 4},
        
        {"code": "5300", "name_ar": "مصاريف صيانة المعدات", "name_en": "Equipment Maintenance Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5280", "level": 3},
        
        {"code": "5301", "name_ar": "مصاريف الصيانة الوقائية للمعدات", "name_en": "Equipment Preventive Maintenance", 
         "type": "Expense", "is_group": False, "parent_code": "5300", "level": 4},
        
        {"code": "5302", "name_ar": "مصاريف إصلاح المعدات", "name_en": "Equipment Repair Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5300", "level": 4},
        
        {"code": "5303", "name_ar": "إهلاك معدات الإنشاءات", "name_en": "Construction Equipment Depreciation", 
         "type": "Expense", "is_group": False, "parent_code": "5300", "level": 4},
        
        {"code": "5310", "name_ar": "مصاريف تراخيص وموافقات", "name_en": "Licenses & Approvals Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5280", "level": 3},
        
        {"code": "5311", "name_ar": "مصاريف تراخيص البناء", "name_en": "Building Permits Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5310", "level": 4},
        
        {"code": "5312", "name_ar": "مصاريف فحوصات واختبارات", "name_en": "Inspections & Tests Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5310", "level": 4},
        
        {"code": "5313", "name_ar": "مصاريف رسوم هندسية", "name_en": "Engineering Fees", 
         "type": "Expense", "is_group": False, "parent_code": "5310", "level": 4},
    ]
    
    @classmethod
    def get_manufacturing_extensions(cls) -> List[Dict]:
        """تصنيع وإنتاج"""
        return [
        # ============ الأصول الثابتة - التصنيع (تحت 1100) ============
        {"code": "1180", "name_ar": "معدات وأصول التصنيع", "name_en": "Manufacturing Equipment & Assets", 
         "type": "Asset", "is_group": True, "parent_code": "1100", "level": 3},
        
        {"code": "1181", "name_ar": "آلات ومعدات الإنتاج الرئيسية", "name_en": "Main Production Machinery", 
         "type": "Asset", "is_group": False, "parent_code": "1180", "level": 4},
        
        {"code": "1182", "name_ar": "خطوط الإنتاج الآلية", "name_en": "Automated Production Lines", 
         "type": "Asset", "is_group": False, "parent_code": "1180", "level": 4},
        
        {"code": "1183", "name_ar": "معدات التحكم والجودة", "name_en": "Quality Control Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1180", "level": 4},
        
        {"code": "1184", "name_ar": "معدات التعبئة والتغليف", "name_en": "Packaging Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1180", "level": 4},
        
        {"code": "1185", "name_ar": "معدات المختبر والبحث", "name_en": "Laboratory & Research Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1180", "level": 4},
        
        # ============ الأصول المتداولة - التصنيع (تحت 1200) ============
        {"code": "12120", "name_ar": "مخزونات التصنيع", "name_en": "Manufacturing Inventory", 
         "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
        
        {"code": "12121", "name_ar": "مخزون المواد الخام", "name_en": "Raw Materials Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12120", "level": 4},
        
        {"code": "12122", "name_ar": "مخزون إنتاج تحت التشغيل", "name_en": "Work in Process (WIP) Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12120", "level": 4},
        
        {"code": "12123", "name_ar": "مخزون المنتجات التامة", "name_en": "Finished Goods Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12120", "level": 4},
        
        {"code": "12124", "name_ar": "مخزون مواد التعبئة والتغليف", "name_en": "Packaging Materials Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12120", "level": 4},
        
        {"code": "12125", "name_ar": "مخزون قطع الغيار", "name_en": "Spare Parts Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12120", "level": 4},
        
        {"code": "12126", "name_ar": "مخزون المواد الوسيطة", "name_en": "Intermediate Materials Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12120", "level": 4},
        
        # ============ الخصوم - التصنيع (تحت 2100) ============
        {"code": "2180", "name_ar": "موردو التصنيع", "name_en": "Manufacturing Suppliers", 
         "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
        
        {"code": "2181", "name_ar": "موردون مواد خام", "name_en": "Raw Materials Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "2180", "level": 4},
        
        {"code": "2182", "name_ar": "موردون مواد تعبئة وتغليف", "name_en": "Packaging Materials Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "2180", "level": 4},
        
        {"code": "2183", "name_ar": "موردون قطع غيار ومعدات", "name_en": "Spare Parts & Equipment Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "2180", "level": 4},
        
        # ============ الإيرادات - التصنيع (تحت 4000) ============
        {"code": "4400", "name_ar": "إيرادات التصنيع والإنتاج", "name_en": "Manufacturing & Production Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4000", "level": 2},
        
        {"code": "4410", "name_ar": "إيرادات مبيعات المنتجات المصنعة", "name_en": "Manufactured Products Sales", 
         "type": "Revenue", "is_group": True, "parent_code": "4400", "level": 3},
        
        {"code": "4411", "name_ar": "إيرادات مبيعات منتجات تامة", "name_en": "Finished Products Sales", 
         "type": "Revenue", "is_group": False, "parent_code": "4410", "level": 4},
        
        {"code": "4412", "name_ar": "إيرادات مبيعات قطع الغيار", "name_en": "Spare Parts Sales", 
         "type": "Revenue", "is_group": False, "parent_code": "4410", "level": 4},
        
        {"code": "4413", "name_ar": "إيرادات مبيعات مواد وسيطة", "name_en": "Intermediate Materials Sales", 
         "type": "Revenue", "is_group": False, "parent_code": "4410", "level": 4},
        
        {"code": "4420", "name_ar": "إيرادات عقود التصنيع", "name_en": "Contract Manufacturing Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4400", "level": 3},
        
        {"code": "4421", "name_ar": "إيرادات تصنيع حسب الطلب", "name_en": "Custom Manufacturing Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4420", "level": 4},
        
        {"code": "4422", "name_ar": "إيرادات تصنيع علامات تجارية خاصة", "name_en": "Private Label Manufacturing", 
         "type": "Revenue", "is_group": False, "parent_code": "4420", "level": 4},
        
        {"code": "4430", "name_ar": "إيرادات الخدمات الصناعية", "name_en": "Industrial Services Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4400", "level": 3},
        
        {"code": "4431", "name_ar": "إيرادات خدمات تصنيعية", "name_en": "Manufacturing Services Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4430", "level": 4},
        
        {"code": "4432", "name_ar": "إيرادات خدمات صيانة صناعية", "name_en": "Industrial Maintenance Services", 
         "type": "Revenue", "is_group": False, "parent_code": "4430", "level": 4},
        
        # ============ التكاليف - التصنيع (تحت 5000) ============
        {"code": "5200", "name_ar": "تكاليف التصنيع والإنتاج", "name_en": "Manufacturing & Production Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
        
        {"code": "5210", "name_ar": "تكاليف المواد المباشرة", "name_en": "Direct Materials Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5200", "level": 3},
        
        {"code": "5211", "name_ar": "تكلفة المواد الخام المستخدمة", "name_en": "Raw Materials Consumed", 
         "type": "Expense", "is_group": False, "parent_code": "5210", "level": 4},
        
        {"code": "5212", "name_ar": "تكلفة مواد التعبئة والتغليف", "name_en": "Packaging Materials Cost", 
         "type": "Expense", "is_group": False, "parent_code": "5210", "level": 4},
        
        {"code": "5213", "name_ar": "تكلفة المواد الوسيطة المستخدمة", "name_en": "Intermediate Materials Used", 
         "type": "Expense", "is_group": False, "parent_code": "5210", "level": 4},
        
        {"code": "5220", "name_ar": "تكاليف العمالة المباشرة", "name_en": "Direct Labor Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5200", "level": 3},
        
        {"code": "5221", "name_ar": "تكلفة عمالة خط الإنتاج", "name_en": "Production Line Labor", 
         "type": "Expense", "is_group": False, "parent_code": "5220", "level": 4},
        
        {"code": "5222", "name_ar": "تكلفة مشرفي الإنتاج", "name_en": "Production Supervisors", 
         "type": "Expense", "is_group": False, "parent_code": "5220", "level": 4},
        
        {"code": "5223", "name_ar": "تكلفة فنيي الصيانة الإنتاجية", "name_en": "Production Maintenance Technicians", 
         "type": "Expense", "is_group": False, "parent_code": "5220", "level": 4},
        
        {"code": "5230", "name_ar": "تكاليف الطاقة والتشغيل", "name_en": "Energy & Operation Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5200", "level": 3},
        
        {"code": "5231", "name_ar": "تكلفة الطاقة الكهربائية للإنتاج", "name_en": "Production Electricity Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5230", "level": 4},
        
        {"code": "5232", "name_ar": "تكلفة الوقود والمحروقات", "name_en": "Fuel & Combustion Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5230", "level": 4},
        
        {"code": "5233", "name_ar": "تكلفة المياه الصناعية", "name_en": "Industrial Water Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5230", "level": 4},
        
        {"code": "5234", "name_ar": "تكلفة الغاز والبخار الصناعي", "name_en": "Industrial Gas & Steam", 
         "type": "Expense", "is_group": False, "parent_code": "5230", "level": 4},
        
        {"code": "5240", "name_ar": "مصاريف المصنع العامة", "name_en": "Factory Overhead", 
         "type": "Expense", "is_group": True, "parent_code": "5200", "level": 3},
        
        {"code": "5241", "name_ar": "صيانة وتشغيل الآلات", "name_en": "Machinery Maintenance & Operation", 
         "type": "Expense", "is_group": False, "parent_code": "5240", "level": 4},
        
        {"code": "5242", "name_ar": "مصاريف مراقبة الجودة", "name_en": "Quality Control Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5240", "level": 4},
        
        {"code": "5243", "name_ar": "مصاريف البحث والتطوير", "name_en": "Research & Development Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5240", "level": 4},
        
        {"code": "5244", "name_ar": "مصاريف السلامة الصناعية", "name_en": "Industrial Safety Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5240", "level": 4},
        
        {"code": "5245", "name_ar": "مصاريف النظافة والصيانة العامة", "name_en": "Cleaning & General Maintenance", 
         "type": "Expense", "is_group": False, "parent_code": "5240", "level": 4},
        
        {"code": "5250", "name_ar": "إهلاك أصول التصنيع", "name_en": "Manufacturing Assets Depreciation", 
         "type": "Expense", "is_group": True, "parent_code": "5200", "level": 3},
        
        {"code": "5251", "name_ar": "إهلاك آلات ومعدات الإنتاج", "name_en": "Production Equipment Depreciation", 
         "type": "Expense", "is_group": False, "parent_code": "5250", "level": 4},
        
        {"code": "5252", "name_ar": "إهلاك خطوط الإنتاج الآلية", "name_en": "Automated Lines Depreciation", 
         "type": "Expense", "is_group": False, "parent_code": "5250", "level": 4},
        
        {"code": "5253", "name_ar": "إهلاك معدات الجودة والقياس", "name_en": "Quality Equipment Depreciation", 
         "type": "Expense", "is_group": False, "parent_code": "5250", "level": 4},
        
        # ============ المصروفات - التصنيع (تحت 5000) ============
        {"code": "5320", "name_ar": "مصاريف إدارية - تصنيع", "name_en": "Administrative Expenses - Manufacturing", 
         "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
        
        {"code": "5330", "name_ar": "مصاريف تسويق منتجات صناعية", "name_en": "Industrial Products Marketing", 
         "type": "Expense", "is_group": True, "parent_code": "5320", "level": 3},
        
        {"code": "5331", "name_ar": "مصاريف مشاركة معارض صناعية", "name_en": "Industrial Exhibitions Participation", 
         "type": "Expense", "is_group": False, "parent_code": "5330", "level": 4},
        
        {"code": "5332", "name_ar": "مصاريف عينات واختبارات تسويقية", "name_en": "Samples & Marketing Tests", 
         "type": "Expense", "is_group": False, "parent_code": "5330", "level": 4},
        
        {"code": "5340", "name_ar": "مصاريف تدريب وتأهيل فني", "name_en": "Technical Training & Qualification", 
         "type": "Expense", "is_group": True, "parent_code": "5320", "level": 3},
        
        {"code": "5341", "name_ar": "مصاريف تدريب عمالة إنتاجية", "name_en": "Production Labor Training", 
         "type": "Expense", "is_group": False, "parent_code": "5340", "level": 4},
        
        {"code": "5342", "name_ar": "مصاريف دورات تقنية متخصصة", "name_en": "Specialized Technical Courses", 
         "type": "Expense", "is_group": False, "parent_code": "5340", "level": 4},
        
        {"code": "5350", "name_ar": "مصاريف تراخيص وشهادات جودة", "name_en": "Licenses & Quality Certificates", 
         "type": "Expense", "is_group": True, "parent_code": "5320", "level": 3},
        
        {"code": "5351", "name_ar": "مصاريف شهادات الجودة الدولية", "name_en": "International Quality Certificates", 
         "type": "Expense", "is_group": False, "parent_code": "5350", "level": 4},
        
        {"code": "5352", "name_ar": "مصاريف تراخيص تشغيل صناعية", "name_en": "Industrial Operation Licenses", 
         "type": "Expense", "is_group": False, "parent_code": "5350", "level": 4},
    ]
    
    @classmethod
    def get_healthcare_extensions(cls) -> List[Dict]:
        """صحة وعناية شخصية"""
        return [
        # ============ الأصول الثابتة - الصحية (تحت 1100) ============
        {"code": "1190", "name_ar": "الأصول الطبية والصحية", "name_en": "Medical & Healthcare Assets", 
         "type": "Asset", "is_group": True, "parent_code": "1100", "level": 3},
        
        {"code": "1191", "name_ar": "الأجهزة والمعدات الطبية", "name_en": "Medical Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1190", "level": 4},
        
        {"code": "1192", "name_ar": "معدات المعامل الطبية", "name_en": "Medical Laboratory Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1190", "level": 4},
        
        {"code": "1193", "name_ar": "معدات الأشعة والتشخيص", "name_en": "Radiology & Diagnostic Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1190", "level": 4},
        
        {"code": "1194", "name_ar": "معدات العمليات الجراحية", "name_en": "Surgical Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1190", "level": 4},
        
        {"code": "1195", "name_ar": "معدات وأثاث العيادات", "name_en": "Clinic Furniture & Equipment", 
         "type": "Asset", "is_group": False, "parent_code": "1190", "level": 4},
        
        # ============ الأصول المتداولة - الصحية (تحت 1200) ============
        {"code": "12130", "name_ar": "مخزونات صحية وطبية", "name_en": "Healthcare & Medical Inventory", 
         "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
        
        {"code": "12131", "name_ar": "مخزون الأدوية", "name_en": "Pharmaceutical Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12130", "level": 4},
        
        {"code": "12132", "name_ar": "مخزون المستلزمات الطبية", "name_en": "Medical Supplies Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12130", "level": 4},
        
        {"code": "12133", "name_ar": "مخزون مواد التعقيم والتطهير", "name_en": "Sterilization & Disinfection Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12130", "level": 4},
        
        {"code": "12134", "name_ar": "مخزون المستهلكات الطبية", "name_en": "Medical Consumables Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12130", "level": 4},
        
        # ============ الخصوم - الصحية (تحت 2100) ============
        {"code": "2190", "name_ar": "موردو الخدمات الصحية", "name_en": "Healthcare Services Suppliers", 
         "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
        
        {"code": "2191", "name_ar": "موردون أدوية ومستلزمات طبية", "name_en": "Pharmaceutical & Medical Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "2190", "level": 4},
        
        {"code": "2192", "name_ar": "موردون معدات وأجهزة طبية", "name_en": "Medical Equipment Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "2190", "level": 4},
        
        {"code": "2193", "name_ar": "موردون خدمات معامل وأشعة", "name_en": "Lab & Radiology Services Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "2190", "level": 4},
        
        # ============ الإيرادات - الصحية (تحت 4000) ============
        {"code": "4500", "name_ar": "إيرادات الخدمات الصحية", "name_en": "Healthcare Services Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4000", "level": 2},
        
        {"code": "4510", "name_ar": "إيرادات الخدمات الطبية", "name_en": "Medical Services Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4500", "level": 3},
        
        {"code": "4511", "name_ar": "إيرادات الكشفيات والاستشارات الطبية", "name_en": "Medical Consultations Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4510", "level": 4},
        
        {"code": "4512", "name_ar": "إيرادات العمليات الجراحية", "name_en": "Surgical Procedures Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4510", "level": 4},
        
        {"code": "4513", "name_ar": "إيرادات العيادات الخارجية", "name_en": "Outpatient Clinics Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4510", "level": 4},
        
        {"code": "4514", "name_ar": "إيرادات الرعاية الطارئة", "name_en": "Emergency Care Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4510", "level": 4},
        
        {"code": "4520", "name_ar": "إيرادات الخدمات التشخيصية", "name_en": "Diagnostic Services Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4500", "level": 3},
        
        {"code": "4521", "name_ar": "إيرادات التحاليل المعملية", "name_en": "Lab Tests Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4520", "level": 4},
        
        {"code": "4522", "name_ar": "إيرادات الأشعة والتشخيص", "name_en": "Radiology & Diagnostic Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4520", "level": 4},
        
        {"code": "4523", "name_ar": "إيرادات فحوصات خاصة", "name_en": "Special Examinations Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4520", "level": 4},
        
        {"code": "4530", "name_ar": "إيرادات الصيدلية والمستلزمات", "name_en": "Pharmacy & Supplies Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4500", "level": 3},
        
        {"code": "4531", "name_ar": "إيرادات توريد الأدوية", "name_en": "Pharmacy Sales Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4530", "level": 4},
        
        {"code": "4532", "name_ar": "إيرادات مستلزمات طبية", "name_en": "Medical Supplies Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4530", "level": 4},
        
        {"code": "4533", "name_ar": "إيرادات منتجات العناية الشخصية", "name_en": "Personal Care Products Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4530", "level": 4},
        
        {"code": "4540", "name_ar": "إيرادات الخدمات المساعدة", "name_en": "Ancillary Services Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4500", "level": 3},
        
        {"code": "4541", "name_ar": "إيرادات الإقامة والرعاية", "name_en": "Accommodation & Care Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4540", "level": 4},
        
        {"code": "4542", "name_ar": "إيرادات التأهيل والعلاج الطبيعي", "name_en": "Rehabilitation & Physiotherapy Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4540", "level": 4},
        
        {"code": "4543", "name_ar": "إيرادات التغذية والحميات", "name_en": "Nutrition & Diet Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4540", "level": 4},
        
        # ============ التكاليف - الصحية (تحت 5000) ============
        {"code": "5360", "name_ar": "تكاليف الخدمات الصحية", "name_en": "Healthcare Services Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
        
        {"code": "5370", "name_ar": "تكاليف الأدوية والمستلزمات", "name_en": "Drugs & Supplies Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5360", "level": 3},
        
        {"code": "5371", "name_ar": "تكلفة الأدوية المستخدمة", "name_en": "Pharmaceuticals Consumed", 
         "type": "Expense", "is_group": False, "parent_code": "5370", "level": 4},
        
        {"code": "5372", "name_ar": "تكلفة المستلزمات الطبية", "name_en": "Medical Supplies Cost", 
         "type": "Expense", "is_group": False, "parent_code": "5370", "level": 4},
        
        {"code": "5373", "name_ar": "تكلفة مواد التعقيم والتطهير", "name_en": "Sterilization & Disinfection Cost", 
         "type": "Expense", "is_group": False, "parent_code": "5370", "level": 4},
        
        {"code": "5380", "name_ar": "تكاليف الخدمات الخارجية", "name_en": "External Services Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5360", "level": 3},
        
        {"code": "5381", "name_ar": "تكلفة خدمات معامل خارجية", "name_en": "External Lab Services", 
         "type": "Expense", "is_group": False, "parent_code": "5380", "level": 4},
        
        {"code": "5382", "name_ar": "تكلفة خدمات أشعة خارجية", "name_en": "External Radiology Services", 
         "type": "Expense", "is_group": False, "parent_code": "5380", "level": 4},
        
        {"code": "5383", "name_ar": "تكلفة استشارات طبية خارجية", "name_en": "External Medical Consultations", 
         "type": "Expense", "is_group": False, "parent_code": "5380", "level": 4},
        
        # ============ المصروفات - الصحية (تحت 5000) ============
        {"code": "5400", "name_ar": "مصاريف تشغيلية - صحية", "name_en": "Operational Expenses - Healthcare", 
         "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
        
        {"code": "5410", "name_ar": "رواتب ومكافآت الكوادر الصحية", "name_en": "Healthcare Staff Salaries & Bonuses", 
         "type": "Expense", "is_group": True, "parent_code": "5400", "level": 3},
        
        {"code": "5411", "name_ar": "رواتب الأطباء والاستشاريين", "name_en": "Doctors & Consultants Salaries", 
         "type": "Expense", "is_group": False, "parent_code": "5410", "level": 4},
        
        {"code": "5412", "name_ar": "رواتب التمريض والفنيين", "name_en": "Nursing & Technician Salaries", 
         "type": "Expense", "is_group": False, "parent_code": "5410", "level": 4},
        
        {"code": "5413", "name_ar": "رواتب الإداريين والموظفين", "name_en": "Administrative & Staff Salaries", 
         "type": "Expense", "is_group": False, "parent_code": "5410", "level": 4},
        
        {"code": "5414", "name_ar": "مكافآت ومزايا العاملين", "name_en": "Employee Bonuses & Benefits", 
         "type": "Expense", "is_group": False, "parent_code": "5410", "level": 4},
        
        {"code": "5420", "name_ar": "مصاريف التشغيل والصيانة", "name_en": "Operation & Maintenance Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5400", "level": 3},
        
        {"code": "5421", "name_ar": "مصاريف التعقيم والصرف الصحي", "name_en": "Sterilization & Sanitation", 
         "type": "Expense", "is_group": False, "parent_code": "5420", "level": 4},
        
        {"code": "5422", "name_ar": "مصاريف صيانة الأجهزة الطبية", "name_en": "Medical Equipment Maintenance", 
         "type": "Expense", "is_group": False, "parent_code": "5420", "level": 4},
        
        {"code": "5423", "name_ar": "مصاريف نفايات طبية", "name_en": "Medical Waste Disposal", 
         "type": "Expense", "is_group": False, "parent_code": "5420", "level": 4},
        
        {"code": "5430", "name_ar": "مصاريف التأمين والامتثال", "name_en": "Insurance & Compliance Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5400", "level": 3},
        
        {"code": "5431", "name_ar": "مصاريف التأمين الطبي والمسؤولية", "name_en": "Medical Insurance & Liability", 
         "type": "Expense", "is_group": False, "parent_code": "5430", "level": 4},
        
        {"code": "5432", "name_ar": "مصاريف التراخيص والاعتمادات", "name_en": "Licenses & Accreditations", 
         "type": "Expense", "is_group": False, "parent_code": "5430", "level": 4},
        
        {"code": "5433", "name_ar": "مصاريف تدريب وتأهيل طبي", "name_en": "Medical Training & Qualification", 
         "type": "Expense", "is_group": False, "parent_code": "5430", "level": 4},
        
        {"code": "5440", "name_ar": "إهلاك الأصول الصحية", "name_en": "Healthcare Assets Depreciation", 
         "type": "Expense", "is_group": True, "parent_code": "5400", "level": 3},
        
        {"code": "5441", "name_ar": "إهلاك الأجهزة والمعدات الطبية", "name_en": "Medical Equipment Depreciation", 
         "type": "Expense", "is_group": False, "parent_code": "5440", "level": 4},
        
        {"code": "5442", "name_ar": "إهلاك معدات المعامل والأشعة", "name_en": "Lab & Radiology Equipment Depreciation", 
         "type": "Expense", "is_group": False, "parent_code": "5440", "level": 4},
        
        {"code": "5443", "name_ar": "إهلاك أثاث وتجهيزات العيادات", "name_en": "Clinic Furniture Depreciation", 
         "type": "Expense", "is_group": False, "parent_code": "5440", "level": 4},
    ]
    
    @classmethod
    def get_retail_ecommerce_extensions(cls) -> List[Dict]:
        """تجزئة وتجارة إلكترونية"""
        return [
        # ============ الأصول المتداولة - التجزئة (تحت 1200) ============
        {"code": "12140", "name_ar": "مخزونات التجزئة والتجارة الإلكترونية", "name_en": "Retail & E-commerce Inventory", 
         "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
        
        {"code": "12141", "name_ar": "مخزون المنتجات للبيع", "name_en": "Merchandise Inventory for Sale", 
         "type": "Asset", "is_group": False, "parent_code": "12140", "level": 4},
        
        {"code": "12142", "name_ar": "مخزون مواد التغليف والشحن", "name_en": "Shipping & Packaging Materials", 
         "type": "Asset", "is_group": False, "parent_code": "12140", "level": 4},
        
        {"code": "12143", "name_ar": "مخزون المنتجات الموسمية", "name_en": "Seasonal Products Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12140", "level": 4},
        
        {"code": "12144", "name_ar": "مخزون البضائع الجديدة", "name_en": "New Arrivals Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12140", "level": 4},
        
        {"code": "12145", "name_ar": "مخزون العروض والخصومات", "name_en": "Promotional Items Inventory", 
         "type": "Asset", "is_group": False, "parent_code": "12140", "level": 4},
        
        # ============ الخصوم - التجزئة (تحت 2100) ============
        {"code": "21100", "name_ar": "موردو التجزئة والتجارة الإلكترونية", "name_en": "Retail & E-commerce Suppliers", 
         "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
        
        {"code": "21110", "name_ar": "موردون منتجات تجزئة", "name_en": "Retail Products Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "21100", "level": 4},
        
        {"code": "21120", "name_ar": "موردون مواد تعبئة وتغليف", "name_en": "Packaging Materials Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "21100", "level": 4},
        
        {"code": "21130", "name_ar": "موردون خدمات لوجستية", "name_en": "Logistics Services Suppliers", 
         "type": "Liability", "is_group": False, "parent_code": "21100", "level": 4},
        
        # ============ الإيرادات - التجزئة (تحت 4000) ============
        {"code": "4600", "name_ar": "إيرادات التجزئة والتجارة الإلكترونية", "name_en": "Retail & E-commerce Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4000", "level": 2},
        
        {"code": "4610", "name_ar": "إيرادات مبيعات التجزئة التقليدية", "name_en": "Traditional Retail Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4600", "level": 3},
        
        {"code": "4611", "name_ar": "إيرادات مبيعات التجزئة المباشرة", "name_en": "Direct Retail Sales Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4610", "level": 4},
        
        {"code": "4612", "name_ar": "إيرادات مبيعات الفروع", "name_en": "Branch Sales Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4610", "level": 4},
        
        {"code": "4613", "name_ar": "إيرادات مبيعات الجملة", "name_en": "Wholesale Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4610", "level": 4},
        
        {"code": "4620", "name_ar": "إيرادات المبيعات عبر الإنترنت", "name_en": "Online Sales Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4600", "level": 3},
        
        {"code": "4621", "name_ar": "إيرادات المبيعات عبر الموقع الإلكتروني", "name_en": "Website Sales Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4620", "level": 4},
        
        {"code": "4622", "name_ar": "إيرادات المبيعات عبر التطبيقات", "name_en": "Mobile App Sales Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4620", "level": 4},
        
        {"code": "4623", "name_ar": "إيرادات المبيعات عبر منصات التواصل", "name_en": "Social Media Sales Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4620", "level": 4},
        
        {"code": "4624", "name_ar": "إيرادات المبيعات عبر المتاجر الإلكترونية", "name_en": "E-marketplace Sales Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4620", "level": 4},
        
        {"code": "4630", "name_ar": "إيرادات الخدمات والعمليات", "name_en": "Services & Operations Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4600", "level": 3},
        
        {"code": "4631", "name_ar": "إيرادات الشحن والخدمات اللوجستية", "name_en": "Shipping & Logistics Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4630", "level": 4},
        
        {"code": "4632", "name_ar": "إيرادات خدمات التركيب والتوصيل", "name_en": "Installation & Delivery Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4630", "level": 4},
        
        {"code": "4633", "name_ar": "إيرادات خدمات ما بعد البيع", "name_en": "After-sales Services Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4630", "level": 4},
        
        {"code": "4634", "name_ar": "إيرادات خدمات الاشتراكات", "name_en": "Subscription Services Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4630", "level": 4},
        
        # ============ التكاليف - التجزئة (تحت 5000) ============
        {"code": "5450", "name_ar": "تكاليف التجزئة والتجارة الإلكترونية", "name_en": "Retail & E-commerce Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
        
        {"code": "5460", "name_ar": "تكلفة البضاعة المباعة (COGS)", "name_en": "Cost of Goods Sold (COGS)", 
         "type": "Expense", "is_group": True, "parent_code": "5450", "level": 3},
        
        {"code": "5461", "name_ar": "تكلفة المنتجات المباعة", "name_en": "Products Cost of Sales", 
         "type": "Expense", "is_group": False, "parent_code": "5460", "level": 4},
        
        {"code": "5462", "name_ar": "تكاليف مرتجعات المبيعات", "name_en": "Sales Returns & Allowances", 
         "type": "Expense", "is_group": False, "parent_code": "5460", "level": 4},
        
        {"code": "5463", "name_ar": "تكاليف الخصومات التجارية", "name_en": "Trade Discounts", 
         "type": "Expense", "is_group": False, "parent_code": "5460", "level": 4},
        
        {"code": "5470", "name_ar": "تكاليف الشحن والتوصيل", "name_en": "Shipping & Delivery Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5450", "level": 3},
        
        {"code": "5471", "name_ar": "تكاليف التوصيل الداخلي", "name_en": "Local Delivery Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5470", "level": 4},
        
        {"code": "5472", "name_ar": "تكاليف الشحن الدولي", "name_en": "International Shipping Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5470", "level": 4},
        
        {"code": "5473", "name_ar": "تكالخدمات شركات التوصيل", "name_en": "Courier Services Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5470", "level": 4},
        
        {"code": "5480", "name_ar": "تكاليف التغليف والتعبئة", "name_en": "Packaging & Packing Costs", 
         "type": "Expense", "is_group": True, "parent_code": "5450", "level": 3},
        
        {"code": "5481", "name_ar": "تكاليف مواد التغليف", "name_en": "Packaging Materials Costs", 
         "type": "Expense", "is_group": False, "parent_code": "5480", "level": 4},
        
        {"code": "5482", "name_ar": "تكاليف أدوات التعبئة", "name_en": "Packing Tools & Supplies", 
         "type": "Expense", "is_group": False, "parent_code": "5480", "level": 4},
        
        {"code": "5483", "name_ar": "تكاليف التغليف الخاص والهدايا", "name_en": "Special Packaging & Gift Wrapping", 
         "type": "Expense", "is_group": False, "parent_code": "5480", "level": 4},
        
        # ============ المصروفات - التجزئة (تحت 5000) ============
        {"code": "5500", "name_ar": "مصاريف تشغيلية - تجزئة وإلكترونية", "name_en": "Operational Expenses - Retail & E-commerce", 
         "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
        
        {"code": "5510", "name_ar": "مصاريف التسويق والإعلان", "name_en": "Marketing & Advertising Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5500", "level": 3},
        
        {"code": "5511", "name_ar": "مصاريف التسويق الرقمي والإعلانات", "name_en": "Digital Marketing & Ads", 
         "type": "Expense", "is_group": False, "parent_code": "5510", "level": 4},
        
        {"code": "5512", "name_ar": "مصاريف التسويق التقليدي", "name_en": "Traditional Marketing", 
         "type": "Expense", "is_group": False, "parent_code": "5510", "level": 4},
        
        {"code": "5513", "name_ar": "مصاريف العروض الترويجية", "name_en": "Promotional Campaigns", 
         "type": "Expense", "is_group": False, "parent_code": "5510", "level": 4},
        
        {"code": "5514", "name_ar": "مصاريف التأثير والتسويق بالمحتوى", "name_en": "Influencer & Content Marketing", 
         "type": "Expense", "is_group": False, "parent_code": "5510", "level": 4},
        
        {"code": "5520", "name_ar": "مصاريف العمليات الرقمية", "name_en": "Digital Operations Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5500", "level": 3},
        
        {"code": "5521", "name_ar": "مصاريف عمليات الدفع الإلكتروني", "name_en": "Payment Gateway Fees", 
         "type": "Expense", "is_group": False, "parent_code": "5520", "level": 4},
        
        {"code": "5522", "name_ar": "مصاريف منصات التجارة الإلكترونية", "name_en": "E-commerce Platform Fees", 
         "type": "Expense", "is_group": False, "parent_code": "5520", "level": 4},
        
        {"code": "5523", "name_ar": "مصاريف الاستضافة والحلول التقنية", "name_en": "Hosting & Technical Solutions", 
         "type": "Expense", "is_group": False, "parent_code": "5520", "level": 4},
        
        {"code": "5524", "name_ar": "مصاريف التطوير والبرمجة", "name_en": "Development & Programming", 
         "type": "Expense", "is_group": False, "parent_code": "5520", "level": 4},
        
        {"code": "5530", "name_ar": "مصاريف الفروع والمخازن", "name_en": "Branches & Warehouses Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5500", "level": 3},
        
        {"code": "5531", "name_ar": "مصاريف إيجار الفروع والمحلات", "name_en": "Branches & Stores Rent", 
         "type": "Expense", "is_group": False, "parent_code": "5530", "level": 4},
        
        {"code": "5532", "name_ar": "مصاريف تشغيل المخازن", "name_en": "Warehouse Operation Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5530", "level": 4},
        
        {"code": "5533", "name_ar": "مصاريف أمن المخازن والفروع", "name_en": "Warehouse & Branch Security", 
         "type": "Expense", "is_group": False, "parent_code": "5530", "level": 4},
        
        {"code": "5540", "name_ar": "مصاريف خدمات العملاء", "name_en": "Customer Services Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5500", "level": 3},
        
        {"code": "5541", "name_ar": "مصاريف خدمة العملاء والدعم", "name_en": "Customer Service & Support", 
         "type": "Expense", "is_group": False, "parent_code": "5540", "level": 4},
        
        {"code": "5542", "name_ar": "مصاريف إدارة المرتجعات", "name_en": "Returns Management", 
         "type": "Expense", "is_group": False, "parent_code": "5540", "level": 4},
        
        {"code": "5543", "name_ar": "مصاريف ضمان الجودة", "name_en": "Quality Assurance", 
         "type": "Expense", "is_group": False, "parent_code": "5540", "level": 4},
    ]
    
    @classmethod
    def get_finance_banking_extensions(cls) -> List[Dict]:
        """خدمات مالية وبنوك"""
        return [
        # ============ الأصول المتداولة - مالية (تحت 1200) ============
        {"code": "12150", "name_ar": "الاستثمارات والأصول المالية", "name_en": "Investments & Financial Assets", 
         "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
        
        {"code": "12151", "name_ar": "محفظة القروض", "name_en": "Loan Portfolio", 
         "type": "Asset", "is_group": True, "parent_code": "12150", "level": 4},
        
        {"code": "121511", "name_ar": "قروض تجارية", "name_en": "Commercial Loans", 
         "type": "Asset", "is_group": False, "parent_code": "12151", "level": 5},
        
        {"code": "121512", "name_ar": "قروض شخصية", "name_en": "Personal Loans", 
         "type": "Asset", "is_group": False, "parent_code": "12151", "level": 5},
        
        {"code": "121513", "name_ar": "قروض عقارية", "name_en": "Mortgage Loans", 
         "type": "Asset", "is_group": False, "parent_code": "12151", "level": 5},
        
        {"code": "12302", "name_ar": "استثمارات في أوراق مالية", "name_en": "Securities Investments", 
         "type": "Asset", "is_group": True, "parent_code": "12300", "level": 4},
        
        {"code": "123021", "name_ar": "أسهم", "name_en": "Stocks", 
         "type": "Asset", "is_group": False, "parent_code": "12302", "level": 5},
        
        {"code": "123022", "name_ar": "سندات", "name_en": "Bonds", 
         "type": "Asset", "is_group": False, "parent_code": "12302", "level": 5},
        
        {"code": "123023", "name_ar": "صكوك", "name_en": "Sukuk", 
         "type": "Asset", "is_group": False, "parent_code": "12302", "level": 5},
        
        {"code": "12303", "name_ar": "استثمارات قصيرة الأجل", "name_en": "Short-term Investments", 
         "type": "Asset", "is_group": False, "parent_code": "12300", "level": 4},
        
        {"code": "12304", "name_ar": "ودائع لدى بنوك أخرى", "name_en": "Deposits with Other Banks", 
         "type": "Asset", "is_group": False, "parent_code": "12300", "level": 4},
        
        # ============ الخصوم المتداولة - مالية (تحت 2100) ============
        {"code": "21110", "name_ar": "ودائع العملاء", "name_en": "Customer Deposits", 
         "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
        
        {"code": "21111", "name_ar": "ودائع جارية", "name_en": "Current Deposits", 
         "type": "Liability", "is_group": False, "parent_code": "21110", "level": 4},
        
        {"code": "21112", "name_ar": "ودائع توفير", "name_en": "Savings Deposits", 
         "type": "Liability", "is_group": False, "parent_code": "21110", "level": 4},
        
        {"code": "21113", "name_ar": "ودائع لأجل", "name_en": "Term Deposits", 
         "type": "Liability", "is_group": False, "parent_code": "21110", "level": 4},
        
        # ============ الخصوم طويلة الأجل - مالية (تحت 2200) ============
        {"code": "2210", "name_ar": "قروض طويلة الأجل", "name_en": "Long-term Loans Payable", 
         "type": "Liability", "is_group": True, "parent_code": "2200", "level": 3},
        
        {"code": "2211", "name_ar": "قروض من بنوك أخرى", "name_en": "Loans from Other Banks", 
         "type": "Liability", "is_group": False, "parent_code": "2210", "level": 4},
        
        {"code": "2212", "name_ar": "سندات قابلة للتحويل", "name_en": "Convertible Bonds", 
         "type": "Liability", "is_group": False, "parent_code": "2210", "level": 4},
        
        {"code": "2213", "name_ar": "صكوك إسلامية", "name_en": "Islamic Sukuk", 
         "type": "Liability", "is_group": False, "parent_code": "2210", "level": 4},
        
        # ============ الإيرادات - مالية (تحت 4000) ============
        {"code": "4700", "name_ar": "إيرادات الخدمات المالية", "name_en": "Financial Services Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4000", "level": 2},
        
        {"code": "4710", "name_ar": "إيرادات الفوائد والمكاسب المالية", "name_en": "Interest & Financial Gains Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4700", "level": 3},
        
        {"code": "4711", "name_ar": "إيرادات الفوائد", "name_en": "Interest Income", 
         "type": "Revenue", "is_group": False, "parent_code": "4710", "level": 4},
        
        {"code": "4712", "name_ar": "إيرادات التداول والاستثمار", "name_en": "Trading & Investment Income", 
         "type": "Revenue", "is_group": False, "parent_code": "4710", "level": 4},
        
        {"code": "4713", "name_ar": "أرباح توزيعات الأسهم", "name_en": "Dividend Income", 
         "type": "Revenue", "is_group": False, "parent_code": "4710", "level": 4},
        
        {"code": "4714", "name_ar": "مكاسب بيع الأصول المالية", "name_en": "Financial Assets Sales Gains", 
         "type": "Revenue", "is_group": False, "parent_code": "4710", "level": 4},
        
        {"code": "4720", "name_ar": "إيرادات العمولات والرسوم", "name_en": "Commissions & Fees Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4700", "level": 3},
        
        {"code": "4721", "name_ar": "إيرادات عمولات الخدمات", "name_en": "Service Commission Income", 
         "type": "Revenue", "is_group": False, "parent_code": "4720", "level": 4},
        
        {"code": "4722", "name_ar": "رسوم التحويل والحوالات", "name_en": "Transfer & Remittance Fees", 
         "type": "Revenue", "is_group": False, "parent_code": "4720", "level": 4},
        
        {"code": "4723", "name_ar": "رسوم الحسابات والبطاقات", "name_en": "Account & Card Fees", 
         "type": "Revenue", "is_group": False, "parent_code": "4720", "level": 4},
        
        {"code": "4724", "name_ar": "رسوم الصرف الأجنبي", "name_en": "Foreign Exchange Fees", 
         "type": "Revenue", "is_group": False, "parent_code": "4720", "level": 4},
        
        {"code": "4725", "name_ar": "رسوم الضمانات والكفالات", "name_en": "Guarantee & Surety Fees", 
         "type": "Revenue", "is_group": False, "parent_code": "4720", "level": 4},
        
        {"code": "4730", "name_ar": "إيرادات الخدمات المصرفية", "name_en": "Banking Services Revenue", 
         "type": "Revenue", "is_group": True, "parent_code": "4700", "level": 3},
        
        {"code": "4731", "name_ar": "إيرادات خدمات الصرافة", "name_en": "Exchange Services Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4730", "level": 4},
        
        {"code": "4732", "name_ar": "إيرادات خدمات الخزينة", "name_en": "Treasury Services Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4730", "level": 4},
        
        {"code": "4733", "name_ar": "إيرادات خدمات الاستيراد والتصدير", "name_en": "Import/Export Services Revenue", 
         "type": "Revenue", "is_group": False, "parent_code": "4730", "level": 4},
        
        # ============ المصروفات - مالية (تحت 5000) ============
        {"code": "5550", "name_ar": "مصاريف الخدمات المالية", "name_en": "Financial Services Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
        
        {"code": "5560", "name_ar": "مصاريف الفوائد والرسوم المالية", "name_en": "Interest & Financial Fees Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5550", "level": 3},
        
        {"code": "5561", "name_ar": "مصاريف الفوائد", "name_en": "Interest Expense", 
         "type": "Expense", "is_group": False, "parent_code": "5560", "level": 4},
        
        {"code": "5562", "name_ar": "مصاريف الرسوم البنكية", "name_en": "Banking Fees Expense", 
         "type": "Expense", "is_group": False, "parent_code": "5560", "level": 4},
        
        {"code": "5563", "name_ar": "مصاريف عمولات الوساطة", "name_en": "Brokerage Commissions", 
         "type": "Expense", "is_group": False, "parent_code": "5560", "level": 4},
        
        {"code": "5570", "name_ar": "مصاريف المخصصات والاحتياطيات", "name_en": "Provisions & Reserves Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5550", "level": 3},
        
        {"code": "5571", "name_ar": "مصاريف الديون المعدومة", "name_en": "Bad Debt Expense", 
         "type": "Expense", "is_group": False, "parent_code": "5570", "level": 4},
        
        {"code": "5572", "name_ar": "مصاريف مخصص الديون المشكوك فيها", "name_en": "Allowance for Doubtful Accounts", 
         "type": "Expense", "is_group": False, "parent_code": "5570", "level": 4},
        
        {"code": "5573", "name_ar": "مصاريف مخصص مخاطر الائتمان", "name_en": "Credit Risk Provision", 
         "type": "Expense", "is_group": False, "parent_code": "5570", "level": 4},
        
        {"code": "5574", "name_ar": "مصاريف مخصص خسائر السوق", "name_en": "Market Loss Provision", 
         "type": "Expense", "is_group": False, "parent_code": "5570", "level": 4},
        
        {"code": "5580", "name_ar": "مصاريف التشغيل والامتثال", "name_en": "Operation & Compliance Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5550", "level": 3},
        
        {"code": "5581", "name_ar": "مصاريف الامتثال التنظيمي", "name_en": "Regulatory Compliance Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5580", "level": 4},
        
        {"code": "5582", "name_ar": "مصاريف التدقيق والمراجعة", "name_en": "Audit & Review Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5580", "level": 4},
        
        {"code": "5583", "name_ar": "مصاريف أنظمة وتقنيات مصرفية", "name_en": "Banking Systems & Technology", 
         "type": "Expense", "is_group": False, "parent_code": "5580", "level": 4},
        
        {"code": "5584", "name_ar": "مصاريف تأمين الودائع والأصول", "name_en": "Deposit & Asset Insurance", 
         "type": "Expense", "is_group": False, "parent_code": "5580", "level": 4},
        
        {"code": "5590", "name_ar": "مصاريف الفروع والشبكات", "name_en": "Branches & Networks Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5550", "level": 3},
        
        {"code": "5591", "name_ar": "مصاريف تشغيل الفروع", "name_en": "Branch Operation Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5590", "level": 4},
        
        {"code": "5592", "name_ar": "مصاريف أجهزة الصراف الآلي", "name_en": "ATM Expenses", 
         "type": "Expense", "is_group": False, "parent_code": "5590", "level": 4},
        
        {"code": "5593", "name_ar": "مصاريف البنية التحتية للشبكات", "name_en": "Network Infrastructure", 
         "type": "Expense", "is_group": False, "parent_code": "5590", "level": 4},
        
        # ============ المصروفات - أخرى (تحت 5000) ============
        {"code": "5600", "name_ar": "مصاريف إدارية - مالية", "name_en": "Administrative Expenses - Financial", 
         "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
        
        {"code": "5610", "name_ar": "مصاريف التسويق المصرفي", "name_en": "Banking Marketing Expenses", 
         "type": "Expense", "is_group": True, "parent_code": "5600", "level": 3},
        
        {"code": "5611", "name_ar": "مصاريف الإعلانات البنكية", "name_en": "Banking Advertising", 
         "type": "Expense", "is_group": False, "parent_code": "5610", "level": 4},
        
        {"code": "5612", "name_ar": "مصاريف العلاقات العامة", "name_en": "Public Relations", 
         "type": "Expense", "is_group": False, "parent_code": "5610", "level": 4},
        
        {"code": "5613", "name_ar": "مصاريف الفعاليات والمؤتمرات", "name_en": "Events & Conferences", 
         "type": "Expense", "is_group": False, "parent_code": "5610", "level": 4},
    ]
    
    @classmethod
    def get_education_extensions(cls) -> List[Dict]:
        """التعليم والتدريب"""
        return [
			# ============ الأصول الثابتة - التعليمية (تحت 1100) ============
			{"code": "11100", "name_ar": "الأصول التعليمية", "name_en": "Educational Assets", 
			 "type": "Asset", "is_group": True, "parent_code": "1100", "level": 3},
			
			{"code": "11101", "name_ar": "معدات وأجهزة تعليمية", "name_en": "Educational Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11100", "level": 4},
			
			{"code": "11102", "name_ar": "مختبرات ومعامل", "name_en": "Laboratories & Labs", 
			 "type": "Asset", "is_group": False, "parent_code": "11100", "level": 4},
			
			{"code": "11103", "name_ar": "تجهيزات فصول ومدرجات", "name_en": "Classroom & Auditorium Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11100", "level": 4},
			
			{"code": "11104", "name_ar": "مكتبات ومصادر تعلم", "name_en": "Libraries & Learning Resources", 
			 "type": "Asset", "is_group": False, "parent_code": "11100", "level": 4},
			
			{"code": "11105", "name_ar": "منصات التعلم الإلكتروني", "name_en": "E-learning Platforms", 
			 "type": "Asset", "is_group": False, "parent_code": "11100", "level": 4},
			
			# ============ الأصول المتداولة - التعليمية (تحت 1200) ============
			{"code": "12160", "name_ar": "مخزونات تعليمية", "name_en": "Educational Inventory", 
			 "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
			
			{"code": "12161", "name_ar": "كتب ومراجع علمية", "name_en": "Books & Scientific References", 
			 "type": "Asset", "is_group": False, "parent_code": "12160", "level": 4},
			
			{"code": "12162", "name_ar": "مستلزمات تدريبية ومعملية", "name_en": "Training & Lab Supplies", 
			 "type": "Asset", "is_group": False, "parent_code": "12160", "level": 4},
			
			{"code": "12163", "name_ar": "مواد وأدوات تعليمية", "name_en": "Educational Materials & Tools", 
			 "type": "Asset", "is_group": False, "parent_code": "12160", "level": 4},
			
			{"code": "12164", "name_ar": "معدات وألعاب تعليمية", "name_en": "Educational Games & Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "12160", "level": 4},
			
			# ============ الخصوم - التعليمية (تحت 2100) ============
			{"code": "21120", "name_ar": "موردو الخدمات التعليمية", "name_en": "Educational Services Suppliers", 
			 "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
			
			{"code": "21121", "name_ar": "موردون كتب ومراجع", "name_en": "Books & References Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21120", "level": 4},
			
			{"code": "21122", "name_ar": "موردون معدات تعليمية", "name_en": "Educational Equipment Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21120", "level": 4},
			
			{"code": "21123", "name_ar": "موردون برامج ومنصات تعليمية", "name_en": "Educational Software & Platforms", 
			 "type": "Liability", "is_group": False, "parent_code": "21120", "level": 4},
			
			{"code": "21124", "name_ar": "موردون خدمات تدريب واستشارات", "name_en": "Training & Consulting Services", 
			 "type": "Liability", "is_group": False, "parent_code": "21120", "level": 4},
			
			# ============ الإيرادات - التعليمية (تحت 4000) ============
			{"code": "4800", "name_ar": "إيرادات الخدمات التعليمية", "name_en": "Educational Services Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4000", "level": 2},
			
			{"code": "4810", "name_ar": "إيرادات الرسوم الدراسية", "name_en": "Tuition Fees Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4800", "level": 3},
			
			{"code": "4811", "name_ar": "رسوم التسجيل والقبول", "name_en": "Registration & Admission Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4810", "level": 4},
			
			{"code": "4812", "name_ar": "رسوم الفصول الدراسية", "name_en": "Semester/Course Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4810", "level": 4},
			
			{"code": "4813", "name_ar": "رسوم برامج خاصة", "name_en": "Special Program Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4810", "level": 4},
			
			{"code": "4814", "name_ar": "رسوم الدراسات العليا", "name_en": "Graduate Studies Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4810", "level": 4},
			
			{"code": "4820", "name_ar": "إيرادات التدريب والدورات", "name_en": "Training & Courses Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4800", "level": 3},
			
			{"code": "4821", "name_ar": "رسوم دورات تدريبية", "name_en": "Training Course Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4820", "level": 4},
			
			{"code": "4822", "name_ar": "رسوم ورش عمل", "name_en": "Workshop Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4820", "level": 4},
			
			{"code": "4823", "name_ar": "رسوم شهادات مهنية", "name_en": "Professional Certification Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4820", "level": 4},
			
			{"code": "4830", "name_ar": "إيرادات خدمات تعليمية إضافية", "name_en": "Additional Educational Services", 
			 "type": "Revenue", "is_group": True, "parent_code": "4800", "level": 3},
			
			{"code": "4831", "name_ar": "رسوم النقل المدرسي", "name_en": "School Transportation Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4830", "level": 4},
			
			{"code": "4832", "name_ar": "رسوم الأنشطة والرحلات", "name_en": "Activities & Trips Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4830", "level": 4},
			
			{"code": "4833", "name_ar": "رسوم الكافتيريا والمطاعم", "name_en": "Cafeteria & Restaurant Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4830", "level": 4},
			
			{"code": "4834", "name_ar": "رسوم السكن والإقامة", "name_en": "Housing & Accommodation Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4830", "level": 4},
			
			{"code": "4840", "name_ar": "إيرادات التعلم الإلكتروني", "name_en": "E-learning Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4800", "level": 3},
			
			{"code": "4841", "name_ar": "رسوم اشتراكات التعلم الإلكتروني", "name_en": "E-learning Subscriptions", 
			 "type": "Revenue", "is_group": False, "parent_code": "4840", "level": 4},
			
			{"code": "4842", "name_ar": "رسوم دورات أونلاين", "name_en": "Online Course Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4840", "level": 4},
			
			{"code": "4843", "name_ar": "رسوم اختبارات إلكترونية", "name_en": "Electronic Testing Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4840", "level": 4},
			
			{"code": "4844", "name_ar": "رسوم شهادات رقمية", "name_en": "Digital Certificates Fees", 
			 "type": "Revenue", "is_group": False, "parent_code": "4840", "level": 4},
			
			{"code": "4850", "name_ar": "إيرادات البحوث والاستشارات", "name_en": "Research & Consulting Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4800", "level": 3},
			
			{"code": "4851", "name_ar": "إيرادات المشاريع البحثية", "name_en": "Research Projects Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4850", "level": 4},
			
			{"code": "4852", "name_ar": "إيرادات الاستشارات الأكاديمية", "name_en": "Academic Consulting Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4850", "level": 4},
			
			{"code": "4853", "name_ar": "إيرادات النشر العلمي", "name_en": "Scientific Publishing Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4850", "level": 4},
			
			# ============ التكاليف - التعليمية (تحت 5000) ============
			{"code": "5620", "name_ar": "تكاليف الخدمات التعليمية", "name_en": "Educational Services Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
			
			{"code": "5630", "name_ar": "تكاليف المواد التعليمية", "name_en": "Educational Materials Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5620", "level": 3},
			
			{"code": "5631", "name_ar": "تكلفة الكتب والمراجع", "name_en": "Books & References Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5630", "level": 4},
			
			{"code": "5632", "name_ar": "تكلفة المستلزمات التعليمية", "name_en": "Educational Supplies Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5630", "level": 4},
			
			{"code": "5633", "name_ar": "تكلفة برامج ومنصات تعليمية", "name_en": "Educational Software & Platforms", 
			 "type": "Expense", "is_group": False, "parent_code": "5630", "level": 4},
			
			{"code": "5640", "name_ar": "تكاليف التدريب والتطوير", "name_en": "Training & Development Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5620", "level": 3},
			
			{"code": "5641", "name_ar": "تكلفة دورات تدريبية خارجية", "name_en": "External Training Courses", 
			 "type": "Expense", "is_group": False, "parent_code": "5640", "level": 4},
			
			{"code": "5642", "name_ar": "تكلفة استشارات تعليمية", "name_en": "Educational Consulting Costs", 
			 "type": "Expense", "is_group": False, "parent_code": "5640", "level": 4},
			
			{"code": "5643", "name_ar": "تكلفة تراخيص وشهادات", "name_en": "Licenses & Certifications Costs", 
			 "type": "Expense", "is_group": False, "parent_code": "5640", "level": 4},
			
			# ============ المصروفات - التعليمية (تحت 5000) ============
			{"code": "5650", "name_ar": "مصاريف تشغيلية - تعليمية", "name_en": "Operational Expenses - Educational", 
			 "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
			
			{"code": "5660", "name_ar": "رواتب ومكافآت الكوادر التعليمية", "name_en": "Educational Staff Salaries", 
			 "type": "Expense", "is_group": True, "parent_code": "5650", "level": 3},
			
			{"code": "5661", "name_ar": "رواتب الأساتذة والمعلمين", "name_en": "Teachers & Professors Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "5660", "level": 4},
			
			{"code": "5662", "name_ar": "رواتب الإداريين والمشرفين", "name_en": "Administrators & Supervisors", 
			 "type": "Expense", "is_group": False, "parent_code": "5660", "level": 4},
			
			{"code": "5663", "name_ar": "رواتب الفنيين والمساعدين", "name_en": "Technicians & Assistants", 
			 "type": "Expense", "is_group": False, "parent_code": "5660", "level": 4},
			
			{"code": "5664", "name_ar": "مكافآت وحوافز تعليمية", "name_en": "Educational Bonuses & Incentives", 
			 "type": "Expense", "is_group": False, "parent_code": "5660", "level": 4},
			
			{"code": "5670", "name_ar": "مصاريف التشغيل والصيانة", "name_en": "Operation & Maintenance Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5650", "level": 3},
			
			{"code": "5671", "name_ar": "مصاريف صيانة المباني التعليمية", "name_en": "Educational Buildings Maintenance", 
			 "type": "Expense", "is_group": False, "parent_code": "5670", "level": 4},
			
			{"code": "5672", "name_ar": "مصاريف صيانة المعدات التعليمية", "name_en": "Educational Equipment Maintenance", 
			 "type": "Expense", "is_group": False, "parent_code": "5670", "level": 4},
			
			{"code": "5673", "name_ar": "مصاريف النظافة والتعقيم", "name_en": "Cleaning & Sterilization", 
			 "type": "Expense", "is_group": False, "parent_code": "5670", "level": 4},
			
			{"code": "5680", "name_ar": "مصاريف الأنشطة والبرامج", "name_en": "Activities & Programs Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5650", "level": 3},
			
			{"code": "5681", "name_ar": "مصاريف الرحلات والزيارات", "name_en": "Trips & Visits Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5680", "level": 4},
			
			{"code": "5682", "name_ar": "مصاريف الفعاليات والاحتفالات", "name_en": "Events & Celebrations", 
			 "type": "Expense", "is_group": False, "parent_code": "5680", "level": 4},
			
			{"code": "5683", "name_ar": "مصاريف المسابقات والمنافسات", "name_en": "Competitions & Contests", 
			 "type": "Expense", "is_group": False, "parent_code": "5680", "level": 4},
			
			{"code": "5684", "name_ar": "مصاريف المخيمات والأنشطة الصيفية", "name_en": "Camps & Summer Activities", 
			 "type": "Expense", "is_group": False, "parent_code": "5680", "level": 4},
			
			{"code": "5690", "name_ar": "مصاريف التكنولوجيا والتطوير", "name_en": "Technology & Development Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5650", "level": 3},
			
			{"code": "5691", "name_ar": "مصاريف منصات التعلم الإلكتروني", "name_en": "E-learning Platforms Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5690", "level": 4},
			
			{"code": "5692", "name_ar": "مصاريف تراخيص برامج تعليمية", "name_en": "Educational Software Licenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5690", "level": 4},
			
			{"code": "5693", "name_ar": "مصاريف البحث والتطوير التعليمي", "name_en": "Educational R&D Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5690", "level": 4},
			
			{"code": "5700", "name_ar": "إهلاك الأصول التعليمية", "name_en": "Educational Assets Depreciation", 
			 "type": "Expense", "is_group": True, "parent_code": "5650", "level": 3},
			
			{"code": "5701", "name_ar": "إهلاك المعدات التعليمية", "name_en": "Educational Equipment Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5700", "level": 4},
			
			{"code": "5702", "name_ar": "إهلاك المنصات الإلكترونية", "name_en": "Electronic Platforms Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5700", "level": 4},
			
			{"code": "5703", "name_ar": "إهلاك المكتبات والمصادر", "name_en": "Libraries & Resources Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5700", "level": 4},
			
			{"code": "5710", "name_ar": "مصاريف الاعتماد والجودة", "name_en": "Accreditation & Quality Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5650", "level": 3},
			
			{"code": "5711", "name_ar": "مصاريف الاعتماد الأكاديمي", "name_en": "Academic Accreditation Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5710", "level": 4},
			
			{"code": "5712", "name_ar": "مصاريف ضمان الجودة التعليمية", "name_en": "Educational Quality Assurance", 
			 "type": "Expense", "is_group": False, "parent_code": "5710", "level": 4},
			
			{"code": "5713", "name_ar": "مصاريف التقييم والاختبارات", "name_en": "Assessment & Testing Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5710", "level": 4},
		]
    
    @classmethod
    def get_logistics_extensions(cls) -> List[Dict]:
        """النقل والخدمات اللوجستية"""
        return [
			# ============ الأصول الثابتة - لوجستية (تحت 1100) ============
			{"code": "11116", "name_ar": "الأصول اللوجستية والنقل", "name_en": "Logistics & Transportation Assets", 
			 "type": "Asset", "is_group": True, "parent_code": "1100", "level": 3},
			
			{"code": "11961", "name_ar": "مركبات النقل البري", "name_en": "Ground Transportation Vehicles", 
			 "type": "Asset", "is_group": False, "parent_code": "11116", "level": 4},
			
			{"code": "11962", "name_ar": "معدات الموانئ والمطارات", "name_en": "Ports & Airports Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11116", "level": 4},
			
			{"code": "11963", "name_ar": "معدات التحميل والتفريغ", "name_en": "Loading & Unloading Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11116", "level": 4},
			
			{"code": "11964", "name_ar": "مركبات النقل الثقيل", "name_en": "Heavy Transport Vehicles", 
			 "type": "Asset", "is_group": False, "parent_code": "11116", "level": 4},
			
			{"code": "11965", "name_ar": "أنظمة التتبع والمراقبة", "name_en": "Tracking & Monitoring Systems", 
			 "type": "Asset", "is_group": False, "parent_code": "11116", "level": 4},
			
			# ============ الأصول المتداولة - لوجستية (تحت 1200) ============
			{"code": "12170", "name_ar": "مخزونات لوجستية", "name_en": "Logistics Inventory", 
			 "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
			
			{"code": "12171", "name_ar": "وقود وزيوت تشغيل", "name_en": "Fuel & Operating Oils", 
			 "type": "Asset", "is_group": False, "parent_code": "12170", "level": 4},
			
			{"code": "12172", "name_ar": "قطع غيار ولوازم صيانة", "name_en": "Spare Parts & Maintenance Supplies", 
			 "type": "Asset", "is_group": False, "parent_code": "12170", "level": 4},
			
			{"code": "12173", "name_ar": "مواد التعبئة والتغليف", "name_en": "Packaging & Wrapping Materials", 
			 "type": "Asset", "is_group": False, "parent_code": "12170", "level": 4},
			
			{"code": "12174", "name_ar": "أدوات وأجهزة السلامة", "name_en": "Safety Tools & Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "12170", "level": 4},
			
			{"code": "12175", "name_ar": "بضائع تحت النقل", "name_en": "Goods in Transit", 
			 "type": "Asset", "is_group": False, "parent_code": "12170", "level": 4},
			
			# ============ الخصوم - لوجستية (تحت 2100) ============
			{"code": "21130", "name_ar": "موردو الخدمات اللوجستية", "name_en": "Logistics Services Suppliers", 
			 "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
			
			{"code": "21131", "name_ar": "موردون وقود وزيوت", "name_en": "Fuel & Oils Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21130", "level": 4},
			
			{"code": "21132", "name_ar": "موردون قطع غيار", "name_en": "Spare Parts Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21130", "level": 4},
			
			{"code": "21133", "name_ar": "مقاولو نقل وبضائع", "name_en": "Transport & Freight Contractors", 
			 "type": "Liability", "is_group": True, "parent_code": "21130", "level": 4},
			
			{"code": "223031", "name_ar": "مقاولو نقل بري", "name_en": "Road Transport Contractors", 
			 "type": "Liability", "is_group": False, "parent_code": "22303", "level": 5},
			
			{"code": "223032", "name_ar": "مقاولو نقل بحري", "name_en": "Maritime Transport Contractors", 
			 "type": "Liability", "is_group": False, "parent_code": "22303", "level": 5},
			
			{"code": "223033", "name_ar": "مقاولو نقل جوي", "name_en": "Air Transport Contractors", 
			 "type": "Liability", "is_group": False, "parent_code": "22303", "level": 5},
			
			{"code": "22304", "name_ar": "موردون تأمينات لوجستية", "name_en": "Logistics Insurance Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "2230", "level": 4},
			
			# ============ الإيرادات - لوجستية (تحت 4000) ============
			{"code": "4900", "name_ar": "إيرادات الخدمات اللوجستية", "name_en": "Logistics Services Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4000", "level": 2},
			
			{"code": "4910", "name_ar": "إيرادات النقل البري", "name_en": "Road Transport Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4900", "level": 3},
			
			{"code": "4911", "name_ar": "إيرادات نقل البضائع", "name_en": "Freight Transport Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4910", "level": 4},
			
			{"code": "4912", "name_ar": "إيرادات نقل الركاب", "name_en": "Passenger Transport Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4910", "level": 4},
			
			{"code": "4913", "name_ar": "إيرادات النقل السريع", "name_en": "Express Delivery Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4910", "level": 4},
			
			{"code": "4920", "name_ar": "إيرادات النقل البحري", "name_en": "Maritime Transport Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4900", "level": 3},
			
			{"code": "4921", "name_ar": "إيرادات نقل الحاويات", "name_en": "Container Shipping Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4920", "level": 4},
			
			{"code": "4922", "name_ar": "إيرادات نقل البضائع السائبة", "name_en": "Bulk Cargo Shipping Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4920", "level": 4},
			
			{"code": "4923", "name_ar": "إيرادات خدمات الموانئ", "name_en": "Port Services Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4920", "level": 4},
			
			{"code": "4930", "name_ar": "إيرادات النقل الجوي", "name_en": "Air Transport Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4900", "level": 3},
			
			{"code": "4931", "name_ar": "إيرادات الشحن الجوي", "name_en": "Air Cargo Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4930", "level": 4},
			
			{"code": "4932", "name_ar": "إيرادات خدمات الشحن الجوي", "name_en": "Air Freight Services Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4930", "level": 4},
			
			{"code": "4933", "name_ar": "إيرادات خدمات المطارات", "name_en": "Airport Services Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4930", "level": 4},
			
			{"code": "4940", "name_ar": "إيرادات خدمات التخزين", "name_en": "Storage Services Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4900", "level": 3},
			
			{"code": "4941", "name_ar": "إيرادات تخزين البضائع", "name_en": "Goods Storage Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4940", "level": 4},
			
			{"code": "4942", "name_ar": "إيرادات تخزين مبرد", "name_en": "Cold Storage Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4940", "level": 4},
			
			{"code": "4943", "name_ar": "إيرادات تخزين خطير", "name_en": "Hazardous Materials Storage", 
			 "type": "Revenue", "is_group": False, "parent_code": "4940", "level": 4},
			
			{"code": "4950", "name_ar": "إيرادات الخدمات المساندة", "name_en": "Support Services Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4900", "level": 3},
			
			{"code": "4951", "name_ar": "إيرادات التغليف والتعبئة", "name_en": "Packaging & Packing Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4950", "level": 4},
			
			{"code": "4952", "name_ar": "إيرادات التوزيع والتوصيل", "name_en": "Distribution & Delivery Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4950", "level": 4},
			
			{"code": "4953", "name_ar": "إيرادات التخليص الجمركي", "name_en": "Customs Clearance Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4950", "level": 4},
			
			{"code": "4954", "name_ar": "إيرادات خدمات التتبع", "name_en": "Tracking Services Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4950", "level": 4},
			
			# ============ التكاليف - لوجستية (تحت 5000) ============
			{"code": "5720", "name_ar": "تكاليف الخدمات اللوجستية", "name_en": "Logistics Services Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
			
			{"code": "5730", "name_ar": "تكاليف الوقود والطاقة", "name_en": "Fuel & Energy Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5720", "level": 3},
			
			{"code": "5731", "name_ar": "تكلفة وقود الديزل", "name_en": "Diesel Fuel Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5730", "level": 4},
			
			{"code": "5732", "name_ar": "تكلفة وقود البنزين", "name_en": "Gasoline Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5730", "level": 4},
			
			{"code": "5733", "name_ar": "تكلفة الزيوت والشحوم", "name_en": "Oils & Lubricants Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5730", "level": 4},
			
			{"code": "5734", "name_ar": "تكلفة الغاز الطبيعي", "name_en": "Natural Gas Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5730", "level": 4},
			
			{"code": "5740", "name_ar": "تكاليف الصيانة والإصلاح", "name_en": "Maintenance & Repair Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5720", "level": 3},
			
			{"code": "5741", "name_ar": "تكلفة صيانة المركبات", "name_en": "Vehicle Maintenance Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5740", "level": 4},
			
			{"code": "5742", "name_ar": "تكلفة قطع الغيار", "name_en": "Spare Parts Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5740", "level": 4},
			
			{"code": "5743", "name_ar": "تكلفة إصلاح المعدات", "name_en": "Equipment Repair Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5740", "level": 4},
			
			{"code": "5744", "name_ar": "تكلفة الإطارات والبطاريات", "name_en": "Tires & Batteries Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5740", "level": 4},
			
			{"code": "5750", "name_ar": "تكاليف التشغيل والعمليات", "name_en": "Operation & Processing Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5720", "level": 3},
			
			{"code": "5751", "name_ar": "تكلفة استئجار المركبات", "name_en": "Vehicle Rental Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5750", "level": 4},
			
			{"code": "5752", "name_ar": "تكلفة رسوم الطرق والجسور", "name_en": "Road & Bridge Tolls", 
			 "type": "Expense", "is_group": False, "parent_code": "5750", "level": 4},
			
			{"code": "5753", "name_ar": "تكلفة خدمات الموانئ والمطارات", "name_en": "Ports & Airports Services", 
			 "type": "Expense", "is_group": False, "parent_code": "5750", "level": 4},
			
			{"code": "5754", "name_ar": "تكلفة التخليص الجمركي", "name_en": "Customs Clearance Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5750", "level": 4},
			
			# ============ المصروفات - لوجستية (تحت 5000) ============
			{"code": "5760", "name_ar": "مصاريف تشغيلية - لوجستية", "name_en": "Operational Expenses - Logistics", 
			 "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
			
			{"code": "5770", "name_ar": "رواتب ومكافآت العاملين", "name_en": "Employee Salaries & Bonuses", 
			 "type": "Expense", "is_group": True, "parent_code": "5760", "level": 3},
			
			{"code": "5771", "name_ar": "رواتب السائقين والمشغلين", "name_en": "Drivers & Operators Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "5770", "level": 4},
			
			{"code": "5772", "name_ar": "رواتب فنيي الصيانة", "name_en": "Maintenance Technicians Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "5770", "level": 4},
			
			{"code": "5773", "name_ar": "رواتب الإداريين والمشرفين", "name_en": "Administrators & Supervisors", 
			 "type": "Expense", "is_group": False, "parent_code": "5770", "level": 4},
			
			{"code": "5774", "name_ar": "مكافآت وحوافز الأداء", "name_en": "Performance Bonuses & Incentives", 
			 "type": "Expense", "is_group": False, "parent_code": "5770", "level": 4},
			
			{"code": "5780", "name_ar": "مصاريف التأمين والامتثال", "name_en": "Insurance & Compliance Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5760", "level": 3},
			
			{"code": "5781", "name_ar": "مصاريف تأمين المركبات", "name_en": "Vehicle Insurance", 
			 "type": "Expense", "is_group": False, "parent_code": "5780", "level": 4},
			
			{"code": "5782", "name_ar": "مصاريف تأمين البضائع", "name_en": "Cargo Insurance", 
			 "type": "Expense", "is_group": False, "parent_code": "5780", "level": 4},
			
			{"code": "5783", "name_ar": "مصاريف تأمين المسؤولية", "name_en": "Liability Insurance", 
			 "type": "Expense", "is_group": False, "parent_code": "5780", "level": 4},
			
			{"code": "5784", "name_ar": "مصاريف التراخيص والتصاريح", "name_en": "Licenses & Permits", 
			 "type": "Expense", "is_group": False, "parent_code": "5780", "level": 4},
			
			{"code": "5790", "name_ar": "مصاريف السلامة والبيئة", "name_en": "Safety & Environmental Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5760", "level": 3},
			
			{"code": "5791", "name_ar": "مصاريف أدوات السلامة", "name_en": "Safety Equipment Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5790", "level": 4},
			
			{"code": "5792", "name_ar": "مصاريف التدريب على السلامة", "name_en": "Safety Training Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5790", "level": 4},
			
			{"code": "5793", "name_ar": "مصاريف الحماية البيئية", "name_en": "Environmental Protection", 
			 "type": "Expense", "is_group": False, "parent_code": "5790", "level": 4},
			
			{"code": "5794", "name_ar": "مصاريف التخلص من النفايات", "name_en": "Waste Disposal Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5790", "level": 4},
			
			{"code": "5800", "name_ar": "مصاريف التكنولوجيا والتتبع", "name_en": "Technology & Tracking Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5760", "level": 3},
			
			{"code": "5801", "name_ar": "مصاريف أنظمة التتبع", "name_en": "Tracking Systems Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5800", "level": 4},
			
			{"code": "5802", "name_ar": "مصاريف برامج إدارة النقل", "name_en": "Transport Management Software", 
			 "type": "Expense", "is_group": False, "parent_code": "5800", "level": 4},
			
			{"code": "5803", "name_ar": "مصاريف أنظمة الاتصالات", "name_en": "Communication Systems Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5800", "level": 4},
			
			{"code": "5810", "name_ar": "إهلاك الأصول اللوجستية", "name_en": "Logistics Assets Depreciation", 
			 "type": "Expense", "is_group": True, "parent_code": "5760", "level": 3},
			
			{"code": "5811", "name_ar": "إهلاك مركبات النقل", "name_en": "Transport Vehicles Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5810", "level": 4},
			
			{"code": "5812", "name_ar": "إهلاك معدات الموانئ", "name_en": "Port Equipment Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5810", "level": 4},
			
			{"code": "5813", "name_ar": "إهلاك معدات التحميل", "name_en": "Loading Equipment Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5810", "level": 4},
			
			{"code": "5814", "name_ar": "إهلاك أنظمة التتبع", "name_en": "Tracking Systems Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5810", "level": 4},
		]
    
    @classmethod
    def get_energy_extensions(cls) -> List[Dict]:
        """الطاقة والبيئة"""
        return [
			# ============ الأصول الثابتة - الطاقة (تحت 1100) ============
			{"code": "11128", "name_ar": "الأصول الطاقية والبيئية", "name_en": "Energy & Environmental Assets", 
			 "type": "Asset", "is_group": True, "parent_code": "1100", "level": 3},
			
			{"code": "11981", "name_ar": "معدات ومحطات توليد الطاقة", "name_en": "Power Generation Equipment & Plants", 
			 "type": "Asset", "is_group": False, "parent_code": "11128", "level": 4},
			
			{"code": "11982", "name_ar": "محطات الطاقة المتجددة", "name_en": "Renewable Energy Plants", 
			 "type": "Asset", "is_group": False, "parent_code": "11128", "level": 4},
			
			{"code": "11983", "name_ar": "معدات النقل والتوزيع", "name_en": "Transmission & Distribution Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11128", "level": 4},
			
			{"code": "11984", "name_ar": "معدات المعالجة والتكرير", "name_en": "Processing & Refining Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11128", "level": 4},
			
			{"code": "11985", "name_ar": "معدات الرصد والمراقبة", "name_en": "Monitoring & Surveillance Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11128", "level": 4},
			
			{"code": "11986", "name_ar": "معدات إدارة النفايات", "name_en": "Waste Management Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11128", "level": 4},
			
			{"code": "11987", "name_ar": "معدات معالجة المياه", "name_en": "Water Treatment Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11128", "level": 4},
			
			# ============ الأصول المتداولة - الطاقة (تحت 1200) ============
			{"code": "12180", "name_ar": "مخزونات الطاقة والمواد", "name_en": "Energy & Materials Inventory", 
			 "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
			
			{"code": "12181", "name_ar": "مخزون الوقود التقليدي", "name_en": "Conventional Fuel Inventory", 
			 "type": "Asset", "is_group": False, "parent_code": "12180", "level": 4},
			
			{"code": "12182", "name_ar": "مخزون المواد الخام الطاقة", "name_en": "Energy Raw Materials Inventory", 
			 "type": "Asset", "is_group": False, "parent_code": "12180", "level": 4},
			
			{"code": "12183", "name_ar": "مخزون المواد الكيميائية", "name_en": "Chemical Materials Inventory", 
			 "type": "Asset", "is_group": False, "parent_code": "12180", "level": 4},
			
			{"code": "12184", "name_ar": "مخزون قطع الغيار", "name_en": "Spare Parts Inventory", 
			 "type": "Asset", "is_group": False, "parent_code": "12180", "level": 4},
			
			{"code": "12185", "name_ar": "مخزون مواد الصيانة", "name_en": "Maintenance Materials Inventory", 
			 "type": "Asset", "is_group": False, "parent_code": "12180", "level": 4},
			
			# ============ الخصوم - الطاقة (تحت 2100) ============
			{"code": "21140", "name_ar": "موردو الطاقة والبيئة", "name_en": "Energy & Environmental Suppliers", 
			 "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
			
			{"code": "21141", "name_ar": "موردون وقود وطاقة", "name_en": "Fuel & Energy Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21140", "level": 4},
			
			{"code": "21142", "name_ar": "موردون معدات طاقية", "name_en": "Energy Equipment Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21140", "level": 4},
			
			{"code": "21143", "name_ar": "موردون مواد كيميائية", "name_en": "Chemical Materials Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21140", "level": 4},
			
			{"code": "21144", "name_ar": "موردون خدمات بيئية", "name_en": "Environmental Services Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21140", "level": 4},
			
			{"code": "21145", "name_ar": "مقاولو الصيانة والتشغيل", "name_en": "Maintenance & Operation Contractors", 
			 "type": "Liability", "is_group": True, "parent_code": "21140", "level": 4},
			
			{"code": "211451", "name_ar": "مقاولو صيانة المعدات", "name_en": "Equipment Maintenance Contractors", 
			 "type": "Liability", "is_group": False, "parent_code": "21145", "level": 5},
			
			{"code": "211452", "name_ar": "مقاولو عمليات التشغيل", "name_en": "Operation Contractors", 
			 "type": "Liability", "is_group": False, "parent_code": "21145", "level": 5},
			
			# ============ الإيرادات - الطاقة (تحت 4000) ============
			{"code": "5010", "name_ar": "إيرادات الطاقة والبيئة", "name_en": "Energy & Environmental Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4000", "level": 2},
			
			{"code": "5020", "name_ar": "إيرادات توليد الطاقة", "name_en": "Power Generation Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "5010", "level": 3},
			
			{"code": "5021", "name_ar": "إيرادات الطاقة التقليدية", "name_en": "Conventional Energy Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5020", "level": 4},
			
			{"code": "5022", "name_ar": "إيرادات الطاقة المتجددة", "name_en": "Renewable Energy Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5020", "level": 4},
			
			{"code": "5023", "name_ar": "إيرادات بيع الكهرباء", "name_en": "Electricity Sales Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5020", "level": 4},
			
			{"code": "5024", "name_ar": "إيرادات الطاقة الحرارية", "name_en": "Thermal Energy Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5020", "level": 4},
			
			{"code": "5030", "name_ar": "إيرادات النفط والغاز", "name_en": "Oil & Gas Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "5010", "level": 3},
			
			{"code": "5031", "name_ar": "إيرادات بيع النفط الخام", "name_en": "Crude Oil Sales Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5030", "level": 4},
			
			{"code": "5032", "name_ar": "إيرادات بيع المنتجات البترولية", "name_en": "Petroleum Products Sales Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5030", "level": 4},
			
			{"code": "5033", "name_ar": "إيرادات بيع الغاز الطبيعي", "name_en": "Natural Gas Sales Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5030", "level": 4},
			
			{"code": "5034", "name_ar": "إيرادات خدمات التكرير", "name_en": "Refining Services Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5030", "level": 4},
			
			{"code": "5040", "name_ar": "إيرادات الخدمات البيئية", "name_en": "Environmental Services Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "5010", "level": 3},
			
			{"code": "5041", "name_ar": "إيرادات معالجة المياه", "name_en": "Water Treatment Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5040", "level": 4},
			
			{"code": "5042", "name_ar": "إيرادات إدارة النفايات", "name_en": "Waste Management Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5040", "level": 4},
			
			{"code": "5043", "name_ar": "إيرادات إعادة التدوير", "name_en": "Recycling Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5040", "level": 4},
			
			{"code": "5044", "name_ar": "إيرادات الاستشارات البيئية", "name_en": "Environmental Consulting Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5040", "level": 4},
			
			{"code": "5050", "name_ar": "إيرادات الخدمات الفنية", "name_en": "Technical Services Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "5010", "level": 3},
			
			{"code": "5051", "name_ar": "إيرادات الصيانة والتشغيل", "name_en": "Maintenance & Operation Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5050", "level": 4},
			
			{"code": "5052", "name_ar": "إيرادات الفحوصات والاختبارات", "name_en": "Inspections & Tests Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5050", "level": 4},
			
			{"code": "5053", "name_ar": "إيرادات تركيب المعدات", "name_en": "Equipment Installation Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5050", "level": 4},
			
			{"code": "5054", "name_ar": "إيرادات التدريب والاستشارات", "name_en": "Training & Consulting Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5050", "level": 4},
			
			# ============ التكاليف - الطاقة (تحت 5000) ============
			{"code": "5920", "name_ar": "تكاليف الطاقة والبيئة", "name_en": "Energy & Environmental Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
			
			{"code": "5930", "name_ar": "تكاليف الوقود والطاقة", "name_en": "Fuel & Energy Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5920", "level": 3},
			
			{"code": "5931", "name_ar": "تكلفة الوقود التقليدي", "name_en": "Conventional Fuel Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5930", "level": 4},
			
			{"code": "5932", "name_ar": "تكلفة المواد الخام", "name_en": "Raw Materials Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5930", "level": 4},
			
			{"code": "5933", "name_ar": "تكلفة الطاقة المشتراة", "name_en": "Purchased Energy Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5930", "level": 4},
			
			{"code": "5934", "name_ar": "تكلفة المواد الكيميائية", "name_en": "Chemical Materials Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5930", "level": 4},
			
			{"code": "5940", "name_ar": "تكاليف التشغيل والإنتاج", "name_en": "Operation & Production Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5920", "level": 3},
			
			{"code": "5941", "name_ar": "تكلفة معالجة المواد", "name_en": "Materials Processing Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5940", "level": 4},
			
			{"code": "5942", "name_ar": "تكلفة عمليات التكرير", "name_en": "Refining Operations Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5940", "level": 4},
			
			{"code": "5943", "name_ar": "تكلفة توليد الطاقة", "name_en": "Power Generation Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5940", "level": 4},
			
			{"code": "5944", "name_ar": "تكلفة النقل والتوزيع", "name_en": "Transportation & Distribution Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5940", "level": 4},
			
			# ============ المصروفات - الطاقة (تحت 5000) ============
			{"code": "5950", "name_ar": "مصاريف تشغيلية - طاقة", "name_en": "Operational Expenses - Energy", 
			 "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
			
			{"code": "5960", "name_ar": "رواتب ومكافآت العاملين", "name_en": "Employee Salaries & Bonuses", 
			 "type": "Expense", "is_group": True, "parent_code": "5950", "level": 3},
			
			{"code": "5961", "name_ar": "رواتب المهندسين والفنيين", "name_en": "Engineers & Technicians Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "5960", "level": 4},
			
			{"code": "5962", "name_ar": "رواتب مشغلي المعدات", "name_en": "Equipment Operators Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "5960", "level": 4},
			
			{"code": "5963", "name_ar": "رواتب الإداريين والمشرفين", "name_en": "Administrators & Supervisors", 
			 "type": "Expense", "is_group": False, "parent_code": "5960", "level": 4},
			
			{"code": "5964", "name_ar": "رواتب طاقم الصيانة", "name_en": "Maintenance Staff Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "5960", "level": 4},
			
			{"code": "5970", "name_ar": "مصاريف الصيانة والإصلاح", "name_en": "Maintenance & Repair Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5950", "level": 3},
			
			{"code": "5971", "name_ar": "مصاريف صيانة المعدات", "name_en": "Equipment Maintenance Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5970", "level": 4},
			
			{"code": "5972", "name_ar": "مصاريف إصلاح الأعطال", "name_en": "Breakdown Repair Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5970", "level": 4},
			
			{"code": "5973", "name_ar": "مصاريف الصيانة الوقائية", "name_en": "Preventive Maintenance Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5970", "level": 4},
			
			{"code": "5974", "name_ar": "مصاريف قطع الغيار", "name_en": "Spare Parts Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5970", "level": 4},
			
			{"code": "5980", "name_ar": "مصاريف البيئة والسلامة", "name_en": "Environmental & Safety Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5950", "level": 3},
			
			{"code": "5981", "name_ar": "مصاريف الرصد البيئي", "name_en": "Environmental Monitoring Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5980", "level": 4},
			
			{"code": "5982", "name_ar": "مصاريف معالجة التلوث", "name_en": "Pollution Treatment Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5980", "level": 4},
			
			{"code": "5983", "name_ar": "مصاريف السلامة الصناعية", "name_en": "Industrial Safety Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5980", "level": 4},
			
			{"code": "5984", "name_ar": "مصاريف التخلص من النفايات", "name_en": "Waste Disposal Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5980", "level": 4},
			
			{"code": "5990", "name_ar": "مصاريف البحث والتطوير", "name_en": "Research & Development Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5950", "level": 3},
			
			{"code": "5991", "name_ar": "مصاريف البحوث الطاقية", "name_en": "Energy Research Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5990", "level": 4},
			
			{"code": "5992", "name_ar": "مصاريف تطوير التقنيات", "name_en": "Technology Development Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5990", "level": 4},
			
			{"code": "5993", "name_ar": "مصاريف اختبارات الجودة", "name_en": "Quality Testing Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5990", "level": 4},
			
			{"code": "5994", "name_ar": "مصاريف براءات الاختراع", "name_en": "Patents Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5990", "level": 4},
			
			{"code": "6000", "name_ar": "مصاريف التراخيص والامتثال", "name_en": "Licenses & Compliance Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5950", "level": 3},
			
			{"code": "6001", "name_ar": "مصاريف التراخيص البيئية", "name_en": "Environmental Licenses Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6000", "level": 4},
			
			{"code": "6002", "name_ar": "مصاريف تراخيص التشغيل", "name_en": "Operation Licenses Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6000", "level": 4},
			
			{"code": "6003", "name_ar": "مصاريف الامتثال التنظيمي", "name_en": "Regulatory Compliance Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6000", "level": 4},
			
			{"code": "6004", "name_ar": "مصاريف التدقيق والمراجعة", "name_en": "Audit & Review Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6000", "level": 4},
			
			{"code": "6010", "name_ar": "إهلاك الأصول الطاقية", "name_en": "Energy Assets Depreciation", 
			 "type": "Expense", "is_group": True, "parent_code": "5950", "level": 3},
			
			{"code": "6011", "name_ar": "إهلاك معدات التوليد", "name_en": "Generation Equipment Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "6010", "level": 4},
			
			{"code": "6012", "name_ar": "إهلاك محطات الطاقة", "name_en": "Power Plants Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "6010", "level": 4},
			
			{"code": "6013", "name_ar": "إهلاك معدات النقل", "name_en": "Transmission Equipment Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "6010", "level": 4},
			
			{"code": "6014", "name_ar": "إهلاك معدات المعالجة", "name_en": "Processing Equipment Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "6010", "level": 4},
		]
    
    
    @classmethod
    def get_hospitality_extensions(cls) -> List[Dict]:
        """الضيافة والسياحة"""
        return [
			# ============ الأصول الثابتة - ضيافة (تحت 1100) ============
			{"code": "11137", "name_ar": "الأصول الفندقية والضيافية", "name_en": "Hospitality & Hotel Assets", 
			 "type": "Asset", "is_group": True, "parent_code": "1100", "level": 3},
			
			{"code": "11971", "name_ar": "مباني وأثاث الفنادق", "name_en": "Hotel Buildings & Furniture", 
			 "type": "Asset", "is_group": False, "parent_code": "11137", "level": 4},
			
			{"code": "11972", "name_ar": "تجهيزات المطاعم والكافتيريات", "name_en": "Restaurant & Cafeteria Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11137", "level": 4},
			
			{"code": "11973", "name_ar": "أجهزة ومعدات المطابخ", "name_en": "Kitchen Equipment & Appliances", 
			 "type": "Asset", "is_group": False, "parent_code": "11137", "level": 4},
			
			{"code": "11974", "name_ar": "مركبات النقل الفندقي", "name_en": "Hotel Transportation Vehicles", 
			 "type": "Asset", "is_group": False, "parent_code": "11137", "level": 4},
			
			{"code": "11975", "name_ar": "أنظمة الترفيه والترفيه", "name_en": "Entertainment & Recreation Systems", 
			 "type": "Asset", "is_group": False, "parent_code": "11137", "level": 4},
			
			{"code": "11976", "name_ar": "معدات المؤتمرات والفعاليات", "name_en": "Conference & Events Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11137", "level": 4},
			
			# ============ الأصول المتداولة - ضيافة (تحت 1200) ============
			{"code": "12190", "name_ar": "مخزونات الضيافة والفندقة", "name_en": "Hospitality & Hotel Inventory", 
			 "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
			
			{"code": "12191", "name_ar": "مخزون المواد الغذائية", "name_en": "Food & Beverage Inventory", 
			 "type": "Asset", "is_group": False, "parent_code": "12190", "level": 4},
			
			{"code": "12192", "name_ar": "مخزون مواد النظافة والتعقيم", "name_en": "Cleaning & Sterilization Inventory", 
			 "type": "Asset", "is_group": False, "parent_code": "12190", "level": 4},
			
			{"code": "12193", "name_ar": "مخزون مستلزمات الغرف", "name_en": "Room Supplies Inventory", 
			 "type": "Asset", "is_group": False, "parent_code": "12190", "level": 4},
			
			{"code": "12194", "name_ar": "مخزون أدوات المطبخ", "name_en": "Kitchen Utensils Inventory", 
			 "type": "Asset", "is_group": False, "parent_code": "12190", "level": 4},
			
			{"code": "12195", "name_ar": "مخزون مواد الترفيه", "name_en": "Entertainment Materials Inventory", 
			 "type": "Asset", "is_group": False, "parent_code": "12190", "level": 4},
			
			# ============ الخصوم - ضيافة (تحت 2100) ============
			{"code": "21150", "name_ar": "موردو الخدمات الفندقية", "name_en": "Hotel Services Suppliers", 
			 "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
			
			{"code": "21150", "name_ar": "موردون مواد غذائية", "name_en": "Food & Beverage Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21150", "level": 4},
			
			{"code": "21151", "name_ar": "موردون تجهيزات فندقية", "name_en": "Hotel Equipment Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21150", "level": 4},
			
			{"code": "21152", "name_ar": "موردون خدمات النظافة", "name_en": "Cleaning Services Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21150", "level": 4},
			
			{"code": "21153", "name_ar": "موردون خدمات الأمن", "name_en": "Security Services Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21150", "level": 4},
			
			{"code": "21154", "name_ar": "موردون خدمات الترفيه", "name_en": "Entertainment Services Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21150", "level": 4},
			
			# ============ الإيرادات - ضيافة (تحت 4000) ============
			{"code": "4960", "name_ar": "إيرادات الخدمات الفندقية", "name_en": "Hotel Services Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4000", "level": 2},
			
			{"code": "4970", "name_ar": "إيرادات الإقامة", "name_en": "Accommodation Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4960", "level": 3},
			
			{"code": "4971", "name_ar": "إيرادات حجز الغرف", "name_en": "Room Booking Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4970", "level": 4},
			
			{"code": "4972", "name_ar": "إيرادات الإقامة الطويلة", "name_en": "Long-term Stay Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4970", "level": 4},
			
			{"code": "4973", "name_ar": "إيرادات الأجنحة الفاخرة", "name_en": "Luxury Suites Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4970", "level": 4},
			
			{"code": "4974", "name_ar": "إيرادات خدمات الغرف", "name_en": "Room Service Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4970", "level": 4},
			
			{"code": "4980", "name_ar": "إيرادات الطعام والشراب", "name_en": "Food & Beverage Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4960", "level": 3},
			
			{"code": "4981", "name_ar": "إيرادات المطاعم", "name_en": "Restaurant Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4980", "level": 4},
			
			{"code": "4982", "name_ar": "إيرادات الكافيهات", "name_en": "Café Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4980", "level": 4},
			
			{"code": "4983", "name_ar": "إيرادات الحفلات والمناسبات", "name_en": "Parties & Events Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4980", "level": 4},
			
			{"code": "4984", "name_ar": "إيرادات المطابخ الخارجية", "name_en": "Catering Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4980", "level": 4},
			
			{"code": "4990", "name_ar": "إيرادات الترفيه والخدمات", "name_en": "Entertainment & Services Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4960", "level": 3},
			
			{"code": "4991", "name_ar": "إيرادات المسابح والمنتجعات", "name_en": "Pools & Resorts Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4990", "level": 4},
			
			{"code": "4992", "name_ar": "إيرادات الصالات الرياضية", "name_en": "Gyms & Fitness Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4990", "level": 4},
			
			{"code": "4993", "name_ar": "إيرادات السبا والعناية", "name_en": "Spa & Care Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4990", "level": 4},
			
			{"code": "4994", "name_ar": "إيرادات خدمات الأعمال", "name_en": "Business Services Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4990", "level": 4},
			
			{"code": "4995", "name_ar": "إيرادات خدمات الغسيل", "name_en": "Laundry Services Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "4990", "level": 4},
			
			{"code": "5001", "name_ar": "إيرادات المؤتمرات والفعاليات", "name_en": "Conferences & Events Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4960", "level": 3},
			
			{"code": "5002", "name_ar": "إيرادات قاعات المؤتمرات", "name_en": "Conference Halls Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5001", "level": 4},
			
			{"code": "5003", "name_ar": "إيرادات حفلات الزفاف", "name_en": "Wedding Parties Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5001", "level": 4},
			
			{"code": "5004", "name_ar": "إيرادات المعارض والعروض", "name_en": "Exhibitions & Shows Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5001", "level": 4},
			
			{"code": "5005", "name_ar": "إيرادات خدمات التنظيم", "name_en": "Organization Services Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5001", "level": 4},
			
			# ============ التكاليف - ضيافة (تحت 5000) ============
			{"code": "5820", "name_ar": "تكاليف الخدمات الفندقية", "name_en": "Hotel Services Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
			
			{"code": "5830", "name_ar": "تكاليف المواد الغذائية", "name_en": "Food & Beverage Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5820", "level": 3},
			
			{"code": "5831", "name_ar": "تكلفة المواد الغذائية المستخدمة", "name_en": "Food & Beverage Consumed", 
			 "type": "Expense", "is_group": False, "parent_code": "5830", "level": 4},
			
			{"code": "5832", "name_ar": "تكلفة المواد الاستهلاكية", "name_en": "Consumables Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5830", "level": 4},
			
			{"code": "5833", "name_ar": "تكلفة المواد الترفيهية", "name_en": "Entertainment Materials Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5830", "level": 4},
			
			{"code": "5834", "name_ar": "تكلفة المشروبات والكحوليات", "name_en": "Beverages & Alcohol Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5830", "level": 4},
			
			{"code": "5840", "name_ar": "تكاليف التشغيل اليومي", "name_en": "Daily Operation Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5820", "level": 3},
			
			{"code": "5841", "name_ar": "تكلفة خدمات النظافة", "name_en": "Cleaning Services Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5840", "level": 4},
			
			{"code": "5842", "name_ar": "تكلفة مواد النظافة", "name_en": "Cleaning Materials Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5840", "level": 4},
			
			{"code": "5843", "name_ar": "تكلفة خدمات الغسيل", "name_en": "Laundry Services Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5840", "level": 4},
			
			{"code": "5844", "name_ar": "تكلفة الأمن والحماية", "name_en": "Security & Protection Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "5840", "level": 4},
			
			# ============ المصروفات - ضيافة (تحت 5000) ============
			{"code": "5850", "name_ar": "مصاريف تشغيلية - فندقية", "name_en": "Operational Expenses - Hotel", 
			 "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
			
			{"code": "5860", "name_ar": "رواتب ومكافآت العاملين", "name_en": "Employee Salaries & Bonuses", 
			 "type": "Expense", "is_group": True, "parent_code": "5850", "level": 3},
			
			{"code": "5861", "name_ar": "رواتب طاقم المطبخ", "name_en": "Kitchen Staff Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "5860", "level": 4},
			
			{"code": "5862", "name_ar": "رواتب طاقم الخدمة", "name_en": "Service Staff Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "5860", "level": 4},
			
			{"code": "5863", "name_ar": "رواتب الإداريين والمشرفين", "name_en": "Administrators & Supervisors", 
			 "type": "Expense", "is_group": False, "parent_code": "5860", "level": 4},
			
			{"code": "5864", "name_ar": "رواتب طاقم النظافة", "name_en": "Cleaning Staff Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "5860", "level": 4},
			
			{"code": "5865", "name_ar": "رواتب طاقم الأمن", "name_en": "Security Staff Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "5860", "level": 4},
			
			{"code": "5870", "name_ar": "مصاريف التسويق والترويج", "name_en": "Marketing & Promotion Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5850", "level": 3},
			
			{"code": "5871", "name_ar": "مصاريف الإعلانات الفندقية", "name_en": "Hotel Advertising Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5870", "level": 4},
			
			{"code": "5872", "name_ar": "مصاريف منصات الحجز", "name_en": "Booking Platforms Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5870", "level": 4},
			
			{"code": "5873", "name_ar": "مصاريف العلاقات العامة", "name_en": "Public Relations Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5870", "level": 4},
			
			{"code": "5874", "name_ar": "مصاريف العروض الترويجية", "name_en": "Promotional Offers Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5870", "level": 4},
			
			{"code": "5880", "name_ar": "مصاريف التشغيل والصيانة", "name_en": "Operation & Maintenance Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5850", "level": 3},
			
			{"code": "5881", "name_ar": "مصاريف صيانة المباني", "name_en": "Building Maintenance Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5880", "level": 4},
			
			{"code": "5882", "name_ar": "مصاريف صيانة المعدات", "name_en": "Equipment Maintenance Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5880", "level": 4},
			
			{"code": "5883", "name_ar": "مصاريف المرافق والخدمات", "name_en": "Utilities & Services Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5880", "level": 4},
			
			{"code": "5884", "name_ar": "مصاريف قطع الغيار", "name_en": "Spare Parts Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5880", "level": 4},
			
			{"code": "5890", "name_ar": "مصاريف الجودة والامتثال", "name_en": "Quality & Compliance Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5850", "level": 3},
			
			{"code": "5891", "name_ar": "مصاريف شهادات الجودة", "name_en": "Quality Certificates Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5890", "level": 4},
			
			{"code": "5892", "name_ar": "مصاريف التدريب والتأهيل", "name_en": "Training & Qualification Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5890", "level": 4},
			
			{"code": "5893", "name_ar": "مصاريف الفحوصات الصحية", "name_en": "Health Inspections Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5890", "level": 4},
			
			{"code": "5894", "name_ar": "مصاريف التأمينات والتراخيص", "name_en": "Insurance & Licenses Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5890", "level": 4},
			
			{"code": "5900", "name_ar": "مصاريف التكنولوجيا والأنظمة", "name_en": "Technology & Systems Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "5850", "level": 3},
			
			{"code": "5901", "name_ar": "مصاريف أنظمة الحجز", "name_en": "Booking Systems Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5900", "level": 4},
			
			{"code": "5902", "name_ar": "مصاريف أنظمة إدارة الفنادق", "name_en": "Hotel Management Systems", 
			 "type": "Expense", "is_group": False, "parent_code": "5900", "level": 4},
			
			{"code": "5903", "name_ar": "مصاريف أنظمة الأمن والمراقبة", "name_en": "Security & Surveillance Systems", 
			 "type": "Expense", "is_group": False, "parent_code": "5900", "level": 4},
			
			{"code": "5904", "name_ar": "مصاريف أنظمة الاتصالات", "name_en": "Communication Systems Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "5900", "level": 4},
			
			{"code": "5910", "name_ar": "إهلاك الأصول الفندقية", "name_en": "Hotel Assets Depreciation", 
			 "type": "Expense", "is_group": True, "parent_code": "5850", "level": 3},
			
			{"code": "5911", "name_ar": "إهلاك المباني والأثاث", "name_en": "Buildings & Furniture Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5910", "level": 4},
			
			{"code": "5912", "name_ar": "إهلاك معدات المطابخ", "name_en": "Kitchen Equipment Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5910", "level": 4},
			
			{"code": "5913", "name_ar": "إهلاك أنظمة الترفيه", "name_en": "Entertainment Systems Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5910", "level": 4},
			
			{"code": "5914", "name_ar": "إهلاك معدات المؤتمرات", "name_en": "Conference Equipment Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "5910", "level": 4},
		]
    
    
    @classmethod
    def get_media_extensions(cls) -> List[Dict]:
        """وسائل الإعلام والترفيه"""
        return [
			# ============ الأصول الثابتة - إعلامية (تحت 1100) ============
			{"code": "11149", "name_ar": "الأصول الإعلامية والإنتاجية", "name_en": "Media & Production Assets", 
			 "type": "Asset", "is_group": True, "parent_code": "1100", "level": 3},
			
			{"code": "11991", "name_ar": "معدات الإنتاج والتسجيل", "name_en": "Production & Recording Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11149", "level": 4},
			
			{"code": "11992", "name_ar": "معدات البث والإرسال", "name_en": "Broadcasting & Transmission Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11149", "level": 4},
			
			{"code": "11993", "name_ar": "معدات التصوير والمونتاج", "name_en": "Filming & Editing Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11149", "level": 4},
			
			{"code": "11994", "name_ar": "استوديوهات ومكاتب إنتاج", "name_en": "Studios & Production Offices", 
			 "type": "Asset", "is_group": False, "parent_code": "11149", "level": 4},
			
			{"code": "11995", "name_ar": "أنظمة الحوسبة والخوادم", "name_en": "Computing Systems & Servers", 
			 "type": "Asset", "is_group": False, "parent_code": "11149", "level": 4},
			
			{"code": "11996", "name_ar": "برامج وتطبيقات إنتاجية", "name_en": "Production Software & Applications", 
			 "type": "Asset", "is_group": False, "parent_code": "11149", "level": 4},
			
			{"code": "11997", "name_ar": "معدات الصوت والإضاءة", "name_en": "Sound & Lighting Equipment", 
			 "type": "Asset", "is_group": False, "parent_code": "11149", "level": 4},
			
			# ============ الأصول المتداولة - إعلامية (تحت 1200) ============
			{"code": "12200", "name_ar": "مخزونات إعلامية وإنتاجية", "name_en": "Media & Production Inventory", 
			 "type": "Asset", "is_group": True, "parent_code": "1200", "level": 3},
			
			{"code": "12201", "name_ar": "مواد وأشرطة تسجيل", "name_en": "Recording Materials & Tapes", 
			 "type": "Asset", "is_group": False, "parent_code": "12200", "level": 4},
			
			{"code": "12202", "name_ar": "مستلزمات إنتاج وأدوات", "name_en": "Production Supplies & Tools", 
			 "type": "Asset", "is_group": False, "parent_code": "12200", "level": 4},
			
			{"code": "12203", "name_ar": "حقوق ملكية فكرية", "name_en": "Intellectual Property Rights", 
			 "type": "Asset", "is_group": False, "parent_code": "12200", "level": 4},
			
			{"code": "12204", "name_ar": "محتوى جاهز للإنتاج", "name_en": "Ready-to-Produce Content", 
			 "type": "Asset", "is_group": False, "parent_code": "12200", "level": 4},
			
			{"code": "12205", "name_ar": "إعلانات ومواد ترويجية", "name_en": "Advertisements & Promotional Materials", 
			 "type": "Asset", "is_group": False, "parent_code": "12200", "level": 4},
			
			# ============ الخصوم - إعلامية (تحت 2100) ============
			{"code": "21160", "name_ar": "موردو الخدمات الإعلامية", "name_en": "Media Services Suppliers", 
			 "type": "Liability", "is_group": True, "parent_code": "2100", "level": 3},
			
			{"code": "211601", "name_ar": "موردون معدات إنتاجية", "name_en": "Production Equipment Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21160", "level": 4},
			
			{"code": "211602", "name_ar": "موردون برامج وتطبيقات", "name_en": "Software & Applications Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "21160", "level": 4},
			
			{"code": "211603", "name_ar": "مقاولو إنتاج ومحتوى", "name_en": "Production & Content Contractors", 
			 "type": "Liability", "is_group": True, "parent_code": "21160", "level": 4},
			
			{"code": "2116031", "name_ar": "مقاولو إنتاج أفلام", "name_en": "Film Production Contractors", 
			 "type": "Liability", "is_group": False, "parent_code": "211603", "level": 5},
			
			{"code": "2116032", "name_ar": "مقاولو إنتاج برامج", "name_en": "Program Production Contractors", 
			 "type": "Liability", "is_group": False, "parent_code": "211603", "level": 5},
			
			{"code": "2116033", "name_ar": "مقاولو كتابة محتوى", "name_en": "Content Writing Contractors", 
			 "type": "Liability", "is_group": False, "parent_code": "211603", "level": 5},
			
			{"code": "22604", "name_ar": "موردو حقوق واستخدامات", "name_en": "Rights & Usage Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "2260", "level": 4},
			
			{"code": "22605", "name_ar": "موردو خدمات فنية", "name_en": "Technical Services Suppliers", 
			 "type": "Liability", "is_group": False, "parent_code": "2260", "level": 4},
			
			# ============ الإيرادات - إعلامية (تحت 4000) ============
			{"code": "5060", "name_ar": "إيرادات الإعلام والترفيه", "name_en": "Media & Entertainment Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "4000", "level": 2},
			
			{"code": "5070", "name_ar": "إيرادات الإعلانات", "name_en": "Advertising Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "5060", "level": 3},
			
			{"code": "5071", "name_ar": "إيرادات الإعلانات التلفزيونية", "name_en": "TV Advertising Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5070", "level": 4},
			
			{"code": "5072", "name_ar": "إيرادات الإعلانات الرقمية", "name_en": "Digital Advertising Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5070", "level": 4},
			
			{"code": "5073", "name_ar": "إيرادات الرعايات", "name_en": "Sponsorship Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5070", "level": 4},
			
			{"code": "5074", "name_ar": "إيرادات الإعلانات المطبوعة", "name_en": "Print Advertising Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5070", "level": 4},
			
			{"code": "5080", "name_ar": "إيرادات المحتوى والإنتاج", "name_en": "Content & Production Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "5060", "level": 3},
			
			{"code": "5081", "name_ar": "إيرادات بيع المحتوى", "name_en": "Content Sales Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5080", "level": 4},
			
			{"code": "5082", "name_ar": "إيرادات تراخيص المحتوى", "name_en": "Content Licensing Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5080", "level": 4},
			
			{"code": "5083", "name_ar": "إيرادات إنتاج الأفلام", "name_en": "Film Production Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5080", "level": 4},
			
			{"code": "5084", "name_ar": "إيرادات إنتاج البرامج", "name_en": "Program Production Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5080", "level": 4},
			
			{"code": "5090", "name_ar": "إيرادات البث والنشر", "name_en": "Broadcasting & Publishing Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "5060", "level": 3},
			
			{"code": "5091", "name_ar": "إيرادات البث التلفزيوني", "name_en": "TV Broadcasting Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5090", "level": 4},
			
			{"code": "5092", "name_ar": "إيرادات البث الإذاعي", "name_en": "Radio Broadcasting Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5090", "level": 4},
			
			{"code": "5093", "name_ar": "إيرادات النشر الرقمي", "name_en": "Digital Publishing Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5090", "level": 4},
			
			{"code": "5094", "name_ar": "إيرادات النشر المطبوع", "name_en": "Print Publishing Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5090", "level": 4},
			
			{"code": "51100", "name_ar": "إيرادات الاشتراكات والتوزيع", "name_en": "Subscriptions & Distribution Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "5060", "level": 3},
			
			{"code": "5101", "name_ar": "إيرادات اشتراكات القنوات", "name_en": "Channel Subscriptions Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "51100", "level": 4},
			
			{"code": "5102", "name_ar": "إيرادات منصات البث", "name_en": "Streaming Platforms Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "51100", "level": 4},
			
			{"code": "5103", "name_ar": "إيرادات توزيع المحتوى", "name_en": "Content Distribution Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "51100", "level": 4},
			
			{"code": "5104", "name_ar": "إيرادات بيع التذاكر", "name_en": "Ticket Sales Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "51100", "level": 4},
			
			{"code": "5110", "name_ar": "إيرادات الخدمات الإعلامية", "name_en": "Media Services Revenue", 
			 "type": "Revenue", "is_group": True, "parent_code": "5060", "level": 3},
			
			{"code": "5111", "name_ar": "إيرادات الاستشارات الإعلامية", "name_en": "Media Consulting Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5110", "level": 4},
			
			{"code": "5112", "name_ar": "إيرادات إدارة المحتوى", "name_en": "Content Management Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5110", "level": 4},
			
			{"code": "5113", "name_ar": "إيرادات التدريب الإعلامي", "name_en": "Media Training Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5110", "level": 4},
			
			{"code": "5114", "name_ar": "إيرادات إنتاج الفعاليات", "name_en": "Events Production Revenue", 
			 "type": "Revenue", "is_group": False, "parent_code": "5110", "level": 4},
			
			# ============ التكاليف - إعلامية (تحت 5000) ============
			{"code": "6020", "name_ar": "تكاليف الإعلام والترفيه", "name_en": "Media & Entertainment Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
			
			{"code": "6030", "name_ar": "تكاليف إنتاج المحتوى", "name_en": "Content Production Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "6020", "level": 3},
			
			{"code": "6031", "name_ar": "تكلفة إنتاج البرامج", "name_en": "Program Production Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "6030", "level": 4},
			
			{"code": "6032", "name_ar": "تكلفة إنتاج الأفلام", "name_en": "Film Production Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "6030", "level": 4},
			
			{"code": "6033", "name_ar": "تكلفة المواد الإنتاجية", "name_en": "Production Materials Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "6030", "level": 4},
			
			{"code": "6034", "name_ar": "تكلفة الحقوق والملكيات", "name_en": "Rights & Properties Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "6030", "level": 4},
			
			{"code": "6040", "name_ar": "تكاليف البث والنشر", "name_en": "Broadcasting & Publishing Costs", 
			 "type": "Expense", "is_group": True, "parent_code": "6020", "level": 3},
			
			{"code": "6041", "name_ar": "تكلفة خدمات البث", "name_en": "Broadcasting Services Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "6040", "level": 4},
			
			{"code": "6042", "name_ar": "تكلفة خدمات النشر", "name_en": "Publishing Services Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "6040", "level": 4},
			
			{"code": "6043", "name_ar": "تكلفة التوزيع", "name_en": "Distribution Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "6040", "level": 4},
			
			{"code": "6044", "name_ar": "تكلفة المنصات الرقمية", "name_en": "Digital Platforms Cost", 
			 "type": "Expense", "is_group": False, "parent_code": "6040", "level": 4},
			
			# ============ المصروفات - إعلامية (تحت 5000) ============
			{"code": "6050", "name_ar": "مصاريف تشغيلية - إعلامية", "name_en": "Operational Expenses - Media", 
			 "type": "Expense", "is_group": True, "parent_code": "5000", "level": 2},
			
			{"code": "6060", "name_ar": "رواتب ومكافآت العاملين", "name_en": "Employee Salaries & Bonuses", 
			 "type": "Expense", "is_group": True, "parent_code": "6050", "level": 3},
			
			{"code": "6061", "name_ar": "رواتب المذيعين والمقدمين", "name_en": "Broadcasters & Presenters Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "6060", "level": 4},
			
			{"code": "6062", "name_ar": "رواتب المنتجين والمخرجين", "name_en": "Producers & Directors Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "6060", "level": 4},
			
			{"code": "6063", "name_ar": "رواتب الصحفيين والكتاب", "name_en": "Journalists & Writers Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "6060", "level": 4},
			
			{"code": "6064", "name_ar": "رواتب الفنيين والمهندسين", "name_en": "Technicians & Engineers Salaries", 
			 "type": "Expense", "is_group": False, "parent_code": "6060", "level": 4},
			
			{"code": "6065", "name_ar": "رواتب الإداريين والمشرفين", "name_en": "Administrators & Supervisors", 
			 "type": "Expense", "is_group": False, "parent_code": "6060", "level": 4},
			
			{"code": "6070", "name_ar": "مصاريف التسويق والترويج", "name_en": "Marketing & Promotion Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "6050", "level": 3},
			
			{"code": "6071", "name_ar": "مصاريف الحملات الإعلانية", "name_en": "Advertising Campaigns Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6070", "level": 4},
			
			{"code": "6072", "name_ar": "مصاريف العلاقات العامة", "name_en": "Public Relations Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6070", "level": 4},
			
			{"code": "6073", "name_ar": "مصاريف البحوث والاستطلاعات", "name_en": "Research & Surveys Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6070", "level": 4},
			
			{"code": "6074", "name_ar": "مصاريف الفعاليات والحفلات", "name_en": "Events & Parties Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6070", "level": 4},
			
			{"code": "6080", "name_ar": "مصاريف التشغيل والصيانة", "name_en": "Operation & Maintenance Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "6050", "level": 3},
			
			{"code": "6081", "name_ar": "مصاريف صيانة المعدات", "name_en": "Equipment Maintenance Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6080", "level": 4},
			
			{"code": "6082", "name_ar": "مصاريف تراخيص البرامج", "name_en": "Software Licenses Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6080", "level": 4},
			
			{"code": "6083", "name_ar": "مصاريف استضافة وحوسبة", "name_en": "Hosting & Computing Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6080", "level": 4},
			
			{"code": "6084", "name_ar": "مصاريف المرافق والخدمات", "name_en": "Utilities & Services Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6080", "level": 4},
			
			{"code": "6090", "name_ar": "مصاريف البحث والتطوير", "name_en": "Research & Development Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "6050", "level": 3},
			
			{"code": "6091", "name_ar": "مصاريف تطوير المحتوى", "name_en": "Content Development Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6090", "level": 4},
			
			{"code": "6092", "name_ar": "مصاريف اختبار التقنيات", "name_en": "Technology Testing Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6090", "level": 4},
			
			{"code": "6093", "name_ar": "مصاريف الدراسات والأبحاث", "name_en": "Studies & Research Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6090", "level": 4},
			
			{"code": "6094", "name_ar": "مصاريف الابتكار والتجديد", "name_en": "Innovation & Renewal Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6090", "level": 4},
			
			{"code": "6100", "name_ar": "مصاريف الحقوق والملكية", "name_en": "Rights & Property Expenses", 
			 "type": "Expense", "is_group": True, "parent_code": "6050", "level": 3},
			
			{"code": "6101", "name_ar": "مصاريف حقوق النشر", "name_en": "Copyright Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6100", "level": 4},
			
			{"code": "6102", "name_ar": "مصاريف تراخيص البث", "name_en": "Broadcasting Licenses Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6100", "level": 4},
			
			{"code": "6103", "name_ar": "مصاريف ملكية فكرية", "name_en": "Intellectual Property Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6100", "level": 4},
			
			{"code": "6104", "name_ar": "مصاريف التسجيل والحماية", "name_en": "Registration & Protection Expenses", 
			 "type": "Expense", "is_group": False, "parent_code": "6100", "level": 4},
			
			{"code": "6110", "name_ar": "إهلاك الأصول الإعلامية", "name_en": "Media Assets Depreciation", 
			 "type": "Expense", "is_group": True, "parent_code": "6050", "level": 3},
			
			{"code": "6111", "name_ar": "إهلاك معدات الإنتاج", "name_en": "Production Equipment Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "6110", "level": 4},
			
			{"code": "6112", "name_ar": "إهلاك معدات البث", "name_en": "Broadcasting Equipment Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "6110", "level": 4},
			
			{"code": "6113", "name_ar": "إهلاك البرامج والتطبيقات", "name_en": "Software & Applications Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "6110", "level": 4},
			
			{"code": "6114", "name_ar": "إهلاك الاستوديوهات", "name_en": "Studios Depreciation", 
			 "type": "Expense", "is_group": False, "parent_code": "6110", "level": 4},
		]
    @classmethod
    def get_industry_extensions(cls, industry_code: str) -> List[Dict]:
        """توليد الإضافات حسب التخصص"""
        industry_groups = {
        # التكنولوجيا والبرمجيات
        'software_dev': cls.get_tech_software_extensions,
        'it_services': cls.get_tech_software_extensions,
        'cybersecurity': cls.get_tech_software_extensions,
        'data_analytics': cls.get_tech_software_extensions,
        'data_science': cls.get_tech_software_extensions,
        'cloud_services': cls.get_tech_software_extensions,
        'telecom': cls.get_tech_software_extensions,
        'saas': cls.get_tech_software_extensions,
        'paas': cls.get_tech_software_extensions,
        'iaas': cls.get_tech_software_extensions,
        'hardware': cls.get_tech_software_extensions,
        'gaming': cls.get_tech_software_extensions,
        'mobile_apps': cls.get_tech_software_extensions,
        'web_development': cls.get_tech_software_extensions,
        'ai_ml': cls.get_tech_software_extensions,
        
        # الإنشاءات والمقاولات
        'construction': cls.get_construction_extensions,
        'architecture': cls.get_construction_extensions,
        'civil_engineering': cls.get_construction_extensions,
        'interior_design': cls.get_construction_extensions,
        'building_materials': cls.get_construction_extensions,
        'mep': cls.get_construction_extensions,
        'infrastructure': cls.get_construction_extensions,
        'real_estate_dev': cls.get_construction_extensions,
        'property_management': cls.get_construction_extensions,
        'facility_management': cls.get_construction_extensions,
        'urban_planning': cls.get_construction_extensions,
        
        # التصنيع والإنتاج
        'automotive': cls.get_manufacturing_extensions,
        'textile': cls.get_manufacturing_extensions,
        'food_production': cls.get_manufacturing_extensions,
        'chemicals': cls.get_manufacturing_extensions,
        'pharmaceuticals': cls.get_manufacturing_extensions,
        'machinery': cls.get_manufacturing_extensions,
        'plastics': cls.get_manufacturing_extensions,
        'electronics_mfg': cls.get_manufacturing_extensions,
        'furniture_mfg': cls.get_manufacturing_extensions,
        'metal_fabrication': cls.get_manufacturing_extensions,
        'packaging_mfg': cls.get_manufacturing_extensions,
        'aerospace': cls.get_manufacturing_extensions,
        'shipbuilding': cls.get_manufacturing_extensions,
        
        # الصحة والعناية الشخصية
        'hospital': cls.get_healthcare_extensions,
        'pharmacy': cls.get_healthcare_extensions,
        'dental': cls.get_healthcare_extensions,
        'medical_labs': cls.get_healthcare_extensions,
        'fitness': cls.get_healthcare_extensions,
        'beauty_salon': cls.get_healthcare_extensions,
        'cosmetics': cls.get_healthcare_extensions,
        'wellness': cls.get_healthcare_extensions,
        'spa': cls.get_healthcare_extensions,
        'nutrition': cls.get_healthcare_extensions,
        'mental_health': cls.get_healthcare_extensions,
        'elderly_care': cls.get_healthcare_extensions,
        'veterinary': cls.get_healthcare_extensions,
        'medical_devices': cls.get_healthcare_extensions,
        
        # التجارة والتجزئة
        'ecommerce': cls.get_retail_ecommerce_extensions,
        'retail': cls.get_retail_ecommerce_extensions,
        'fashion_retail': cls.get_retail_ecommerce_extensions,
        'supermarket': cls.get_retail_ecommerce_extensions,
        'electronics_retail': cls.get_retail_ecommerce_extensions,
        'home_goods': cls.get_retail_ecommerce_extensions,
        'jewelry': cls.get_retail_ecommerce_extensions,
        'automotive_sales': cls.get_retail_ecommerce_extensions,
        'wholesale': cls.get_retail_ecommerce_extensions,
        'bookstore': cls.get_retail_ecommerce_extensions,
        'sports_retail': cls.get_retail_ecommerce_extensions,
        'toy_store': cls.get_retail_ecommerce_extensions,
        'pet_supplies': cls.get_retail_ecommerce_extensions,
        'luxury_retail': cls.get_retail_ecommerce_extensions,
        
        # الخدمات المالية والمصرفية
        'banking': cls.get_finance_banking_extensions,
        'investment': cls.get_finance_banking_extensions,
        'insurance': cls.get_finance_banking_extensions,
        'accounting': cls.get_finance_banking_extensions,
        'fintech': cls.get_finance_banking_extensions,
        'legal': cls.get_finance_banking_extensions,
        'consulting': cls.get_finance_banking_extensions,
        'auditing': cls.get_finance_banking_extensions,
        'venture_capital': cls.get_finance_banking_extensions,
        'private_equity': cls.get_finance_banking_extensions,
        'stock_brokerage': cls.get_finance_banking_extensions,
        'microfinance': cls.get_finance_banking_extensions,
        'crowdfunding': cls.get_finance_banking_extensions,
        
        # التعليم والتدريب
        'education': cls.get_education_extensions,
        'training': cls.get_education_extensions,
        'e_learning': cls.get_education_extensions,
        'language_school': cls.get_education_extensions,
        'technical_training': cls.get_education_extensions,
        'university': cls.get_education_extensions,
        'research_institute': cls.get_education_extensions,
        
        # النقل والخدمات اللوجستية
        'logistics': cls.get_logistics_extensions,
        'transportation': cls.get_logistics_extensions,
        'shipping': cls.get_logistics_extensions,
        'freight': cls.get_logistics_extensions,
        'warehousing': cls.get_logistics_extensions,
        'courier': cls.get_logistics_extensions,
        'aviation': cls.get_logistics_extensions,
        
        # الضيافة والسياحة
        'hospitality': cls.get_hospitality_extensions,
        'tourism': cls.get_hospitality_extensions,
        'hotel': cls.get_hospitality_extensions,
        'restaurant': cls.get_hospitality_extensions,
        'catering': cls.get_hospitality_extensions,
        'event_planning': cls.get_hospitality_extensions,
        'travel_agency': cls.get_hospitality_extensions,
        
        # الطاقة والبيئة
        'energy': cls.get_energy_extensions,
        'renewable_energy': cls.get_energy_extensions,
        'oil_gas': cls.get_energy_extensions,
        'environmental': cls.get_energy_extensions,
        'waste_management': cls.get_energy_extensions,
        'water_treatment': cls.get_energy_extensions,
        
        # وسائل الإعلام والترفيه
        'media': cls.get_media_extensions,
        'entertainment': cls.get_media_extensions,
        'publishing': cls.get_media_extensions,
        'broadcasting': cls.get_media_extensions,
        'film_production': cls.get_media_extensions,
        'music': cls.get_media_extensions,
        'gaming_entertainment': cls.get_media_extensions,
        }
    
        extension_func = industry_groups.get(industry_code)
        if extension_func:
            try:
                return extension_func()
            except Exception as e:
                # تسجيل الخطأ وإرجاع قائمة فارغة في حالة وجود مشكلة
                print(f"Error loading extensions for industry {industry_code}: {e}")
                return []
        else:
            # إرجاع قائمة فارغة إذا لم يتم العثور على التخصص
            return []
    # ==================== دالة الإنشاء الرئيسية ====================
    
    @classmethod
    def seed_chart_of_accounts(cls, project_id: int, industry: Optional[str] = None, 
                           currency_id: int = 1, company_size: str = "medium") -> Dict[str, int]:
        """
    إنشاء شجرة حسابات متكاملة ومتخصصة
        """
    
    # التحقق من صحة الإدخال
        if not project_id or project_id <= 0:
            raise ValueError("معرف المشروع غير صالح")
    
    # التحقق من العملة بأمان
        try:
            currency = Currency.query.get(currency_id)
            if not currency:
                print(f"⚠️ العملة ID {currency_id} غير موجودة، استخدام العملة الافتراضية (ID: 1)")
                currency_id = 1
        except Exception as e:
            print(f"⚠️ خطأ في الاستعلام عن العملة: {e}، استخدام العملة الافتراضية")
            currency_id = 1
    
    # 1. تجميع القائمة الكاملة
        all_accounts = cls.STANDARD_FRAMEWORK.copy()
    
    # 2. إضافة حسابات التخصص
        if industry and industry != '1':  # تأكد أن industry ليس '1' فقط
            extensions = cls.get_industry_extensions(industry)
            if extensions:
                print(f"🔧 إضافة {len(extensions)} حساب متخصص لـ '{industry}'")
                all_accounts.extend(extensions)
            else:
                print(f"ℹ️ لا توجد حسابات متخصصة لـ '{industry}'، استخدام الشجرة الأساسية")
        else:
            print(f"ℹ️ التخصص غير محدد ({industry})، استخدام الشجرة الأساسية")
    
    # 3. التحقق من عدم تكرار الأكواد
        code_set = set()
        for account in all_accounts:
            code = account.get('code')
            if not code:
                raise ValueError(f"حساب بدون كود: {account.get('name_ar')}")
            if code in code_set:
                raise ValueError(f"تكرر كود الحساب: {code}")
            code_set.add(code)
    
    # 4. إنشاء الخرائط المساعدة
        code_to_id = {}
        code_to_fullcode = {}
        default_accounts = {}
    
    # 5. إنشاء الحسابات في قاعدة البيانات
        try:
        # ترتيب الحسابات حسب المستوى (من المستوى 1 إلى الأعلى)
            all_accounts.sort(key=lambda x: x.get('level', 1))
        
            for account_data in all_accounts:
                parent_id = None
                parent_full_code = None
            
                parent_code = account_data.get('parent_code')
                if parent_code:
                    parent_id = code_to_id.get(parent_code)
                    parent_full_code = code_to_fullcode.get(parent_code)
                
                    if not parent_id:
                        print(f"⚠️ الحساب الأب {parent_code} غير موجود للحساب {account_data['code']}")
                    # حاول العثور على الحساب الأب في قاعدة البيانات
                        parent_acc = ChartOfAccounts.query.filter_by(
                            project_id=project_id, 
                            code=parent_code
                        ).first()
                        if parent_acc:
                            parent_id = parent_acc.id
                            parent_full_code = parent_acc.full_code
                            code_to_id[parent_code] = parent_id
                            code_to_fullcode[parent_code] = parent_full_code
                        else:
                        # إذا لم يوجد الحساب الأب، تخطى هذا الحساب
                            print(f"⏭️ تخطي {account_data['code']} لأن الأب غير موجود")
                            continue
            
            # بناء full_code
                if parent_full_code:
                    full_code = f"{parent_full_code}.{account_data['code']}"
                else:
                    full_code = account_data['code']
            
            # التحقق من أن الحساب غير موجود مسبقاً
                existing = ChartOfAccounts.query.filter_by(
                    project_id=project_id,
                    full_code=full_code
                ).first()
            
                if existing:
                    print(f"⏭️ الحساب {full_code} موجود مسبقاً، تخطي")
                    code_to_id[account_data['code']] = existing.id
                    code_to_fullcode[account_data['code']] = full_code
                    continue
            
            # إنشاء كائن الحساب
                account = ChartOfAccounts(
                    project_id=project_id,
                    name=account_data['name_ar'],
                    name_ar=account_data['name_ar'],
                    name_en=account_data['name_en'],
                    type=account_data['type'],
                    code=account_data['code'],
                    full_code=full_code,
                    level=account_data.get('level', 1),
                    parent_account_id=parent_id,
                    is_group=account_data['is_group'],
                    currency_id=currency_id,
                    is_active=True,
                    normal_balance=None,
                    created_by=None
                )
            
                db.session.add(account)
                db.session.flush()  # للحصول على ID فوراً
            
            # تحديث الخرائط
                code_to_id[account_data['code']] = account.id
                code_to_fullcode[account_data['code']] = full_code
            
            # التقاط الحسابات الافتراضية المهمة
                tag = account_data.get('tag')
                if tag:
                    default_accounts[tag] = account.id
        
            db.session.commit()
        
            print(f"✅ تم إنشاء {len(code_set)} حساب بنجاح")
            print(f"📊 الحسابات الافتراضية: {default_accounts}")
        
            return default_accounts
        
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في إنشاء شجرة الحسابات: {str(e)}")
            import traceback
            traceback.print_exc()  # طباعة تفاصيل الخطأ
            raise
# ==================== دالة مساعدة للاستخدام ====================

def create_custom_coa(project_id: int, industry: str = None, 
                     currency_id: int = 1, company_size: str = "medium") -> Dict[str, int]:
    """
    واجهة مبسطة لإنشاء شجرة حسابات
    
    Args:
        project_id: معرف المشروع
        industry: مجال العمل
        currency_id: العملة
        company_size: حجم الشركة
        
    Returns:
        Dict[str, int]: الحسابات الافتراضية
    """
    try:
        defaults = SmartCOAEngine.seed_chart_of_accounts(
            project_id=project_id,
            industry=industry,
            currency_id=currency_id,
            company_size=company_size
        )
        
        # هنا يمكنك تحديث المشروع بالحسابات الافتراضية
        # update_project_with_defaults(project_id, defaults)
        
        return {
            'success': True,
            'message': 'تم إنشاء شجرة الحسابات بنجاح',
            'defaults': defaults,
            'total_accounts_created': len(SmartCOAEngine.STANDARD_FRAMEWORK) + 
                                     len(SmartCOAEngine.get_industry_extensions(industry or ''))
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'خطأ في إنشاء شجرة الحسابات: {str(e)}'
        }
