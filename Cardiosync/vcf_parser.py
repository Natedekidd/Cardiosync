"""
vcf_parser.py
Parse VCF (Variant Call Format) files and extract cardiovascular-relevant genotypes
"""

import pandas as pd
import re
from io import StringIO


class VCFParser:
    """
    Parse VCF files and extract genotypes for cardiovascular genes
    """
    
    def __init__(self, gene_database_path='cardiovascular_genes.csv'):
        """
        Initialize parser with gene database
        
        Args:
            gene_database_path (str): Path to cardiovascular genes CSV
        """
        self.gene_db = pd.read_csv(gene_database_path)
        self.target_rsids = set(self.gene_db['rsid'].values)
        print(f"✅ Loaded {len(self.target_rsids)} cardiovascular SNPs to look for")
    
    
    def parse_vcf_file(self, vcf_file_content):
        """
        Parse VCF file and extract genotypes
        
        Args:
            vcf_file_content: File content (string or bytes)
            
        Returns:
            dict: Extracted genotypes {rsid: genotype}
                  e.g., {'rs429358': 'CC', 'rs7412': 'CT'}
        """
        # Convert bytes to string if needed
        if isinstance(vcf_file_content, bytes):
            vcf_content = vcf_file_content.decode('utf-8')
        else:
            vcf_content = vcf_file_content
        
        genotypes = {}
        lines = vcf_content.split('\n')
        
        # Find header line (starts with #CHROM)
        header_idx = None
        for i, line in enumerate(lines):
            if line.startswith('#CHROM'):
                header_idx = i
                break
        
        if header_idx is None:
            raise ValueError("Invalid VCF file: No header line found (#CHROM)")
        
        # Parse header to find column positions
        header = lines[header_idx].strip().split('\t')
        
        # VCF columns: CHROM, POS, ID, REF, ALT, QUAL, FILTER, INFO, FORMAT, [SAMPLE]
        try:
            chrom_idx = header.index('#CHROM')
            pos_idx = header.index('POS')
            id_idx = header.index('ID')
            ref_idx = header.index('REF')
            alt_idx = header.index('ALT')
            format_idx = header.index('FORMAT') if 'FORMAT' in header else None
            
            # Sample column (usually last column after FORMAT)
            sample_idx = len(header) - 1 if format_idx else None
            
        except ValueError as e:
            raise ValueError(f"Invalid VCF format: Missing required columns - {e}")
        
        # Parse variant lines
        for line in lines[header_idx + 1:]:
            if not line or line.startswith('#'):
                continue
            
            parts = line.strip().split('\t')
            
            if len(parts) < 5:
                continue  # Skip malformed lines
            
            # Extract variant info
            rsid = parts[id_idx] if len(parts) > id_idx else '.'
            
            # Skip if not an rsID or not in our target list
            if not rsid.startswith('rs') or rsid not in self.target_rsids:
                continue
            
            ref_allele = parts[ref_idx]
            alt_allele = parts[alt_idx]
            
            # Extract genotype from sample column
            if format_idx and sample_idx and len(parts) > sample_idx:
                format_field = parts[format_idx]
                sample_field = parts[sample_idx]
                
                genotype = self._extract_genotype(
                    format_field, 
                    sample_field, 
                    ref_allele, 
                    alt_allele
                )
                
                if genotype:
                    genotypes[rsid] = genotype
            else:
                # Simple VCF without genotype - assume homozygous for ALT
                genotypes[rsid] = alt_allele + alt_allele
        
        print(f"✅ Found {len(genotypes)} cardiovascular variants in VCF file")
        return genotypes
    
    
    def _extract_genotype(self, format_field, sample_field, ref_allele, alt_allele):
        """
        Extract genotype from FORMAT and sample fields
        
        Args:
            format_field (str): FORMAT column (e.g., "GT:DP:GQ")
            sample_field (str): Sample column (e.g., "0/1:30:99")
            ref_allele (str): Reference allele
            alt_allele (str): Alternate allele
        
        Returns:
            str: Genotype (e.g., "CT") or None
        """
        # Split format and sample
        format_parts = format_field.split(':')
        sample_parts = sample_field.split(':')
        
        # Find GT (genotype) field
        try:
            gt_idx = format_parts.index('GT')
            gt_value = sample_parts[gt_idx]
        except (ValueError, IndexError):
            return None
        
        # Parse genotype
        # GT can be: 0/0, 0/1, 1/1, 0|1, etc.
        # 0 = reference, 1 = first alt, 2 = second alt
        
        # Handle different separators (/ or |)
        if '/' in gt_value:
            alleles = gt_value.split('/')
        elif '|' in gt_value:
            alleles = gt_value.split('|')
        else:
            return None
        
        # Convert to actual alleles
        allele_map = {
            '0': ref_allele,
            '1': alt_allele.split(',')[0] if ',' in alt_allele else alt_allele,
            '.': 'N'  # Missing data
        }
        
        try:
            allele1 = allele_map.get(alleles[0], 'N')
            allele2 = allele_map.get(alleles[1], 'N')
            
            # Skip if missing data
            if allele1 == 'N' or allele2 == 'N':
                return None
            
            return allele1 + allele2
        
        except (IndexError, KeyError):
            return None
    
    
    def get_missing_snps(self, found_genotypes):
        """
        Identify which cardiovascular SNPs were not found in VCF
        
        Args:
            found_genotypes (dict): Genotypes found in VCF
        
        Returns:
            list: List of missing rsIDs
        """
        found_rsids = set(found_genotypes.keys())
        missing_rsids = self.target_rsids - found_rsids
        return list(missing_rsids)
    
    
    def validate_vcf_format(self, vcf_content):
        """
        Check if file is valid VCF format
        
        Args:
            vcf_content (str): VCF file content
        
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if isinstance(vcf_content, bytes):
            vcf_content = vcf_content.decode('utf-8')
        
        lines = vcf_content.split('\n')
        
        # Check for VCF header
        if not any(line.startswith('##fileformat=VCF') for line in lines[:10]):
            return False, "Not a valid VCF file: Missing ##fileformat=VCF header"
        
        # Check for column header
        if not any(line.startswith('#CHROM') for line in lines):
            return False, "Not a valid VCF file: Missing #CHROM header line"
        
        # Check for at least one variant
        variant_lines = [l for l in lines if l and not l.startswith('#')]
        if len(variant_lines) == 0:
            return False, "VCF file contains no variants"
        
        return True, None
    
    
    def generate_summary_report(self, genotypes, gene_db_path='cardiovascular_genes.csv'):
        """
        Generate summary of found variants
        
        Args:
            genotypes (dict): Found genotypes
            gene_db_path (str): Path to gene database
        
        Returns:
            dict: Summary statistics
        """
        gene_db = pd.read_csv(gene_db_path)
        
        summary = {
            'total_variants_found': len(genotypes),
            'total_cardiovascular_snps': len(self.target_rsids),
            'coverage_percent': (len(genotypes) / len(self.target_rsids) * 100) if len(self.target_rsids) > 0 else 0,
            'genes_covered': set(),
            'pharmacogenomic_variants': [],
            'high_risk_variants': [],
            'protective_variants': []
        }
        
        for rsid, genotype in genotypes.items():
            variant_info = gene_db[gene_db['rsid'] == rsid]
            
            if len(variant_info) == 0:
                continue
            
            variant_info = variant_info.iloc[0]
            
            # Track gene
            summary['genes_covered'].add(variant_info['gene_name'])
            
            # Track pharmacogenomic
            if pd.notna(variant_info['drug_interaction']):
                summary['pharmacogenomic_variants'].append({
                    'rsid': rsid,
                    'gene': variant_info['gene_name'],
                    'drug': variant_info['drug_interaction']
                })
            
            # Track risk variants
            risk_allele = variant_info['risk_allele']
            if genotype.count(risk_allele) >= 1:
                summary['high_risk_variants'].append({
                    'rsid': rsid,
                    'gene': variant_info['gene_name'],
                    'genotype': genotype,
                    'effect': variant_info['effect_size']
                })
            
            # Track protective variants
            protective_allele = variant_info['protective_allele']
            effect_size = variant_info['effect_size']
            if pd.notna(protective_allele) and genotype.count(protective_allele) == 2 and effect_size < 1.0:
                summary['protective_variants'].append({
                    'rsid': rsid,
                    'gene': variant_info['gene_name'],
                    'genotype': genotype
                })
        
        summary['genes_covered'] = list(summary['genes_covered'])
        
        return summary


def create_sample_vcf(rsids_and_genotypes):
    """
    Create a sample VCF file for testing
    
    Args:
        rsids_and_genotypes (dict): {rsid: genotype} e.g., {'rs429358': 'CC'}
    
    Returns:
        str: VCF file content
    """
    vcf_content = """##fileformat=VCFv4.2
