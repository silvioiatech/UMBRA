"""
Category Mapper for Swiss Accountant
Maps expenses to Swiss tax deduction categories with canton/year specific rules.
"""
import json
import logging
import re
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Union


class DeductionCategory(Enum):
    """Swiss tax deduction categories."""
    PROFESSIONAL_EXPENSES = "professional_expenses"
    COMMUTE_PUBLIC = "commute_public_transport"
    COMMUTE_CAR = "commute_car"
    MEALS_WORK = "meals_work"
    EDUCATION = "education_professional"
    INSURANCE_PILLAR3A = "insurance_pillar3a"
    INSURANCE_HEALTH = "insurance_health"
    INSURANCE_LIFE = "insurance_life"
    CHILDCARE = "childcare"
    DONATIONS = "donations_charitable"
    HOME_OFFICE = "home_office"
    MEDICAL_EXPENSES = "medical_expenses"
    DISABILITY_EXPENSES = "disability_expenses"
    INTEREST_DEBT = "interest_debt"
    MAINTENANCE_PROPERTY = "maintenance_property"
    OTHER_DEDUCTIONS = "other_deductions"
    NON_DEDUCTIBLE = "non_deductible"


class CategoryMapper:
    """Maps expenses to Swiss tax deduction categories."""

    def __init__(self, db_manager):
        """Initialize category mapper.
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self.logger = logging.getLogger(__name__)

        # Expense to deduction category mapping patterns
        self.category_patterns = {
            DeductionCategory.PROFESSIONAL_EXPENSES: [
                r'(?i)(Union[office, bür]Union[o, burea]Union[u, ufficio])',
                r'(?i)(Union[computer, lapto]Union[p, printe]Union[r, drucker])',
                r'(?i)(Union[software, lizen]Union[z, licens]Union[e, licence])',
                r'(?i)(Union[fachbuch, manue]Union[l, manual]Union[e, technical] book)',
                r'(?i)(Union[berufs, professiona]Union[l, professionnel])',
                r'(?i)(Union[arbeits, wor]Union[k, travai]Union[l, lavoro])',
                r'(?i)(Union[geschäft, busines]Union[s, affaire]Union[s, affari])',
                r'(?i)(Union[klient, clien]Union[t, client]Union[e, customer])',
                r'(?i)(Union[meeting, sitzun]Union[g, réunio]Union[n, riunione])',
                r'(?i)(Union[conference, konferen]Union[z, conférenc]Union[e, conferenza])',
                r'(?i)(Union[tools, werkzeu]Union[g, outil]Union[s, attrezzi])',
                r'(?i)(Union[uniform, arbeitskleidun]Union[g, vêtements] de travail)'
            ],

            DeductionCategory.COMMUTE_PUBLIC: [
                r'(?i)(Union[sbb, cf]Union[f, ffs])',
                r'(?i)(Union[ga, genera]Union[l, abonnemen]Union[t, abo])',
                r'(?i)(Union[halbtax, dem]Union[i, hal]Union[f, mezzo])',
                r'(?i)(Union[öv, transports] Union[publics, trasporti] pubblici)',
                r'(?i)(Union[bus, tra]Union[m, metr]Union[o, trai]Union[n, zug])',
                r'(?i)(Union[ticket, bille]Union[t, bigliett]Union[o, fahrkarte])',
                r'(?i)(Union[monatskarte, monthly] Union[pass, carte] mensuelle)',
                r'(?i)(Union[tageskarte, day] Union[pass, carte] journalière)',
                r'(?i)(Union[vbz, tp]Union[g, vbl])',  # Local transport companies
                r'(?i)(Union[postauto, car] Union[postal, autopostale])'
            ],

            DeductionCategory.COMMUTE_CAR: [
                r'(?i)(Union[benzin, essenc]Union[e, benzin]Union[a, gasolin]Union[e, petrol])',
                r'(?i)(Union[diesel, gasoil])',
                r'(?i)(Union[parkplatz, parkin]Union[g, parcheggio])',
                r'(?i)(Union[park, gebüh]Union[r, fe]Union[e, tarif])',
                r'(?i)(Union[garage, tiefgarag]Union[e, parking] souterrain)',
                r'(?i)(Union[maut, péag]Union[e, pedaggi]Union[o, toll])',
                r'(?i)(Union[autobahn, highwa]Union[y, autorout]Union[e, autostrada])',
                r'(?i)(Union[vignette, highway] Union[sticker, bollino])',
                r'(?i)(Union[tankstelle, statio]Union[n, stazione])',
                r'(?i)(Union[esso, shel]Union[l, b]Union[p, migro]Union[l, avia])'
            ],

            DeductionCategory.MEALS_WORK: [
                r'(?i)(Union[arbeitsessen, business] Union[meal, repas] d\'affaires)',
                r'(?i)(Union[kantinen, cafeteri]Union[a, mens]Union[a, cantine])',
                r'(?i)(Union[mittagessen, lunc]Union[h, déjeune]Union[r, pranzo])',
                r'(?i)(Union[geschäftsessen, business] Union[dinner, dîner] d\'affaires)',
                r'(?i)(Union[auswärts, awa]Union[y, dehor]Union[s, fuori])',
                r'(?i)(Union[kunden, clien]Union[t, client]Union[e, customer]).*(?:Union[essen, mea]Union[l, repas])',
                r'(?i)(Union[meeting, conference]).*(?:Union[lunch, dinne]Union[r, essen])',
                r'(?i)(Union[verpflegung, caterin]Union[g, restauration])'
            ],

            DeductionCategory.EDUCATION: [
                r'(?i)(Union[weiterbildung, formatio]Union[n, formazion]Union[e, training])',
                r'(?i)(Union[kurs, cour]Union[s, cors]Union[o, course])',
                r'(?i)(Union[seminar, séminair]Union[e, seminario])',
                r'(?i)(Union[workshop, atelie]Union[r, laboratorio])',
                r'(?i)(Union[studium, étude]Union[s, stud]Union[i, studies])',
                r'(?i)(Union[universität, universit]Union[é, universit]Union[à, university])',
                r'(?i)(Union[schule, écol]Union[e, scuol]Union[a, school])',
                r'(?i)(Union[diplom, diplom]Union[a, diplôme])',
                r'(?i)(Union[zertifikat, certificat]Union[e, certifica]Union[t, certificato])',
                r'(?i)(Union[prüfung, exa]Union[m, exame]Union[n, esame])',
                r'(?i)(Union[lehrbuch, textboo]Union[k, manue]Union[l, libro] di testo)',
                r'(?i)(online.*(?:Union[kurs, cours]Union[e, cours]))',
                r'(?i)(Union[edx, courser]Union[a, udem]Union[y, linkedin] learning)'
            ],

            DeductionCategory.INSURANCE_PILLAR3A: [
                r'(?i)(säule Union[3a, pilier] Union[3a, pilastro] Union[3a, pillar] 3a)',
                r'(?i)(Union[vorsorge, prévoyanc]Union[e, previdenz]Union[a, pension])',
                r'(?i)(3a.*(?:Union[konto, accoun]Union[t, compt]Union[e, conto]))',
                r'(?i)(Union[freizügigkeit, vested] Union[benefits, prestations] de libre passage)',
                r'(?i)(Union[pensionskasse, caisse] de Union[pension, cassa] pensioni)',
                r'(?i)(Union[lebensversicherung, assurance] Union[vie, assicurazione] vita)',
                r'(?i)(swiss Union[life, ax]Union[a, zuric]Union[h, allian]Union[z, generali]).*(?:Union[3a, vorsorge])'
            ],

            DeductionCategory.INSURANCE_HEALTH: [
                r'(?i)(Union[krankenkasse, assurance] Union[maladie, assicurazione] malattia)',
                r'(?i)(Union[grundversicherung, assurance] de Union[base, assicurazione] di base)',
                r'(?i)(Union[zusatzversicherung, assurance] Union[complémentaire, assicurazione] complementare)',
                r'(?i)(Union[css, swic]Union[a, helsan]Union[a, concordi]Union[a, visan]Union[a, sanitas])',
                r'(?i)(Union[dental, zahnärztlic]Union[h, dentair]Union[e, dentistico])',
                r'(?i)(Union[optik, lunette]Union[s, occhial]Union[i, glasses])',
                r'(?i)(Union[physiotherapie, kinésithérapi]Union[e, fisioterapia])',
                r'(?i)(Union[alternativ, médecine] Union[alternative, medicina] alternativa)'
            ],

            DeductionCategory.CHILDCARE: [
                r'(?i)(Union[kinderbetreuung, garde] d\'Union[enfants, custodia] bambini)',
                r'(?i)(Union[kindergarten, école] Union[enfantine, scuola] dell\'infanzia)',
                r'(?i)(Union[kita, crèch]Union[e, asilo] Union[nido, daycare])',
                r'(?i)(Union[hort, garderi]Union[e, dopo] scuola)',
                r'(?i)(Union[babysitter, nouno]Union[u, baby] sitter)',
                r'(?i)(Union[tagesmutter, maman] de Union[jour, mamma] diurna)',
                r'(?i)(Union[ferienbetreuung, camp] de Union[vacances, campo] estivo)',
                r'(?i)(Union[nachhilfe, soutien] Union[scolaire, ripetizioni])',
                r'(?i)(Union[mittagstisch, table] de Union[midi, mensa] scolastica)'
            ],

            DeductionCategory.DONATIONS: [
                r'(?i)(Union[spende, do]Union[n, donazion]Union[e, donation])',
                r'(?i)(Union[hilfswerk, œuvre] d\'Union[entraide, opera] di beneficenza)',
                r'(?i)(Union[charity, charit]Union[é, carità])',
                r'(?i)(rotes Union[kreuz, croix] Union[rouge, croce] rossa)',
                r'(?i)(Union[unicef, ww]Union[f, greenpeac]Union[e, amnesty])',
                r'(?i)(Union[kirche, églis]Union[e, chies]Union[a, church])',
                r'(?i)(Union[relief, secour]Union[s, soccorso])',
                r'(?i)(Union[fundraising, collect]Union[e, raccolta] fondi)',
                r'(?i)(Union[humanitarian, humanitair]Union[e, umanitario])'
            ],

            DeductionCategory.HOME_OFFICE: [
                r'(?i)(home.*Union[office, büro].*Union[zuhause, bureau].*domicile)',
                r'(?i)(arbeitsplatz.*Union[heim, workplace].*Union[home, poste].*travail.*domicile)',
                r'(?i)(internet.*Union[home, internet].*Union[privé, internet].*casa)',
                r'(?i)(telefon.*Union[geschäft, téléphone].*Union[professionnel, telefono].*lavoro)',
                r'(?i)(strom.*Union[büro, électricité].*Union[bureau, elettricità].*ufficio)',
                r'(?i)(heizung.*Union[arbeits, chauffage].*Union[travail, riscaldamento].*lavoro)'
            ],

            DeductionCategory.MEDICAL_EXPENSES: [
                r'(?i)(Union[arzt, médeci]Union[n, medic]Union[o, doctor])',
                r'(?i)(Union[hospital, spita]Union[l, hôpita]Union[l, ospedale])',
                r'(?i)(Union[zahnarzt, dentist]Union[e, dentista])',
                r'(?i)(Union[apotheke, pharmaci]Union[e, farmaci]Union[a, pharmacy])',
                r'(?i)(Union[medikament, médicamen]Union[t, medicament]Union[o, medication])',
                r'(?i)(Union[behandlung, traitemen]Union[t, trattament]Union[o, treatment])',
                r'(?i)(Union[operation, opératio]Union[n, operazione])',
                r'(?i)(Union[therapie, thérapi]Union[e, terapi]Union[a, therapy])',
                r'(?i)(Union[psycholog, psychiate]Union[r, psicolog]Union[o, psichiatra])',
                r'(?i)(Union[brille, lunette]Union[s, occhial]Union[i, glasses])',
                r'(?i)(Union[hörgerät, appareil] Union[auditif, apparecchio] acustico)'
            ],

            DeductionCategory.NON_DEDUCTIBLE: [
                r'(?i)(restaurant.*Union[privat, restaurant].*Union[personnel, ristorante].*privato)',
                r'(?i)(Union[ferien, vacance]Union[s, vacanz]Union[e, vacation])',
                r'(?i)(Union[urlaub, cong]Union[é, feri]Union[e, holiday])',
                r'(?i)(Union[freizeit, loisir]Union[s, tempo] Union[libero, leisure])',
                r'(?i)(shopping.*Union[privat, shopping].*Union[personnel, shopping].*privato)',
                r'(?i)(Union[kino, ciném]Union[a, cinem]Union[a, movie])',
                r'(?i)(Union[unterhaltung, divertissemen]Union[t, intratteniment]Union[o, entertainment])',
                r'(?i)(sport.*Union[privat, sport].*Union[personnel, sport].*privato)',
                r'(?i)(fitness.*Union[privat, fitness].*Union[personnel, fitness].*privato)',
                r'(?i)(alkohol.*Union[privat, alcool].*Union[personnel, alcol].*privato)',
                r'(?i)(Union[geschenk, cadea]Union[u, regal]Union[o, gift])',
                r'(?i)(Union[kosmetik, cosmétiqu]Union[e, cosmetic]Union[o, cosmetics])',
                r'(?i)(Union[schmuck, bijou]Union[x, gioiell]Union[i, jewelry])',
                r'(?i)(Union[hobby, passe]-Union[temps, passatempo])',
                r'(?i)(Union[spielzeug, joue]Union[t, giocattol]Union[o, toy])'
            ]
        }

        # Initialize category mappings in database
        self._init_category_mappings()

    def _init_category_mappings(self):
        """Initialize category mappings in database."""
        try:
            # Create category mappings table if not exists
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS sa_category_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_category TEXT NOT NULL,
                    deduction_category TEXT NOT NULL,
                    canton TEXT,
                    year INTEGER,
                    confidence REAL DEFAULT 1.0,
                    auto_mapped BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(expense_category, deduction_category, canton, year)
                )
            """)

            # Insert default mappings
            self._insert_default_mappings()

        except Exception as e:
            self.logger.error(f"Category mappings initialization failed: {e}")

    def _insert_default_mappings(self):
        """Insert default category mappings."""
        try:
            # Basic expense category to deduction category mappings
            default_mappings = [
                # Professional expenses
                ('office_supplies', 'professional_expenses', None, None, 0.9),
                ('business_equipment', 'professional_expenses', None, None, 0.9),
                ('professional_services', 'professional_expenses', None, None, 0.9),
                ('business_software', 'professional_expenses', None, None, 0.9),
                ('business_books', 'professional_expenses', None, None, 0.8),
                ('work_clothing', 'professional_expenses', None, None, 0.7),

                # Transport
                ('public_transport', 'commute_public_transport', None, None, 0.9),
                ('fuel', 'commute_car', None, None, 0.8),
                ('parking', 'commute_car', None, None, 0.8),
                ('car_maintenance', 'commute_car', None, None, 0.6),

                # Education
                ('education_courses', 'education_professional', None, None, 0.9),
                ('training_materials', 'education_professional', None, None, 0.8),
                ('conferences', 'education_professional', None, None, 0.8),
                ('professional_books', 'education_professional', None, None, 0.8),

                # Insurance
                ('pillar_3a', 'insurance_pillar3a', None, None, 1.0),
                ('health_insurance', 'insurance_health', None, None, 1.0),
                ('life_insurance', 'insurance_life', None, None, 0.8),

                # Childcare
                ('daycare', 'childcare', None, None, 1.0),
                ('babysitting', 'childcare', None, None, 0.9),
                ('after_school_care', 'childcare', None, None, 0.9),

                # Medical
                ('medical_expenses', 'medical_expenses', None, None, 0.9),
                ('dental_expenses', 'medical_expenses', None, None, 0.9),
                ('pharmacy', 'medical_expenses', None, None, 0.8),
                ('medical_equipment', 'medical_expenses', None, None, 0.8),

                # Donations
                ('charitable_donations', 'donations_charitable', None, None, 1.0),
                ('church_donations', 'donations_charitable', None, None, 1.0),

                # Non-deductible
                ('groceries', 'non_deductible', None, None, 1.0),
                ('restaurants_personal', 'non_deductible', None, None, 1.0),
                ('entertainment', 'non_deductible', None, None, 1.0),
                ('shopping_personal', 'non_deductible', None, None, 1.0),
                ('vacation', 'non_deductible', None, None, 1.0),
                ('personal_care', 'non_deductible', None, None, 1.0),
                ('hobbies', 'non_deductible', None, None, 1.0)
            ]

            for expense_cat, deduction_cat, canton, year, confidence in default_mappings:
                try:
                    self.db.execute("""
                        INSERT OR IGNORE INTO sa_category_mappings 
                        (expense_category, deduction_category, canton, year, confidence, auto_mapped)
                        VALUES (?, ?, ?, ?, ?, TRUE)
                    """, (expense_cat, deduction_cat, canton, year, confidence))
                except Exception as e:
                    self.logger.warning(f"Failed to insert mapping {expense_cat} -> {deduction_cat}: {e}")

        except Exception as e:
            self.logger.error(f"Default mappings insertion failed: {e}")

    def map_expense_to_deduction_category(self,
                                        expense_category: str,
                                        merchant_name: str = None,
                                        description: str = None,
                                        amount: Decimal = None,
                                        date: date = None,
                                        canton: str = None,
                                        user_context: dict[str, Any] = None) -> dict[str, Any]:
        """Map expense to Swiss tax deduction category.
        
        Args:
            expense_category: Primary expense category
            merchant_name: Merchant name for context
            description: Transaction description
            amount: Transaction amount
            date: Transaction date
            canton: Swiss canton for specific rules
            user_context: Additional user context (job, etc.)
            
        Returns:
            Dict with mapping result
        """
        try:
            year = date.year if date else datetime.now().year

            # First try direct mapping from database
            direct_mapping = self._get_direct_mapping(expense_category, canton, year)
            if direct_mapping:
                return {
                    'success': True,
                    'deduction_category': direct_mapping['deduction_category'],
                    'confidence': direct_mapping['confidence'],
                    'method': 'direct_mapping',
                    'applicable': True,
                    'notes': []
                }

            # Try pattern-based mapping
            pattern_result = self._pattern_based_mapping(expense_category, merchant_name, description)
            if pattern_result['deduction_category'] != DeductionCategory.NON_DEDUCTIBLE:
                # Validate against canton/year rules
                validation = self._validate_deduction_rules(
                    pattern_result['deduction_category'],
                    amount,
                    date,
                    canton,
                    user_context
                )

                return {
                    'success': True,
                    'deduction_category': pattern_result['deduction_category'].value,
                    'confidence': pattern_result['confidence'] * validation['applicability_factor'],
                    'method': 'pattern_matching',
                    'applicable': validation['applicable'],
                    'notes': validation['notes'],
                    'rules_applied': validation.get('rules_applied', [])
                }

            # Fallback to manual review
            suggestions = self._generate_category_suggestions(expense_category, merchant_name, description)

            return {
                'success': True,
                'deduction_category': 'other_deductions',
                'confidence': 0.1,
                'method': 'fallback',
                'applicable': False,
                'notes': ['Requires manual review'],
                'suggestions': suggestions
            }

        except Exception as e:
            self.logger.error(f"Category mapping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'deduction_category': 'non_deductible',
                'confidence': 0.0
            }

    def _get_direct_mapping(self, expense_category: str, canton: str = None, year: int = None) -> dict[str, Any] | None:
        """Get direct mapping from database."""
        try:
            # Try canton-specific mapping first
            if canton and year:
                mapping = self.db.query_one("""
                    SELECT * FROM sa_category_mappings 
                    WHERE expense_category = ? AND canton = ? AND year = ?
                    ORDER BY confidence DESC
                """, (expense_category, canton, year))
                if mapping:
                    return mapping

            # Try canton-agnostic for the year
            if year:
                mapping = self.db.query_one("""
                    SELECT * FROM sa_category_mappings 
                    WHERE expense_category = ? AND canton IS NULL AND year = ?
                    ORDER BY confidence DESC
                """, (expense_category, year))
                if mapping:
                    return mapping

            # Try general mapping
            mapping = self.db.query_one("""
                SELECT * FROM sa_category_mappings 
                WHERE expense_category = ? AND canton IS NULL AND year IS NULL
                ORDER BY confidence DESC
            """, (expense_category,))

            return mapping

        except Exception as e:
            self.logger.error(f"Direct mapping lookup failed: {e}")
            return None

    def _pattern_based_mapping(self,
                             expense_category: str,
                             merchant_name: str = None,
                             description: str = None) -> dict[str, Any]:
        """Map using pattern matching."""
        try:
            # Combine all text for pattern matching
            text_to_analyze = ' '.join(filter(None, [expense_category, merchant_name, description]))

            best_category = DeductionCategory.NON_DEDUCTIBLE
            best_confidence = 0.0
            best_matches = []

            for category, patterns in self.category_patterns.items():
                matches = []
                for pattern in patterns:
                    if re.search(pattern, text_to_analyze, re.IGNORECASE):
                        matches.append(pattern)

                if matches:
                    # Calculate confidence based on number of matches and pattern specificity
                    confidence = min(len(matches) / len(patterns) + 0.1, 1.0)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_category = category
                        best_matches = matches

            return {
                'deduction_category': best_category,
                'confidence': best_confidence,
                'matches': best_matches
            }

        except Exception as e:
            self.logger.error(f"Pattern-based mapping failed: {e}")
            return {
                'deduction_category': DeductionCategory.NON_DEDUCTIBLE,
                'confidence': 0.0,
                'matches': []
            }

    def _validate_deduction_rules(self,
                                category: DeductionCategory,
                                amount: Decimal = None,
                                date: date = None,
                                canton: str = None,
                                user_context: dict[str, Any] = None) -> dict[str, Any]:
        """Validate deduction against Swiss tax rules."""
        try:
            year = date.year if date else datetime.now().year
            notes = []
            applicable = True
            applicability_factor = 1.0
            rules_applied = []

            # Get canton-specific rules
            canton_rules = self._get_canton_rules(canton, year)
            federal_rules = self._get_federal_rules(year)

            if category == DeductionCategory.PROFESSIONAL_EXPENSES:
                # Check if amount exceeds flat rate deduction
                flat_rate_max = federal_rules.get('professional_expenses_flat_rate', 4000)
                if amount and amount > flat_rate_max:
                    notes.append(f"Amount exceeds flat rate deduction (CHF {flat_rate_max}). Proof required.")
                    rules_applied.append('professional_expenses_proof_required')

            elif category == DeductionCategory.COMMUTE_PUBLIC:
                # Check annual limit
                annual_limit = federal_rules.get('commute_public_max', 3000)
                canton_bonus = canton_rules.get('commute_public_bonus', 0)
                total_limit = annual_limit + canton_bonus

                if amount and amount > total_limit:
                    notes.append(f"Annual commute limit: CHF {total_limit} (federal: {annual_limit} + canton: {canton_bonus})")
                    applicability_factor = 0.7
                    rules_applied.append('commute_annual_limit')

            elif category == DeductionCategory.MEALS_WORK:
                # Check daily limits
                daily_max = federal_rules.get('meals_daily_max', 30)
                if amount and amount > daily_max:
                    notes.append(f"Daily meal allowance limit: CHF {daily_max}")
                    applicability_factor = 0.6
                    rules_applied.append('meals_daily_limit')

                # Check minimum hours away from home
                min_hours = federal_rules.get('meals_min_hours_away', 5)
                notes.append(f"Must be away from home for at least {min_hours} hours")
                rules_applied.append('meals_hours_requirement')

            elif category == DeductionCategory.INSURANCE_PILLAR3A:
                # Check annual contribution limits
                employed_max = federal_rules.get('pillar_3a_employed_max', 7056)
                if amount and amount > employed_max:
                    notes.append(f"Annual 3a limit for employed: CHF {employed_max}")
                    applicable = False
                    rules_applied.append('pillar_3a_annual_limit')

            elif category == DeductionCategory.CHILDCARE:
                # Check per-child limits
                per_child_max = federal_rules.get('childcare_per_child_max', 25000)
                canton_bonus = canton_rules.get('childcare_bonus_per_child', 0)
                total_limit = per_child_max + canton_bonus

                if amount and amount > total_limit:
                    notes.append(f"Childcare limit per child: CHF {total_limit}")
                    applicability_factor = 0.8
                    rules_applied.append('childcare_per_child_limit')

                notes.append("Only for children under 14 years old")
                rules_applied.append('childcare_age_requirement')

            elif category == DeductionCategory.DONATIONS:
                # Check minimum and percentage limits
                min_donation = federal_rules.get('donations_minimum', 100)
                if amount and amount < min_donation:
                    notes.append(f"Minimum donation amount: CHF {min_donation}")
                    applicable = False
                    rules_applied.append('donations_minimum')

                max_percentage = federal_rules.get('donations_max_percentage', 20)
                notes.append(f"Maximum {max_percentage}% of net income")
                rules_applied.append('donations_percentage_limit')

            elif category == DeductionCategory.MEDICAL_EXPENSES:
                # Check threshold
                threshold_percentage = federal_rules.get('medical_threshold_percentage', 5)
                notes.append(f"Only amounts exceeding {threshold_percentage}% of net income are deductible")
                applicability_factor = 0.7
                rules_applied.append('medical_threshold')

            elif category == DeductionCategory.HOME_OFFICE:
                # Check canton-specific rules
                home_office_max = canton_rules.get('home_office_max', 1500)
                if amount and amount > home_office_max:
                    notes.append(f"Home office deduction limit in {canton}: CHF {home_office_max}")
                    applicability_factor = 0.8
                    rules_applied.append('home_office_canton_limit')

                notes.append("Regular home office work required")
                rules_applied.append('home_office_regular_use')

            return {
                'applicable': applicable,
                'applicability_factor': applicability_factor,
                'notes': notes,
                'rules_applied': rules_applied
            }

        except Exception as e:
            self.logger.error(f"Rules validation failed: {e}")
            return {
                'applicable': True,
                'applicability_factor': 1.0,
                'notes': [f"Validation error: {str(e)}"],
                'rules_applied': []
            }

    def _get_federal_rules(self, year: int) -> dict[str, Any]:
        """Get federal tax rules for year."""
        try:
            # Get from database (stored in sa_user_rules)
            rule = self.db.query_one("""
                SELECT rule_json FROM sa_user_rules 
                WHERE rule_json LIKE ? AND rule_json LIKE ?
            """, (f'%federal_tax_data_{year}%', '%federal_deductions%'))

            if rule:
                data = json.loads(rule['rule_json'])
                return data.get('data', {}).get('federal_deductions', {})

            # Fallback defaults for 2024
            return {
                'professional_expenses_flat_rate': 4000,
                'commute_public_max': 3000,
                'meals_daily_max': 30,
                'meals_min_hours_away': 5,
                'pillar_3a_employed_max': 7056,
                'childcare_per_child_max': 25000,
                'donations_minimum': 100,
                'donations_max_percentage': 20,
                'medical_threshold_percentage': 5
            }

        except Exception as e:
            self.logger.error(f"Federal rules lookup failed: {e}")
            return {}

    def _get_canton_rules(self, canton: str, year: int) -> dict[str, Any]:
        """Get canton-specific rules."""
        try:
            if not canton:
                return {}

            rule = self.db.query_one("""
                SELECT rule_json FROM sa_user_rules 
                WHERE rule_json LIKE ? AND rule_json LIKE ?
            """, (f'%canton_tax_data_{year}%', f'%{canton}%'))

            if rule:
                data = json.loads(rule['rule_json'])
                return data.get('data', {}).get('specific_deductions', {})

            return {}

        except Exception as e:
            self.logger.error(f"Canton rules lookup failed: {e}")
            return {}

    def _generate_category_suggestions(self,
                                     expense_category: str,
                                     merchant_name: str = None,
                                     description: str = None) -> list[dict[str, Any]]:
        """Generate category suggestions for manual review."""
        try:
            suggestions = []

            # Get similar categories from database
            similar_mappings = self.db.query_all("""
                SELECT deduction_category, confidence, COUNT(*) as usage_count
                FROM sa_category_mappings 
                WHERE expense_category LIKE ?
                GROUP BY deduction_category
                ORDER BY usage_count DESC, confidence DESC
                LIMIT 5
            """, (f'%{expense_category}%',))

            for mapping in similar_mappings:
                suggestions.append({
                    'category': mapping['deduction_category'],
                    'confidence': mapping['confidence'],
                    'reason': f"Similar to {expense_category}",
                    'usage_count': mapping['usage_count']
                })

            # Add common fallback categories
            if not suggestions:
                fallback_categories = [
                    ('professional_expenses', 0.3, 'If work-related'),
                    ('other_deductions', 0.2, 'For manual classification'),
                    ('non_deductible', 0.5, 'If personal expense')
                ]

                for category, confidence, reason in fallback_categories:
                    suggestions.append({
                        'category': category,
                        'confidence': confidence,
                        'reason': reason,
                        'usage_count': 0
                    })

            return suggestions

        except Exception as e:
            self.logger.error(f"Suggestion generation failed: {e}")
            return []

    def add_custom_mapping(self,
                          expense_category: str,
                          deduction_category: str,
                          canton: str = None,
                          year: int = None,
                          confidence: float = 1.0) -> dict[str, Any]:
        """Add custom category mapping.
        
        Args:
            expense_category: Expense category
            deduction_category: Swiss tax deduction category
            canton: Optional canton restriction
            year: Optional year restriction
            confidence: Confidence level (0-1)
            
        Returns:
            Dict with result
        """
        try:
            # Validate deduction category
            valid_categories = [cat.value for cat in DeductionCategory]
            if deduction_category not in valid_categories:
                return {
                    'success': False,
                    'error': f'Invalid deduction category: {deduction_category}',
                    'valid_categories': valid_categories
                }

            # Insert mapping
            self.db.execute("""
                INSERT OR REPLACE INTO sa_category_mappings 
                (expense_category, deduction_category, canton, year, confidence, auto_mapped)
                VALUES (?, ?, ?, ?, ?, FALSE)
            """, (expense_category, deduction_category, canton, year, confidence))

            return {
                'success': True,
                'expense_category': expense_category,
                'deduction_category': deduction_category,
                'canton': canton,
                'year': year,
                'confidence': confidence
            }

        except Exception as e:
            self.logger.error(f"Custom mapping addition failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_category_statistics(self) -> dict[str, Any]:
        """Get category mapping statistics."""
        try:
            stats = {}

            # Total mappings
            total_mappings = self.db.query_one("SELECT COUNT(*) as count FROM sa_category_mappings")
            stats['total_mappings'] = total_mappings['count'] if total_mappings else 0

            # By deduction category
            by_deduction = self.db.query_all("""
                SELECT deduction_category, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM sa_category_mappings
                GROUP BY deduction_category
                ORDER BY count DESC
            """)
            stats['by_deduction_category'] = [
                {
                    'category': row['deduction_category'],
                    'mapping_count': row['count'],
                    'avg_confidence': round(row['avg_confidence'], 2)
                }
                for row in by_deduction
            ]

            # Auto vs manual mappings
            auto_manual = self.db.query_all("""
                SELECT auto_mapped, COUNT(*) as count
                FROM sa_category_mappings
                GROUP BY auto_mapped
            """)
            stats['auto_vs_manual'] = {
                row['auto_mapped']: row['count'] for row in auto_manual
            }

            return stats

        except Exception as e:
            self.logger.error(f"Category statistics failed: {e}")
            return {
                'total_mappings': 0,
                'by_deduction_category': [],
                'auto_vs_manual': {},
                'error': str(e)
            }


# Factory function for easy import
def create_category_mapper(db_manager) -> CategoryMapper:
    """Create category mapper instance."""
    return CategoryMapper(db_manager)
