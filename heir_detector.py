# ============================================
# heir_detector.py
# Module de détection des héritiers
# ============================================

"""
Module spécialisé pour la détection et l'extraction des héritiers
à partir d'un texte en arabe.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from fractions import Fraction
from enum import Enum


# ============================================
# MODÈLE DE DONNÉES
# ============================================

class RelationType(Enum):
    """Types de relations familiales"""
    SPOUSE_WIFE = "الزوجة"
    SPOUSE_HUSBAND = "الزوج"
    SON = "الابن"
    DAUGHTER = "البنت"
    FATHER = "الأب"
    MOTHER = "الأم"
    GRANDFATHER = "الجد"
    GRANDMOTHER = "الجدة"
    GRANDSON = "ابن_الابن"
    GRANDDAUGHTER = "بنت_الابن"
    GRANDDAUGHTER_DAUGHTER = "بنت_البنت"
    BROTHER_FULL = "الأخ_الشقيق"
    SISTER_FULL = "الأخت_الشقيقة"
    BROTHER_PATERNAL = "الأخ_لأب"
    SISTER_PATERNAL = "الأخت_لأب"
    BROTHER_MATERNAL = "الأخ_لأم"
    SISTER_MATERNAL = "الأخت_لأم"
    NEPHEW = "ابن_الأخ"
    UNCLE_PATERNAL = "العم"
    NEPHEW_OF_UNCLE = "ابن_العم"


@dataclass
class Heir:
    """Représentation d'un héritier"""
    name: str
    relation: str
    gender: str
    count: int = 1
    is_blocked: bool = False
    share: Fraction = field(default_factory=lambda: Fraction(0, 1))
    
    def __str__(self):
        if self.count > 1:
            return f"{self.name} (×{self.count})"
        return self.name
    
    def to_dict(self) -> Dict:
        """Convertir en dictionnaire"""
        return {
            "name": self.name,
            "relation": self.relation,
            "gender": self.gender,
            "count": self.count,
            "is_blocked": self.is_blocked,
            "share": str(self.share)
        }


# ============================================
# DÉTECTEUR D'HÉRITIERS
# ============================================

