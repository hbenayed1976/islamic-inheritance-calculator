# ============================================
# heritage_calculator.py
# Module de calcul d'héritage islamique
# ============================================

"""
Module spécialisé pour le calcul des parts d'héritage
selon les règles du Fiqh islamique.
"""

from typing import List, Dict
from fractions import Fraction
from heir_detector import Heir


# ============================================
# MOTEUR DE CALCUL D'HÉRITAGE
# ============================================

class HeritageCalculator:
    """
    Moteur de calcul des parts d'héritage
    Séparé de la détection des héritiers
    """
    
    def __init__(self, heirs: List[Heir]):
        self.heirs = heirs
        self.steps = []
        self.reasoning = []
        
    def apply_hijab_rules(self):
        """Appliquer les règles de voile (حجب)"""
        self.reasoning.append("🔒 **فحص حالات الحجب:**")
        
        relations = [h.relation for h in self.heirs if not h.is_blocked]
        
        # Règle 1: Grand-père bloqué par le père
        if "الأب" in relations:
            for heir in self.heirs:
                if heir.relation == "الجد":
                    heir.is_blocked = True
                    self.reasoning.append(f"  → الجد محجوب بوجود الأب")
        
        # Règle 2: Frères bloqués par père OU fils OU grand-père (en l'absence du père)
        has_father = "الأب" in relations
        has_son = "الابن" in relations
        has_grandfather = "الجد" in relations and not has_father
        
        # Le bloqueur est soit le père, soit le fils, soit le grand-père (si pas de père)
        blocker = None
        if has_father:
            blocker = "الأب"
        elif has_son:
            blocker = "الابن"
        elif has_grandfather:
            blocker = "الجد"
        
        if blocker:
            for heir in self.heirs:
                if heir.relation in ["الأخ_الشقيق", "الأخ_لأب", "الأخت_الشقيقة", "الأخت_لأب"]:
                    heir.is_blocked = True
                    self.reasoning.append(f"  → {heir.name} محجوب بوجود {blocker}")
        
        # Règle 3: Frères consanguins bloqués par frères germains
        if "الأخ_الشقيق" in relations:
            for heir in self.heirs:
                if heir.relation in ["الأخ_لأب", "الأخت_لأب"]:
                    heir.is_blocked = True
                    self.reasoning.append(f"  → {heir.name} محجوب بوجود الأخ الشقيق")
        
        if not any(h.is_blocked for h in self.heirs):
            self.reasoning.append("  ✓ لا توجد حالات حجب")
    
    def check_umariyyatayn(self) -> bool:
        """Vérifier si c'est un cas des Umariyyatayn"""
        relations = {h.relation for h in self.heirs if not h.is_blocked}
        
        if "الأب" not in relations:
            return False
        
        case1 = relations == {"الزوجة", "الأب", "الأم"}
        case2 = relations == {"الزوج", "الأب", "الأم"}
        num_heirs = len([h for h in self.heirs if not h.is_blocked])
        
        return (case1 or case2) and num_heirs == 3
    
    def solve_umariyyatayn(self) -> Fraction:
        """Résoudre le cas des Umariyyatayn"""
        relations = {h.relation for h in self.heirs if not h.is_blocked}
        
        self.reasoning.append(f"\n⭐ **مسألة العمريتين:**")
        self.reasoning.append(f"  • هذه المسألة من المسائل الشهيرة التي قضى فيها عمر رضي الله عنه")
        
        if "الزوجة" in relations:
            spouse_share = Fraction(1, 4)
            remainder = Fraction(3, 4)
            mother_share = remainder / 3
            father_share = remainder * 2 / 3
            
            self.reasoning.append(f"  • العمرية الأولى: زوجة + أب + أم")
            self.reasoning.append(f"  • الزوجة: {spouse_share}")
            self.reasoning.append(f"  • الباقي: {remainder}")
            self.reasoning.append(f"  • الأم: {mother_share} (ثلث الباقي)")
            self.reasoning.append(f"  • الأب: {father_share} (ضعف الأم)")
            
            for heir in self.heirs:
                if heir.relation == "الزوجة":
                    heir.share = spouse_share
                elif heir.relation == "الأم":
                    heir.share = mother_share
                elif heir.relation == "الأب":
                    heir.share = father_share
        else:
            spouse_share = Fraction(1, 2)
            remainder = Fraction(1, 2)
            mother_share = remainder / 3
            father_share = remainder * 2 / 3
            
            self.reasoning.append(f"  • العمرية الثانية: زوج + أب + أم")
            self.reasoning.append(f"  • الزوج: {spouse_share}")
            self.reasoning.append(f"  • الباقي: {remainder}")
            self.reasoning.append(f"  • الأم: {mother_share} (ثلث الباقي)")
            self.reasoning.append(f"  • الأب: {father_share} (ضعف الأم)")
            
            for heir in self.heirs:
                if heir.relation == "الزوج":
                    heir.share = spouse_share
                elif heir.relation == "الأم":
                    heir.share = mother_share
                elif heir.relation == "الأب":
                    heir.share = father_share
        
        return Fraction(1, 1)
    
    def calculate_fixed_shares(self) -> Fraction:
        """Calculer les parts fixes (فروض)"""
        if self.check_umariyyatayn():
            return self.solve_umariyyatayn()
        
        total_shares = Fraction(0, 1)
        has_children = any(h.relation in ["الابن", "البنت"] 
                          for h in self.heirs if not h.is_blocked)
        
        self.reasoning.append(f"\n📊 **حساب الفروض المقدرة:**")
        self.reasoning.append(f"  • هل يوجد فرع وارث؟ {'نعم' if has_children else 'لا'}")
        
        for heir in self.heirs:
            if heir.is_blocked:
                continue
            
            relation = heir.relation
            
            # Épouse
            if relation == "الزوجة":
                share = Fraction(1, 8) if has_children else Fraction(1, 4)
                heir.share = share
                total_shares += share
                verse = "فَإِن كَانَ لَكُمْ وَلَدٌ فَلَهُنَّ الثُّمُنُ" if has_children else "وَلَهُنَّ الرُّبُعُ"
                self.reasoning.append(f"  • الزوجة: {share}")
                self.reasoning.append(f"    الدليل: {verse} (النساء: 12)")
            
            # Époux
            elif relation == "الزوج":
                share = Fraction(1, 4) if has_children else Fraction(1, 2)
                heir.share = share
                total_shares += share
                self.reasoning.append(f"  • الزوج: {share}")
            
            # Fille(s)
            elif relation == "البنت":
                num_daughters = sum(1 for h in self.heirs 
                                   if h.relation == "البنت" and not h.is_blocked)
                num_sons = sum(1 for h in self.heirs 
                              if h.relation == "الابن" and not h.is_blocked)
                
                if num_sons == 0:  # Pas de fils
                    if num_daughters == 1:
                        share = Fraction(1, 2)
                        self.reasoning.append(f"  • البنت الواحدة: {share}")
                    else:
                        share = Fraction(2, 3) / num_daughters
                        self.reasoning.append(f"  • البنتان فأكثر: {share} لكل واحدة")
                    
                    heir.share = share
                    total_shares += share
            
            # Père
            elif relation == "الأب":
                if has_children:
                    share = Fraction(1, 6)
                    heir.share = share
                    total_shares += share
                    self.reasoning.append(f"  • الأب: {share} (السدس فرضا)")
                # Si pas d'enfants, le père n'a pas de fard fixe, il prendra par 'asaba
            
            # Grand-père (comme le père en l'absence de celui-ci)
            elif relation == "الجد":
                if has_children:
                    share = Fraction(1, 6)
                    heir.share = share
                    total_shares += share
                    self.reasoning.append(f"  • الجد: {share} (السدس فرضا - كالأب)")
                # Si pas d'enfants, le grand-père prendra par 'asaba
            
            # Mère
            elif relation == "الأم":
                num_siblings = sum(1 for h in self.heirs 
                                  if ("أخ" in h.relation or "أخت" in h.relation) 
                                  and not h.is_blocked)
                
                if has_children or num_siblings >= 2:
                    share = Fraction(1, 6)
                    self.reasoning.append(f"  • الأم: {share} (السدس)")
                else:
                    share = Fraction(1, 3)
                    self.reasoning.append(f"  • الأم: {share} (الثلث)")
                
                heir.share = share
                total_shares += share
        
        self.reasoning.append(f"\n  📌 **مجموع الفروض = {total_shares}**")
        return total_shares
    
    def distribute_asaba(self, remainder: Fraction):
        """Distribuer par 'asaba (عصبة)"""
        self.reasoning.append(f"\n🔄 **توزيع العصبة (الباقي = {remainder}):**")
        
        # Fils et filles par 'asaba
        sons = [h for h in self.heirs if h.relation == "الابن" and not h.is_blocked]
        daughters = [h for h in self.heirs 
                    if h.relation == "البنت" and not h.is_blocked and h.share == 0]
        
        if sons or daughters:
            total_units = len(sons) * 2 + len(daughters)
            unit_share = remainder / total_units
            
            self.reasoning.append(f"  • عدد الأبناء: {len(sons)}")
            self.reasoning.append(f"  • عدد البنات: {len(daughters)}")
            self.reasoning.append(f"  • القاعدة: للذكر مثل حظ الأنثيين")
            
            for son in sons:
                son.share = unit_share * 2
            for daughter in daughters:
                daughter.share = unit_share
            return
        
        # Père hérite le reste (même s'il a déjà reçu 1/6 comme fard)
        father = next((h for h in self.heirs if h.relation == "الأب" and not h.is_blocked), None)
        if father and remainder > 0:
            if father.share > 0:
                # Le père a déjà un fard (1/6), il prend aussi le reste
                self.reasoning.append(f"  • الأب له {father.share} فرضا (السدس)")
                father.share += remainder
                self.reasoning.append(f"  • الأب يأخذ الباقي عصبة: {remainder}")
                self.reasoning.append(f"  • المجموع للأب: {father.share}")
            else:
                # Le père n'a pas de fard, il prend tout par 'asaba
                father.share = remainder
                self.reasoning.append(f"  • الأب يرث الباقي عصبة: {remainder}")
            return
        
        # Grand-père hérite le reste (en l'absence du père)
        grandfather = next((h for h in self.heirs if h.relation == "الجد" and not h.is_blocked), None)
        if grandfather and remainder > 0:
            if grandfather.share > 0:
                # Le grand-père a déjà un fard (1/6), il prend aussi le reste
                self.reasoning.append(f"  • الجد له {grandfather.share} فرضا (السدس)")
                grandfather.share += remainder
                self.reasoning.append(f"  • الجد يأخذ الباقي عصبة: {remainder}")
                self.reasoning.append(f"  • المجموع للجد: {grandfather.share}")
            else:
                # Le grand-père n'a pas de fard, il prend tout par 'asaba
                grandfather.share = remainder
                self.reasoning.append(f"  • الجد يرث الباقي عصبة (كالأب): {remainder}")
            return
        
        # Frères germains
        brothers_full = [h for h in self.heirs 
                        if h.relation == "الأخ_الشقيق" and not h.is_blocked]
        sisters_full = [h for h in self.heirs 
                       if h.relation == "الأخت_الشقيقة" and not h.is_blocked and h.share == 0]
        
        if brothers_full or sisters_full:
            total_units = len(brothers_full) * 2 + len(sisters_full)
            unit_share = remainder / total_units
            
            self.reasoning.append(f"  • الإخوة الأشقاء يرثون بالعصبة")
            self.reasoning.append(f"  • عدد الإخوة: {len(brothers_full)}")
            self.reasoning.append(f"  • عدد الأخوات: {len(sisters_full)}")
            
            for brother in brothers_full:
                brother.share = unit_share * 2
            for sister in sisters_full:
                sister.share = unit_share
            return
        
        # Frères consanguins
        brothers_paternal = [h for h in self.heirs 
                            if h.relation == "الأخ_لأب" and not h.is_blocked]
        sisters_paternal = [h for h in self.heirs 
                           if h.relation == "الأخت_لأب" and not h.is_blocked and h.share == 0]
        
        if brothers_paternal or sisters_paternal:
            total_units = len(brothers_paternal) * 2 + len(sisters_paternal)
            unit_share = remainder / total_units
            
            self.reasoning.append(f"  • الإخوة لأب يرثون بالعصبة")
            self.reasoning.append(f"  • عدد الإخوة: {len(brothers_paternal)}")
            self.reasoning.append(f"  • عدد الأخوات: {len(sisters_paternal)}")
            
            for brother in brothers_paternal:
                brother.share = unit_share * 2
            for sister in sisters_paternal:
                sister.share = unit_share
            return
    
    def calculate(self) -> Dict:
        """Calculer l'héritage complet"""
        self.steps = []
        self.reasoning = ["\n🎯 **بدء عملية الحل:**\n"]
        
        # Étape 1: Hijab
        self.apply_hijab_rules()
        
        # Étape 2: Fards
        total_fards = self.calculate_fixed_shares()
        
        # Étape 3: 'Asaba
        if not self.check_umariyyatayn():
            remainder = 1 - total_fards
            if remainder > 0:
                self.distribute_asaba(remainder)
        
        # Résultats
        self.reasoning.append("\n✅ **النتائج النهائية:**")
        results = {}
        
        for heir in self.heirs:
            if heir.is_blocked:
                results[heir.name] = "محجوب"
            else:
                percentage = float(heir.share) * 100
                results[heir.name] = {
                    "الكسر": str(heir.share),
                    "النسبة_المئوية": round(percentage, 2),
                    "الصلة": heir.relation
                }
        
        return {
            "النتائج": results,
            "الخطوات": self.steps,
            "الاستدلالات": self.reasoning
        }
    
    def get_heir_share(self, heir_name: str) -> Fraction:
        """Obtenir la part d'un héritier spécifique"""
        for heir in self.heirs:
            if heir.name == heir_name:
                return heir.share
        return Fraction(0, 1)
    
    def get_total_distributed(self) -> Fraction:
        """Obtenir le total distribué"""
        return sum(h.share for h in self.heirs if not h.is_blocked)
    
    def validate_distribution(self) -> bool:
        """Valider que la distribution est correcte (total = 1)"""
        total = self.get_total_distributed()
        return total == Fraction(1, 1)


