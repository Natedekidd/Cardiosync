"""
gene_database.py
Load and query the cardiovascular gene database
"""

import pandas as pd
import os


class GeneDatabase:
    """
    Handler for cardiovascular gene database
    """
    
    def __init__(self, csv_path='cardiovascular_genes.csv'):
        """
        Load gene database from CSV
        
        Args:
            csv_path (str): Path to gene database CSV file
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Gene database not found: {csv_path}")
        
        self.genes = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(self.genes)} gene variants from database")
    
    
    def get_variant_info(self, rsid):
        """
        Get information about a specific variant
        
        Args:
            rsid (str): RS number (e.g., 'rs429358')
            
        Returns:
            dict or None: Variant information
        """
        variant = self.genes[self.genes['rsid'] == rsid]
        
        if len(variant) == 0:
            return None
        
        return variant.iloc[0].to_dict()
    
    
    def get_gene_variants(self, gene_name):
        """
        Get all variants for a specific gene
        
        Args:
            gene_name (str): Gene symbol (e.g., 'APOE')
            
        Returns:
            pd.DataFrame: All variants for this gene
        """
        return self.genes[self.genes['gene_name'] == gene_name]
    
    
    def get_pharmacogenomic_variants(self):
        """
        Get all variants that affect drug response
        
        Returns:
            pd.DataFrame: Variants with drug interactions
        """
        return self.genes[self.genes['drug_interaction'].notna()]
    
    
    def calculate_polygenic_risk_score(self, user_genotypes):
        """
        Calculate polygenic risk score from user's genotypes
        
        Args:
            user_genotypes (dict): User's genotypes
                Format: {'rs429358': 'CC', 'rs7412': 'CT', ...}
        
        Returns:
            tuple: (prs_score, risk_variants_found, protective_variants_found)
        """
        prs_score = 1.0  # Start at baseline (1.0 = average risk)
        risk_variants = []
        protective_variants = []
        
        for rsid, genotype in user_genotypes.items():
            variant_info = self.get_variant_info(rsid)
            
            if variant_info is None:
                continue  # Variant not in our database
            
            risk_allele = variant_info['risk_allele']
            protective_allele = variant_info['protective_allele']
            effect_size = variant_info['effect_size']
            
            # Count risk alleles in genotype
            risk_allele_count = genotype.count(risk_allele)
            
            if risk_allele_count == 2:
                # Homozygous for risk allele (e.g., CC when C is risk)
                prs_score *= effect_size ** 2  # Square the effect
                risk_variants.append({
                    'gene': variant_info['gene_name'],
                    'rsid': rsid,
                    'genotype': genotype,
                    'effect': f"{effect_size**2:.2f}x",
                    'condition': variant_info['condition']
                })
            
            elif risk_allele_count == 1:
                # Heterozygous (e.g., CT when C is risk)
                prs_score *= effect_size
                risk_variants.append({
                    'gene': variant_info['gene_name'],
                    'rsid': rsid,
                    'genotype': genotype,
                    'effect': f"{effect_size:.2f}x",
                    'condition': variant_info['condition']
                })
            
            # Check for protective alleles
            protective_allele_count = genotype.count(protective_allele)
            if protective_allele_count == 2 and protective_allele != risk_allele:
                protective_variants.append({
                    'gene': variant_info['gene_name'],
                    'rsid': rsid,
                    'genotype': genotype,
                    'effect': f"{1/effect_size:.2f}x protective"
                })
        
        return prs_score, risk_variants, protective_variants
    
    
    def get_drug_recommendations(self, user_genotypes):
        """
        Get pharmacogenomic drug recommendations
        
        Args:
            user_genotypes (dict): User's genotypes
        
        Returns:
            dict: Drug recommendations categorized by safety
        """
        recommendations = {
            'safe': [],
            'caution': [],
            'avoid': []
        }
        
        # Check pharmacogenomic variants
        cyp2c19_genotypes = []
        cyp2c9_genotypes = []
        vkorc1_genotype = None
        slco1b1_genotype = None
        
        for rsid, genotype in user_genotypes.items():
            variant_info = self.get_variant_info(rsid)
            
            if variant_info is None or pd.isna(variant_info['drug_interaction']):
                continue
            
            gene = variant_info['gene_name']
            drug = variant_info['drug_interaction']
            risk_allele = variant_info['risk_allele']
            
            # CYP2C19 - affects clopidogrel
            if gene == 'CYP2C19':
                cyp2c19_genotypes.append((rsid, genotype, risk_allele))
            
            # CYP2C9 - affects warfarin
            elif gene == 'CYP2C9':
                cyp2c9_genotypes.append((rsid, genotype, risk_allele))
            
            # VKORC1 - affects warfarin
            elif gene == 'VKORC1':
                vkorc1_genotype = (rsid, genotype, risk_allele)
            
            # SLCO1B1 - affects statins
            elif gene == 'SLCO1B1':
                slco1b1_genotype = (rsid, genotype, risk_allele)
        
        # Analyze CYP2C19 for clopidogrel
        if cyp2c19_genotypes:
            poor_metabolizer = False
            for rsid, genotype, risk_allele in cyp2c19_genotypes:
                if rsid in ['rs4244285', 'rs4986893']:  # *2 or *3 alleles
                    if genotype.count(risk_allele) >= 1:
                        poor_metabolizer = True
            
            if poor_metabolizer:
                recommendations['avoid'].append({
                    'drug': 'Clopidogrel (Plavix)',
                    'reason': 'CYP2C19 poor metabolizer - reduced effectiveness',
                    'alternative': 'Use prasugrel or ticagrelor instead'
                })
                recommendations['safe'].append({
                    'drug': 'Prasugrel',
                    'reason': 'Not affected by CYP2C19 metabolism',
                    'note': 'Preferred antiplatelet for your genetic profile'
                })
            else:
                recommendations['safe'].append({
                    'drug': 'Clopidogrel',
                    'reason': 'Normal CYP2C19 metabolism',
                    'note': 'Standard effectiveness expected'
                })
        
        # Analyze CYP2C9/VKORC1 for warfarin
        if cyp2c9_genotypes or vkorc1_genotype:
            requires_adjustment = False
            for rsid, genotype, risk_allele in cyp2c9_genotypes:
                if genotype.count(risk_allele) >= 1:
                    requires_adjustment = True
            
            if vkorc1_genotype:
                rsid, genotype, risk_allele = vkorc1_genotype
                if genotype.count(risk_allele) >= 1:
                    requires_adjustment = True
            
            if requires_adjustment:
                recommendations['caution'].append({
                    'drug': 'Warfarin',
                    'reason': 'Genetic variants detected - requires dose adjustment',
                    'note': 'Start with lower dose, monitor INR closely'
                })
        
        # Analyze SLCO1B1 for statins
        if slco1b1_genotype:
            rsid, genotype, risk_allele = slco1b1_genotype
            if genotype.count(risk_allele) >= 1:
                recommendations['caution'].append({
                    'drug': 'Simvastatin (high dose)',
                    'reason': 'SLCO1B1 variant increases myopathy risk',
                    'note': 'Use lower doses or alternative statin (atorvastatin, rosuvastatin)'
                })
                recommendations['safe'].append({
                    'drug': 'Atorvastatin',
                    'reason': 'Lower risk of side effects with SLCO1B1 variant',
                    'note': 'Preferred statin for your genetic profile'
                })
            else:
                recommendations['safe'].append({
                    'drug': 'Statins (all types)',
                    'reason': 'No SLCO1B1 risk variants detected',
                    'note': 'Low risk of muscle-related side effects'
                })
        
        return recommendations
    
    
    def get_african_specific_variants(self):
        """
        Get variants that are particularly relevant for African populations
        
        Returns:
            pd.DataFrame: African-specific or high-frequency variants
        """
        # Filter for variants with higher frequency in Africans
        african_variants = self.genes[self.genes['african_frequency'] > 0.1]
        
        # Also include APOL1 regardless of frequency (important for Africans)
        apol1_variants = self.genes[self.genes['gene_name'] == 'APOL1']
        
        return pd.concat([african_variants, apol1_variants]).drop_duplicates()
    
    
    def generate_report_text(self, prs_score, risk_variants, protective_variants, drug_recommendations):
        """
        Generate human-readable genetic report
        
        Args:
            prs_score (float): Polygenic risk score
            risk_variants (list): List of risk variants found
            protective_variants (list): List of protective variants found
            drug_recommendations (dict): Drug safety recommendations
        
        Returns:
            str: Formatted report text
        """
        report = "🧬 GENETIC ANALYSIS RESULTS\n"
        report += "=" * 60 + "\n\n"
        
        # Overall genetic risk
        report += f"Your Genetic Risk Score: {prs_score:.2f}x average\n\n"
        
        if prs_score > 1.5:
            report += "⚠️ HIGHER THAN AVERAGE genetic risk for cardiovascular disease\n"
        elif prs_score > 1.2:
            report += "⚠️ MODERATELY ELEVATED genetic risk\n"
        elif prs_score < 0.8:
            report += "✅ LOWER THAN AVERAGE genetic risk (protective genes found)\n"
        else:
            report += "✅ AVERAGE genetic risk\n"
        
        report += "\n" + "=" * 60 + "\n\n"
        
        # Risk variants
        if risk_variants:
            report += "⚠️ RISK VARIANTS FOUND:\n\n"
            for var in risk_variants:
                report += f"• {var['gene']} ({var['rsid']})\n"
                report += f"  Your genotype: {var['genotype']}\n"
                report += f"  Effect: {var['effect']} risk for {var['condition']}\n\n"
        
        # Protective variants
        if protective_variants:
            report += "✅ PROTECTIVE VARIANTS FOUND:\n\n"
            for var in protective_variants:
                report += f"• {var['gene']} ({var['rsid']})\n"
                report += f"  Your genotype: {var['genotype']}\n"
                report += f"  Effect: {var['effect']}\n\n"
        
        report += "=" * 60 + "\n\n"
        
        # Drug recommendations
        report += "💊 MEDICATION RECOMMENDATIONS:\n\n"
        
        if drug_recommendations['avoid']:
            report += "❌ AVOID THESE MEDICATIONS:\n"
            for drug in drug_recommendations['avoid']:
                report += f"• {drug['drug']}\n"
                report += f"  Reason: {drug['reason']}\n"
                report += f"  Alternative: {drug['alternative']}\n\n"
        
        if drug_recommendations['caution']:
            report += "⚠️ USE WITH CAUTION:\n"
            for drug in drug_recommendations['caution']:
                report += f"• {drug['drug']}\n"
                report += f"  Reason: {drug['reason']}\n"
                report += f"  Note: {drug['note']}\n\n"
        
        if drug_recommendations['safe']:
            report += "✅ SAFE FOR YOU:\n"
            for drug in drug_recommendations['safe']:
                report += f"• {drug['drug']}\n"
                report += f"  Reason: {drug['reason']}\n\n"
        
        report += "=" * 60 + "\n"
        report += "NOTE: Discuss all medications with your doctor before making changes.\n"
        
        return report


# Example usage
if __name__ == "__main__":
    # Load database
    db = GeneDatabase('cardiovascular_genes.csv')
    
    # Example: User's genotypes from VCF file
    user_genotypes = {
        'rs429358': 'CC',  # APOE e4/e4 (high risk)
        'rs7412': 'CC',    # APOE e3/e3 (normal)
        'rs10455872': 'GA', # LPA (heterozygous risk)
        'rs4244285': 'AA',  # CYP2C19*2 (poor metabolizer)
    }
    
    # Calculate risk
    prs, risk_vars, protective_vars = db.calculate_polygenic_risk_score(user_genotypes)
    
    print(f"\nPolygenic Risk Score: {prs:.2f}x")
    print(f"Risk variants found: {len(risk_vars)}")
    print(f"Protective variants found: {len(protective_vars)}")
    
    # Get drug recommendations
    drug_recs = db.get_drug_recommendations(user_genotypes)
    
    print(f"\nDrug recommendations:")
    print(f"  Safe: {len(drug_recs['safe'])}")
    print(f"  Caution: {len(drug_recs['caution'])}")
    print(f"  Avoid: {len(drug_recs['avoid'])}")
    
    # Generate full report
    report = db.generate_report_text(prs, risk_vars, protective_vars, drug_recs)
    print("\n" + report)