##reference=GRCh38
##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE
"""
    
    # Map rsIDs to chromosome positions (simplified)
    gene_db = pd.read_csv('cardiovascular_genes.csv')
    
    for rsid, genotype in rsids_and_genotypes.items():
        variant = gene_db[gene_db['rsid'] == rsid]
        
        if len(variant) == 0:
            continue
        
        variant = variant.iloc[0]
        chrom = variant['chromosome']
        pos = variant['position']
        ref = variant['protective_allele'] if pd.notna(variant['protective_allele']) else 'A'
        alt = variant['risk_allele']
        
        # Convert genotype to GT format
        if genotype == ref + ref:
            gt = '0/0'
        elif genotype == alt + alt:
            gt = '1/1'
        else:
            gt = '0/1'
        
        vcf_content += f"{chrom}\t{pos}\t{rsid}\t{ref}\t{alt}\t100\tPASS\t.\tGT\t{gt}\n"
    
    return vcf_content


# Example usage
if __name__ == "__main__":
    # Initialize parser
    parser = VCFParser('cardiovascular_genes.csv')
    
    # Create sample VCF for testing
    sample_genotypes = {
        'rs429358': 'CC',  # APOE e4/e4 - high risk
        'rs7412': 'CC',    # APOE e3/e3
        'rs10455872': 'GA', # LPA - heterozygous risk
        'rs4244285': 'AA',  # CYP2C19*2 - poor metabolizer
        'rs1799853': 'TT',  # CYP2C9*2 - warfarin sensitivity
    }
    
    sample_vcf = create_sample_vcf(sample_genotypes)
    
    print("Testing VCF Parser...")
    print("=" * 60)
    
    # Validate format
    is_valid, error = parser.validate_vcf_format(sample_vcf)
    print(f"VCF Valid: {is_valid}")
    if error:
        print(f"Error: {error}")
    
    # Parse VCF
    genotypes = parser.parse_vcf_file(sample_vcf)
    print(f"\nFound genotypes: {genotypes}")
    
    # Get missing SNPs
    missing = parser.get_missing_snps(genotypes)
    print(f"\nMissing SNPs: {len(missing)} out of {len(parser.target_rsids)}")
    
    # Generate summary
    summary = parser.generate_summary_report(genotypes)
    print(f"\nSummary:")
    print(f"  Coverage: {summary['coverage_percent']:.1f}%")
    print(f"  Genes covered: {len(summary['genes_covered'])}")
    print(f"  Pharmacogenomic variants: {len(summary['pharmacogenomic_variants'])}")
    print(f"  High risk variants: {len(summary['high_risk_variants'])}")
    print(f"  Protective variants: {len(summary['protective_variants'])}")