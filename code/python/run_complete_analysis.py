#!/usr/bin/env python3
"""
Complete Analysis Pipeline

This script orchestrates the full analysis pipeline:
1. QC summary from fMRIprep outputs
2. First-level GLM analysis
3. Second-level group analysis
4. ROI-based analysis
5. Correlation analysis (PSYRATS)
6. Effect size calculations
7. Demographic statistics
8. Generate summary report
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import argparse

# Add code directory to path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))


def run_qc_analysis():
    """Run QC analysis."""
    print("\n" + "="*80)
    print("STEP 1: QUALITY CONTROL ANALYSIS")
    print("="*80)
    
    from qc_summary import main as qc_main
    return qc_main()


def run_first_level():
    """Run first-level GLM."""
    print("\n" + "="*80)
    print("STEP 2: FIRST-LEVEL GLM ANALYSIS")
    print("="*80)
    
    from first_level_glm import main as glm_main
    return glm_main()


def run_second_level():
    """Run second-level group analysis."""
    print("\n" + "="*80)
    print("STEP 3: SECOND-LEVEL GROUP ANALYSIS")
    print("="*80)
    
    from second_level_glm import main as second_level_main
    return second_level_main()


def run_roi_analysis():
    """Run ROI-based analysis."""
    print("\n" + "="*80)
    print("STEP 4: ROI-BASED ANALYSIS")
    print("="*80)
    
    from roi_analysis import main as roi_main
    return roi_main()


def run_correlation_analysis():
    """Run correlation analysis."""
    print("\n" + "="*80)
    print("STEP 5: CORRELATION ANALYSIS (PSYRATS)")
    print("="*80)
    
    from correlation_analysis import main as corr_main
    return corr_main()


def run_effect_sizes():
    """Run effect size analysis."""
    print("\n" + "="*80)
    print("STEP 6: EFFECT SIZE ANALYSIS")
    print("="*80)
    
    from effect_size_analysis import main as effect_main
    return effect_main()


def run_demographic_stats():
    """Run demographic statistics."""
    print("\n" + "="*80)
    print("STEP 7: DEMOGRAPHIC STATISTICS")
    print("="*80)
    
    from normality_tests import main as normality_main
    normality_main()
    
    from welch_anova import main as anova_main
    anova_main()


def generate_summary_report(results_dir, output_path):
    """
    Generate a summary report of all analyses.
    
    Parameters
    ----------
    results_dir : Path
        Directory with all results
    output_path : Path
        Path for output report
    """
    print("\n" + "="*80)
    print("STEP 8: GENERATING SUMMARY REPORT")
    print("="*80)
    
    results_dir = Path(results_dir)
    
    report = []
    report.append("=" * 80)
    report.append("COMPLETE ANALYSIS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    
    # QC Summary
    report.append("\n\n## QUALITY CONTROL SUMMARY\n")
    qc_file = results_dir / 'qc' / 'qc_summary.csv'
    if qc_file.exists():
        import pandas as pd
        qc_df = pd.read_csv(qc_file)
        report.append(f"Subjects processed: {len(qc_df)}")
        if 'mean_fd' in qc_df.columns:
            report.append(f"Mean framewise displacement: {qc_df['mean_fd'].mean():.3f} mm")
            report.append(f"Range: {qc_df['mean_fd'].min():.3f} - {qc_df['mean_fd'].max():.3f} mm")
        
        exclusion_file = results_dir / 'qc' / 'motion_exclusions.txt'
        if exclusion_file.exists():
            with open(exclusion_file) as f:
                content = f.read()
                if 'No subjects flagged' in content:
                    report.append("Motion exclusions: None")
                else:
                    report.append("See motion_exclusions.txt for potential exclusions")
    else:
        report.append("QC data not available")
    
    # First-level Summary
    report.append("\n\n## FIRST-LEVEL GLM SUMMARY\n")
    first_level_log = results_dir / 'first_level' / 'first_level_processing.json'
    if first_level_log.exists():
        with open(first_level_log) as f:
            log = json.load(f)
        report.append(f"Subjects processed: {log['n_successful']}/{log['n_subjects']}")
        report.append(f"Contrasts computed: {len(log['contrasts'])}")
        report.append(f"Smoothing FWHM: {log['smoothing_fwhm']} mm")
        if log['n_failed'] > 0:
            report.append(f"Failed subjects: {log['n_failed']}")
    else:
        report.append("First-level data not available")
    
    # Second-level Summary
    report.append("\n\n## SECOND-LEVEL GROUP ANALYSIS SUMMARY\n")
    second_level_summary = results_dir / 'second_level' / 'second_level_summary.json'
    if second_level_summary.exists():
        with open(second_level_summary) as f:
            summary = json.load(f)
        report.append(f"Contrasts analyzed: {len(summary)}")
        report.append("Groups compared: HC vs AVH- vs AVH+")
        report.append("Covariates: age, IQ, sex")
    else:
        report.append("Second-level data not available")
    
    # ROI Analysis Summary
    report.append("\n\n## ROI-BASED ANALYSIS SUMMARY\n")
    roi_summary = results_dir / 'roi_analysis' / 'roi_analysis_summary.json'
    if roi_summary.exists():
        with open(roi_summary) as f:
            summary = json.load(f)
        report.append(f"ROIs analyzed: {summary['n_rois']}")
        report.append(f"Contrasts: {summary['n_contrasts']}")
        
        # Check for significant results
        import pandas as pd
        for contrast in summary['contrasts']:
            anova_file = results_dir / 'roi_analysis' / f'{contrast}_roi_anova.csv'
            if anova_file.exists():
                anova_df = pd.read_csv(anova_file)
                if 'p_fdr' in anova_df.columns:
                    sig = anova_df[anova_df['p_fdr'] < 0.05]
                    if len(sig) > 0:
                        report.append(f"\n  {contrast}: {len(sig)} significant ROIs (FDR p<0.05)")
    else:
        report.append("ROI analysis data not available")
    
    # Correlation Summary
    report.append("\n\n## PSYRATS CORRELATION SUMMARY (AVH+ Group)\n")
    corr_summary = results_dir / 'correlations' / 'correlation_summary.json'
    if corr_summary.exists():
        with open(corr_summary) as f:
            summary = json.load(f)
        
        for contrast, data in summary.items():
            if 'error' not in data:
                correlations = data.get('correlations', [])
                sig_corrs = [c for c in correlations 
                            if c.get('pearson_p') is not None and c['pearson_p'] < 0.05]
                if len(sig_corrs) > 0:
                    report.append(f"\n  {contrast}: {len(sig_corrs)} significant correlations (p<0.05)")
                    for c in sig_corrs[:3]:  # Show top 3
                        report.append(f"    - {c['roi']}: r={c['pearson_r']:.3f}, p={c['pearson_p']:.4f}")
    else:
        report.append("Correlation data not available")
    
    # Effect Size Summary
    report.append("\n\n## EFFECT SIZE SUMMARY\n")
    effect_summary = results_dir / 'effect_sizes' / 'effect_sizes_summary.csv'
    if effect_summary.exists():
        import pandas as pd
        effect_df = pd.read_csv(effect_summary)
        
        # Count large effects
        large = effect_df[effect_df['interpretation'] == 'large']
        medium = effect_df[effect_df['interpretation'] == 'medium']
        
        report.append(f"Large effects (|d| >= 0.8): {len(large)}")
        report.append(f"Medium effects (0.5 <= |d| < 0.8): {len(medium)}")
        
        # Highlight largest effects
        if len(large) > 0:
            report.append("\nLargest effects (HC vs AVH+):")
            hc_avh_large = large[large['comparison'] == 'HC_vs_AVH+'].nlargest(5, 'cohens_d', key=abs)
            for _, row in hc_avh_large.iterrows():
                report.append(f"  - {row['contrast']}/{row['roi']}: d={row['cohens_d']:.2f}")
    else:
        report.append("Effect size data not available")
    
    # Write report
    report.append("\n\n" + "="*80)
    report.append("END OF REPORT")
    report.append("="*80)
    
    report_text = "\n".join(report)
    
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\nReport saved to: {output_path}")


def main():
    """Main function to run complete analysis pipeline."""
    parser = argparse.ArgumentParser(description='Run complete fMRI analysis pipeline')
    parser.add_argument('--skip-qc', action='store_true', help='Skip QC analysis')
    parser.add_argument('--skip-first-level', action='store_true', help='Skip first-level GLM')
    parser.add_argument('--skip-second-level', action='store_true', help='Skip second-level analysis')
    parser.add_argument('--skip-roi', action='store_true', help='Skip ROI analysis')
    parser.add_argument('--skip-correlations', action='store_true', help='Skip correlation analysis')
    parser.add_argument('--skip-effect-sizes', action='store_true', help='Skip effect size analysis')
    parser.add_argument('--skip-demographics', action='store_true', help='Skip demographic statistics')
    parser.add_argument('--report-only', action='store_true', help='Only generate summary report')
    
    args = parser.parse_args()
    
    dataset_root = Path(__file__).parent.parent.parent
    results_dir = dataset_root / 'results'
    
    print("\n" + "="*80)
    print("COMPLETE fMRI ANALYSIS PIPELINE")
    print("="*80)
    print(f"\nDataset: {dataset_root.name}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    if args.report_only:
        generate_summary_report(results_dir, results_dir / 'analysis_report.txt')
        return
    
    # Run analysis steps
    try:
        if not args.skip_qc:
            run_qc_analysis()
        
        if not args.skip_first_level:
            run_first_level()
        
        if not args.skip_second_level:
            run_second_level()
        
        if not args.skip_roi:
            run_roi_analysis()
        
        if not args.skip_correlations:
            run_correlation_analysis()
        
        if not args.skip_effect_sizes:
            run_effect_sizes()
        
        if not args.skip_demographics:
            run_demographic_stats()
        
        # Generate summary report
        generate_summary_report(results_dir, results_dir / 'analysis_report.txt')
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Results saved to: {results_dir}")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n\nERROR: Analysis failed with error:\n{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