# ============================================
# INTERFACE SYSTÈME COMPLET
# ============================================

class HeritageSystem:
    """
    Interface principale du système d'héritage
    Coordonne la détection et le calcul
    """
    
    def __init__(self):
        from heir_detector import HeirDetector
        self.detector = HeirDetector()
        self.calculator = None
        
    def solve(self, query: str, verbose: bool = True) -> Dict:
        """
        Résoudre un cas d'héritage complet
        
        Args:
            query: Question en arabe
            verbose: Afficher les détails
        
        Returns:
            Dictionnaire avec résultats et raisonnement
        """
        # Phase 1: Détection
        heirs = self.detector.detect_heirs(query)
        
        if verbose:
            print(self.detector.get_detection_summary())
        
        if not heirs:
            return {
                "error": "لم يتم اكتشاف أي ورثة",
                "النتائج": {},
                "الاستدلالات": ["⚠️ لم يتم العثور على ورثة في النص المدخل"]
            }
        
        # Phase 2: Calcul
        self.calculator = HeritageCalculator(heirs)
        result = self.calculator.calculate()
        
        # Ajouter le résumé de détection au début
        result["ملخص_الكشف"] = self.detector.get_detection_summary()
        
        return result
    
    def solve_and_print(self, query: str):
        """Résoudre et afficher de manière formatée"""
        print("=" * 70)
        print(f"📝 السؤال: {query}")
        print("=" * 70)
        
        result = self.solve(query, verbose=True)
        
        if "error" in result:
            print(f"\n❌ {result['error']}")
            return
        
        print("\n" + "=" * 70)
        print("💡 التفاصيل والاستدلالات:")
        print("=" * 70)
        print("\n".join(result["الاستدلالات"]))
        
        print("\n" + "=" * 70)
        print("📊 النتائج النهائية:")
        print("=" * 70)
        
        for heir_name, share in result["النتائج"].items():
            if share == "محجوب":
                print(f"  ❌ {heir_name}: محجوب")
            else:
                print(f"  ✅ {heir_name}: {share['الكسر']} ({share['النسبة_المئوية']}%)")


# ============================================
# TESTS
# ============================================

if __name__ == "__main__":
    print("🧪 TEST DU MODULE heritage_calculator.py\n")
    print("="*70)
    
    system = HeritageSystem()
    
    test_cases = [
        "ترك زوجة وولدان وبنتان",
        "توفي عن زوجة وأب وأم",
        "ماتت عن زوج وأب وأم",
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n\n{'='*70}")
        print(f"TEST {i}:")
        print(f"{'='*70}")
        system.solve_and_print(test)
