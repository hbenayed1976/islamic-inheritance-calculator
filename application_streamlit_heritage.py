"""
Application Streamlit pour le système de calcul d'héritage islamique
"""

import streamlit as st
from fractions import Fraction
import sys
from pathlib import Path

# Ajouter le chemin des modules
sys.path.insert(0, str(Path(__file__).parent))

from heir_detector import HeirDetector, Heir
from heritage_calculator import HeritageCalculator

# ============================================
# CONFIGURATION DE LA PAGE
# ============================================

st.set_page_config(
    page_title="نظام حساب المواريث",
    page_icon="📿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# STYLE CSS PERSONNALISÉ
# ============================================

st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1e7e34;
        padding: 1rem 0;
        border-bottom: 3px solid #1e7e34;
        margin-bottom: 2rem;
    }
    
    .result-card {
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .blocked-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #0066cc;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .rtl-text {
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def fraction_to_arabic(frac: Fraction) -> str:
    """Convertir une fraction en texte arabe"""
    if frac.denominator == 1:
        return f"{frac.numerator}/1"
    return f"{frac.numerator}/{frac.denominator}"

def display_heir_card(name: str, share_info, is_blocked: bool = False):
    """Afficher une carte pour un héritier"""
    if is_blocked:
        st.markdown(f"""
        <div class="blocked-card rtl-text">
            <h4>❌ {name}</h4>
            <p><strong>محجوب</strong> - لا يرث</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        frac = share_info['الكسر']
        percent = share_info['النسبة_المئوية']
        relation = share_info['الصلة']
        
        st.markdown(f"""
        <div class="result-card rtl-text">
            <h4>✅ {name}</h4>
            <p><strong>الصلة:</strong> {relation}</p>
            <p><strong>الكسر:</strong> {frac}</p>
            <p><strong>النسبة:</strong> {percent}%</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# INITIALISATION DE LA SESSION
# ============================================

if 'history' not in st.session_state:
    st.session_state.history = []

if 'detector' not in st.session_state:
    st.session_state.detector = HeirDetector()

# ============================================
# EN-TÊTE
# ============================================

st.markdown("""
<div class="main-header">
    <h1>📿 نظام حساب المواريث الإسلامية</h1>
    <p>Islamic Inheritance Calculator System</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR - INFORMATIONS ET EXEMPLES
# ============================================

with st.sidebar:
    st.header("ℹ️ معلومات")
    
    st.info("""
    **كيفية الاستخدام:**
    
    1. أدخل حالة الوراثة بالعربية
    2. اضغط على "حساب"
    3. شاهد النتائج والتفاصيل
    """)
    
    st.header("📝 أمثلة")
    
    examples = [
        "ترك زوجة وولدان وبنتان",
        "توفي عن زوجة وأب وأم",
        "ماتت عن زوج وأب وأم",
        "ترك زوجة وثلاثة إخوة أشقاء",
        "توفي وترك زوجة وأخا وبنتا",
        "ماتت عن زوج وأم وبنت"
    ]
    
    for i, example in enumerate(examples, 1):
        if st.button(f"مثال {i}", key=f"example_{i}", use_container_width=True):
            st.session_state.query_input = example
    
    st.divider()
    
    st.header("📊 الإحصائيات")
    st.metric("عدد الحسابات", len(st.session_state.history))
    
    if st.button("🗑️ مسح السجل", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# ============================================
# ZONE PRINCIPALE
# ============================================

# Créer deux colonnes pour la mise en page
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 إدخال الحالة")
    
    # Zone de texte pour la requête
    query = st.text_area(
        "أدخل حالة الوراثة:",
        value=st.session_state.get('query_input', ''),
        height=100,
        placeholder="مثال: ترك زوجة وولدان وبنتان",
        key="query_area"
    )
    
    # Boutons d'action
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        calculate_btn = st.button("🔢 حساب", type="primary", use_container_width=True)
    
    with col_btn2:
        clear_btn = st.button("🔄 مسح", use_container_width=True)
    
    if clear_btn:
        st.session_state.query_input = ""
        st.rerun()

with col2:
    st.header("🔍 معلومات سريعة")
    st.markdown("""
    <div class="info-box rtl-text">
        <h4>الفروض المقدرة:</h4>
        <ul>
            <li>النصف (1/2)</li>
            <li>الربع (1/4)</li>
            <li>الثمن (1/8)</li>
            <li>الثلثان (2/3)</li>
            <li>الثلث (1/3)</li>
            <li>السدس (1/6)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# TRAITEMENT ET AFFICHAGE DES RÉSULTATS
# ============================================

if calculate_btn and query.strip():
    
    with st.spinner("جاري الحساب..."):
        
        # Étape 1: Détection des héritiers
        st.header("🔍 مرحلة الكشف عن الورثة")
        
        detector = HeirDetector()
        heirs = detector.detect_heirs(query)
        
        if not heirs:
            st.error("❌ لم يتم اكتشاف أي ورثة في النص المدخل")
            st.stop()
        
        # Afficher le résumé de détection
        col_detect1, col_detect2 = st.columns(2)
        
        with col_detect1:
            st.metric("جنس المتوفى", detector.deceased_gender)
        
        with col_detect2:
            st.metric("عدد الورثة المكتشفين", len(heirs))
        
        # Liste des héritiers détectés
        st.subheader("قائمة الورثة المكتشفين:")
        
        heir_cols = st.columns(3)
        for idx, heir in enumerate(heirs):
            with heir_cols[idx % 3]:
                st.success(f"✓ {heir.name} ({heir.relation})")
        
        st.divider()
        
        # Étape 2: Calcul des parts
        st.header("🔢 مرحلة حساب الأنصبة")
        
        calculator = HeritageCalculator(heirs)
        result = calculator.calculate()
        
        # Afficher le raisonnement
        with st.expander("📖 عرض التفاصيل والاستدلالات", expanded=True):
            for step in result['الاستدلالات']:
                st.markdown(f"<div class='rtl-text'>{step}</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # Étape 3: Résultats finaux
        st.header("📊 النتائج النهائية")
        
        # Séparer les héritiers bloqués et non bloqués
        active_heirs = {}
        blocked_heirs = {}
        
        for heir_name, share_info in result['النتائج'].items():
            if share_info == "محجوب":
                blocked_heirs[heir_name] = share_info
            else:
                active_heirs[heir_name] = share_info
        
        # Afficher les héritiers actifs
        if active_heirs:
            st.subheader("✅ الورثة الذين يرثون:")
            
            for heir_name, share_info in active_heirs.items():
                display_heir_card(heir_name, share_info, False)
        
        # Afficher les héritiers bloqués
        if blocked_heirs:
            st.subheader("❌ الورثة المحجوبون:")
            
            for heir_name in blocked_heirs.keys():
                st.markdown(f"""
                <div class="blocked-card rtl-text">
                    <h4>❌ {heir_name}</h4>
                    <p><strong>محجوب</strong> - لا يرث</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Validation
        total = calculator.get_total_distributed()
        is_valid = calculator.validate_distribution()
        
        st.divider()
        
        col_valid1, col_valid2 = st.columns(2)
        
        with col_valid1:
            if is_valid:
                st.success(f"✅ التوزيع صحيح - المجموع = {total}")
            else:
                st.warning(f"⚠️ المجموع = {total}")
        
        with col_valid2:
            st.info(f"📊 عدد الورثة الفعليين: {len(active_heirs)}")
        
        # Ajouter à l'historique
        st.session_state.history.append({
            'query': query,
            'num_heirs': len(active_heirs),
            'deceased_gender': detector.deceased_gender
        })

elif calculate_btn:
    st.warning("⚠️ الرجاء إدخال حالة الوراثة")

# ============================================
# SECTION HISTORIQUE
# ============================================

if st.session_state.history:
    st.divider()
    st.header("📜 السجل")
    
    with st.expander("عرض السجل", expanded=False):
        for idx, record in enumerate(reversed(st.session_state.history), 1):
            st.markdown(f"""
            **{idx}.** {record['query']}  
            - جنس المتوفى: {record['deceased_gender']}  
            - عدد الورثة: {record['num_heirs']}
            """)

# ============================================
# FOOTER
# ============================================

st.divider()

st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p>📿 نظام حساب المواريث الإسلامية</p>
    <p style='font-size: 0.8rem;'>هذا النظام للإرشاد فقط - يُنصح بمراجعة عالم متخصص</p>
</div>
""", unsafe_allow_html=True)