class HeirDetector:
    """
    Classe modulaire pour la détection des héritiers
    Séparée de la logique de calcul
    """
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.detected_heirs: List[Heir] = []
        self.deceased_gender: Optional[str] = None
        
    def _initialize_patterns(self) -> Dict:
        """Initialiser les patterns de détection avec nombres"""
        return {
            # Patterns pour les nombres
            'numbers': {
                'واحد': 1, 'واحدة': 1,
                'اثنان': 2, 'اثنين': 2, 'اثنتان': 2, 'اثنتين': 2,
                'ثلاثة': 3, 'ثلاث': 3,
                'أربعة': 4, 'أربع': 4,
                'خمسة': 5, 'خمس': 5,
                'ستة': 6, 'ست': 6,
                'سبعة': 7, 'سبع': 7,
                'ثمانية': 8, 'ثماني': 8,
                'تسعة': 9, 'تسع': 9,
                'عشرة': 10, 'عشر': 10
            },
            
            # Patterns spécifiques pour fils et filles
            'son': [
                r'(\d+)\s*أبناء',  # X أبناء
                r'(\d+)\s*ابن',    # X ابن
                r'(ثلاثة|أربعة|خمسة|ستة|سبعة|ثمانية|تسعة|عشرة)\s*أبناء',
                r'(اثنان|اثنين)\s*من\s*الأبناء',
                r'ولدان',  # 2 fils
                r'ولدين',  # 2 fils
                r'\bوابنا\b',  # وابنا
                r'\bوابن\b(?!ة)(?!\sعم)(?!\sأخ)(?!\sالابن)',  # وابن
                r'و\s+ابنا\b',  # و ابنا (avec espace)
                r'و\s+ابن\b(?!ة)(?!\sعم)(?!\sأخ)',  # و ابن (avec espace)
                r'(?<!بنت\s)(?<!ابن\s)(?<!\s)\bابن\b(?!ة)(?!\sعم)(?!\sأخ)(?!\sالابن)',  # fils unique
                r'ولد(?!\sابن)',  # fils
                r'\bولدا\b',  # ولدا
            ],
            
            'daughter': [
                r'(\d+)\s*بنات',   # X بنات
                r'(\d+)\s*بنت',    # X بنت
                r'(ثلاث|أربع|خمس|ست|سبع|ثماني|تسع|عشر)\s*بنات',
                r'(اثنتان|اثنتين)\s*من\s*البنات',
                r'بنتان',  # 2 filles
                r'بنتين',  # 2 filles
                r'\bوبنتا\b(?!\s+ابن)(?!\s+بنت)',  # وبنتا
                r'\bوبنت\b(?!\s+ابن)(?!\s+بنت)',   # وبنت
                r'و\s+بنتا\b(?!\s+ابن)(?!\s+بنت)',  # و بنتا (avec espace)
                r'و\s+بنت\b(?!\s+ابن)(?!\s+بنت)',   # و بنت (avec espace)
                r'\bبنتا\b(?!\s+ابن)(?!\s+بنت)',  # fille (accusatif)
                r'(?<!بنت\s)\bبنت\b(?!\s+ابن)(?!\s+بنت)(?!\s+الابن)',  # fille unique
            ],
            
            # Patterns pour les frères
            'brother_full': [
                r'(\d+)\s*إخوة\s*أشقاء',
                r'(ثلاثة|أربعة)\s*إخوة\s*أشقاء',
                r'(أخوين|أخوان)\s*شقيقين',
                r'أخ\s*شقيق',
                r'\bوأخا\b(?!\sلأب)(?!\sلأم)',  # وأخا
                r'\bوأخ\b(?!\sلأب)(?!\sلأم)',  # وأخ
                r'و\s+أخا\b(?!\sلأب)(?!\sلأم)',  # و أخا (avec espace)
                r'و\s+أخ\b(?!\sلأب)(?!\sلأم)',  # و أخ (avec espace)
                r'\bأخا\b(?!\sلأب)(?!\sلأم)',  # frère (accusatif)
                r'(?<!ابن\s)\bأخ\b(?!\sلأب)(?!\sلأم)',  # frère sans qualification = frère germain
            ],
            
            'sister_full': [
                r'(\d+)\s*أخوات\s*شقيقات',
                r'(أختين|أختان)\s*شقيقتين',
                r'أخت\s*شقيقة',
                r'\bأختا\b(?!\sلأب)(?!\sلأم)',  # أختا
                r'\bوأختا\b(?!\sلأب)(?!\sلأم)',  # وأختا
                r'\bوأخت\b(?!\sلأب)(?!\sلأم)',  # وأخت
                r'و\s+أختا\b(?!\sلأب)(?!\sلأم)',  # و أختا (avec espace)
                r'و\s+أخت\b(?!\sلأب)(?!\sلأم)',  # و أخت (avec espace)
                r'(?<!ابن\s)\bأخت\b(?!\sلأب)(?!\sلأم)',  # sœur sans qualification = sœur germaine
            ],
            
            'brother_paternal': [
                r'(\d+)\s*إخوة\s*لأب',
                r'أخ\s*لأب',
                r'أخا\s*لأب',
                r'وأخ\s*لأب',
                r'وأخا\s*لأب',
            ],
            
            'sister_paternal': [
                r'(\d+)\s*أخوات\s*لأب',
                r'أخت\s*لأب',
                r'أختا\s*لأب',
                r'وأخت\s*لأب',
                r'وأختا\s*لأب',
            ],
        }
    
    def detect_deceased_gender(self, text: str) -> str:
        """Détecter le genre du défunt"""
        text_lower = text.lower()
        
        male_indicators = ['توفي', 'مات', 'توفى', 'تاركا', 'وترك', 'رجل', 'عن']
        female_indicators = ['توفيت', 'ماتت', 'توفت', 'تاركة', 'امرأة']
        
        for indicator in female_indicators:
            if indicator in text_lower:
                return 'أنثى'
        
        for indicator in male_indicators:
            if indicator in text_lower:
                return 'ذكر'
        
        # Par défaut, si on trouve "زوجة" c'est un homme qui est mort
        if 'زوجة' in text_lower:
            return 'ذكر'
        elif 'زوج' in text_lower and 'زوجة' not in text_lower:
            return 'أنثى'
        
        return 'ذكر'  # Par défaut
    
    def extract_number_from_text(self, text: str, pattern_match: str) -> int:
        """Extraire le nombre d'un texte"""
        # Chercher un chiffre
        digit_match = re.search(r'\d+', pattern_match)
        if digit_match:
            return int(digit_match.group())
        
        # Chercher un nombre en lettres
        for word, num in self.patterns['numbers'].items():
            if word in pattern_match:
                return num
        
        # Cas spéciaux
        if any(x in pattern_match for x in ['ولدان', 'ولدين', 'بنتان', 'بنتين', 'اثنان', 'اثنين', 'اثنتان', 'اثنتين']):
            return 2
        
        return 1
    
    def detect_sons(self, text: str) -> int:
        """Détecter le nombre de fils"""
        text_lower = text.lower()
        max_count = 0
        
        for pattern in self.patterns['son']:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                full_match = match.group(0)
                count = self.extract_number_from_text(text_lower, full_match)
                max_count = max(max_count, count)
        
        return max_count
    
    def detect_daughters(self, text: str) -> int:
        """Détecter le nombre de filles"""
        text_lower = text.lower()
        max_count = 0
        
        for pattern in self.patterns['daughter']:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                full_match = match.group(0)
                count = self.extract_number_from_text(text_lower, full_match)
                max_count = max(max_count, count)
        
        return max_count
    
    def detect_brothers(self, text: str, brother_type: str = 'full') -> int:
        """Détecter le nombre de frères"""
        text_lower = text.lower()
        max_count = 0
        
        patterns = self.patterns.get(f'brother_{brother_type}', [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                full_match = match.group(0)
                count = self.extract_number_from_text(text_lower, full_match)
                max_count = max(max_count, count)
        
        return max_count
    
    def detect_sisters(self, text: str, sister_type: str = 'full') -> int:
        """Détecter le nombre de sœurs"""
        text_lower = text.lower()
        max_count = 0
        
        patterns = self.patterns.get(f'sister_{sister_type}', [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                full_match = match.group(0)
                count = self.extract_number_from_text(text_lower, full_match)
                max_count = max(max_count, count)
        
        return max_count
    
    def detect_heirs(self, text: str) -> List[Heir]:
        """
        Fonction principale de détection des héritiers
        Retourne une liste d'objets Heir
        """
        self.detected_heirs = []
        text_lower = text.lower()
        
        # Détecter le genre du défunt
        self.deceased_gender = self.detect_deceased_gender(text)
        
        # 1. Conjoint(e)
        if self.deceased_gender == 'ذكر':
            wife_patterns = ['زوجة', 'زوجته', 'وزوجة', 'وزوجته']
            if any(pattern in text_lower for pattern in wife_patterns):
                self.detected_heirs.append(
                    Heir(name="الزوجة", relation="الزوجة", gender="أنثى", count=1)
                )
        else:  # أنثى
            if 'زوج' in text_lower and 'زوجة' not in text_lower:
                self.detected_heirs.append(
                    Heir(name="الزوج", relation="الزوج", gender="ذكر", count=1)
                )
        
        # 2. Fils
        sons_count = self.detect_sons(text)
        if sons_count > 0:
            if sons_count == 1:
                self.detected_heirs.append(
                    Heir(name="الابن", relation="الابن", gender="ذكر", count=1)
                )
            else:
                for i in range(sons_count):
                    self.detected_heirs.append(
                        Heir(name=f"الابن {i+1}", relation="الابن", gender="ذكر", count=1)
                    )
        
        # 3. Filles
        daughters_count = self.detect_daughters(text)
        if daughters_count > 0:
            if daughters_count == 1:
                self.detected_heirs.append(
                    Heir(name="البنت", relation="البنت", gender="أنثى", count=1)
                )
            else:
                for i in range(daughters_count):
                    self.detected_heirs.append(
                        Heir(name=f"البنت {i+1}", relation="البنت", gender="أنثى", count=1)
                    )
        
        # 4. Petite-fille (بنت ابن) et bint bint (بنت بنت)
        if re.search(r'بنت\s+ابن', text_lower):
            self.detected_heirs.append(
                Heir(name="بنت الابن", relation="بنت_الابن", gender="أنثى", count=1)
            )
        
        # 5. Bint bint (بنت بنت) - petite-fille par la fille
        if re.search(r'بنت\s+بنت', text_lower):
            self.detected_heirs.append(
                Heir(name="بنت البنت", relation="بنت_البنت", gender="أنثى", count=1)
            )
        
        # 6. Grand-père (الجد)
        grandfather_patterns = [
            r'\bجد\b',      # جد
            r'\bجدا\b',     # جدا
            r'\bوجد\b',     # وجد
            r'\bوجدا\b',    # وجدا
            r'و\s+جد\b',    # و جد (avec espace)
            r'و\s+جدا\b',   # و جدا (avec espace)
        ]
        has_grandfather = any(re.search(pattern, text_lower) for pattern in grandfather_patterns)
        
        if has_grandfather and 'جدة' not in text_lower:
            self.detected_heirs.append(
                Heir(name="الجد", relation="الجد", gender="ذكر", count=1)
            )
        
        # 7. Père
        father_patterns = [
            r'\bأب\b',      # أب
            r'\bأبا\b',     # أبا
            r'\bوأب\b',     # وأب
            r'\bوأبا\b',    # وأبا
            r'و\s+أب\b',    # و أب (avec espace)
            r'و\s+أبا\b',   # و أبا (avec espace)
        ]
        has_father = any(re.search(pattern, text_lower) for pattern in father_patterns)
        
        if has_father and 'أبناء' not in text_lower and 'لأب' not in text_lower:
            if not re.search(r'أخ\s*لأب', text_lower):
                self.detected_heirs.append(
                    Heir(name="الأب", relation="الأب", gender="ذكر", count=1)
                )
        
        # 8. Mère
        mother_patterns = [
            r'\bأم\b',      # أم
            r'\bأما\b',     # أما
            r'\bوأم\b',     # وأم
            r'\bوأما\b',    # وأما
            r'و\s+أم\b',    # و أم (avec espace)
            r'و\s+أما\b',   # و أما (avec espace)
        ]
        has_mother = any(re.search(pattern, text_lower) for pattern in mother_patterns)
        
        if has_mother and 'لأم' not in text_lower:
            self.detected_heirs.append(
                Heir(name="الأم", relation="الأم", gender="أنثى", count=1)
            )
        
        # 9. Frères germains
        brothers_full_count = self.detect_brothers(text, 'full')
        if brothers_full_count > 0:
            if brothers_full_count == 1:
                self.detected_heirs.append(
                    Heir(name="الأخ الشقيق", relation="الأخ_الشقيق", gender="ذكر", count=1)
                )
            else:
                for i in range(brothers_full_count):
                    self.detected_heirs.append(
                        Heir(name=f"الأخ الشقيق {i+1}", relation="الأخ_الشقيق", gender="ذكر", count=1)
                    )
        
        # 10. Sœurs germaines
        sisters_full_count = self.detect_sisters(text, 'full')
        if sisters_full_count > 0:
            if sisters_full_count == 1:
                self.detected_heirs.append(
                    Heir(name="الأخت الشقيقة", relation="الأخت_الشقيقة", gender="أنثى", count=1)
                )
            else:
                for i in range(sisters_full_count):
                    self.detected_heirs.append(
                        Heir(name=f"الأخت الشقيقة {i+1}", relation="الأخت_الشقيقة", gender="أنثى", count=1)
                    )
        
        # 11. Frères/sœurs pour père
        if re.search(r'أخ\s+لأب', text_lower):
            brothers_paternal_count = self.extract_number_from_text(text_lower, 'أخ لأب')
            if brothers_paternal_count >= 1:
                for i in range(brothers_paternal_count):
                    self.detected_heirs.append(
                        Heir(name=f"الأخ لأب {i+1}" if brothers_paternal_count > 1 else "الأخ لأب",
                             relation="الأخ_لأب", gender="ذكر", count=1)
                    )
        
        if re.search(r'أخت\s+لأب', text_lower):
            sisters_paternal_count = self.extract_number_from_text(text_lower, 'أخت لأب')
            if sisters_paternal_count >= 1:
                for i in range(sisters_paternal_count):
                    self.detected_heirs.append(
                        Heir(name=f"الأخت لأب {i+1}" if sisters_paternal_count > 1 else "الأخت لأب",
                             relation="الأخت_لأب", gender="أنثى", count=1)
                    )
        
        return self.detected_heirs
    
    def get_detection_summary(self) -> str:
        """Obtenir un résumé de la détection"""
        summary = f"🔍 **نتائج الكشف عن الورثة:**\n"
        summary += f"  • جنس المتوفى: {self.deceased_gender}\n"
        summary += f"  • عدد الورثة المكتشفين: {len(self.detected_heirs)}\n\n"
        
        if self.detected_heirs:
            summary += "**قائمة الورثة:**\n"
            for heir in self.detected_heirs:
                summary += f"  • {heir.name} ({heir.relation})\n"
        else:
            summary += "⚠️ لم يتم اكتشاف أي ورثة\n"
        
        return summary
    
    def get_heirs_list(self) -> List[Heir]:
        """Retourner la liste des héritiers détectés"""
        return self.detected_heirs
    
    def get_deceased_gender(self) -> Optional[str]:
        """Retourner le genre du défunt"""
        return self.deceased_gender


# ============================================
# TESTS
# ============================================

if __name__ == "__main__":
    print("🧪 TEST DU MODULE heir_detector.py\n")
    print("="*70)
    
    detector = HeirDetector()
    
    test_cases = [
        "ترك زوجة وولدان وبنتان",
        "توفي عن زوجة وأب وأم",
        "ماتت عن زوج وأب وأم",
        "ترك زوجة وثلاثة إخوة أشقاء",
        "توفي عن بنت ابن",
        "ترك بنت بنت",
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔎 TEST {i}: {test}")
        print("-"*70)
        
        heirs = detector.detect_heirs(test)
        print(detector.get_detection_summary())
        
        print("\n📊 Détails des héritiers:")
        for heir in heirs:
            print(f"  • {heir.name} - {heir.relation} - {heir.gender}")
