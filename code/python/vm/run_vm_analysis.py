#!/usr/bin/env python3
"""
Complete Analysis Pipeline for GCP VM

This script runs the full fMRI analysis pipeline on the GCP VM where
fMRIprep outputs are located at /data/output.
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import argparse

# Import VM config
from config import (
    FMRIPREP_DIR, ANALYSIS_ROOT, PARTICIPANTS_PATH, 
    EVENTS_PATH, TASK_JSON_PATH, RESULTS_DIR
)


def run_qc_analysis():
    """Run QC analysis."""
    print("\n" + "="*80)
    print("STEP 1: QUALITY CONTROL ANALYSIS")
    print("="*80)
    
    from qc_vm import generate_qc_summary, flag_motion_outliers, print_qc_report
    
    output_dir = RESULTS_DIR / 'qc'
    qc_df = generate_qc_summary(FMRIPREP_DIR, output_dir)
    
    if qc_df is not None:
        exclusions, reasons = flag_motion_outliers(qc_df)
        print_qc_report(qc_df, exclusions, reasons, output_dir)
        return qc_df, exclusions
    
    return None, []


def run_first_level():
    """Run first-level GLM."""
    print("\n" + "="*80)
    print("STEP 2: FIRST-LEVEL GLM ANALYSIS")
    print("="*80)
    
    from first_level_vm import run_all_subjects
    
    output_dir = RESULTS_DIR / 'first_level'
    
    results = run_all_subjects(
        fmriprep_dir=FMRIPREP_DIR,
        events_path=EVENTS_PATH,
        output_dir=output_dir,
        t_r=2.0,
        confound_strategy='standard',
        smoothing_fwhm=6.0
    )
    
    return results


def run_second_level():
    """Run second-level group analysis."""
    print("\n" + "="*80)
    print("STEP 3: SECOND-LEVEL GROUP ANALYSIS")
    print("="*80)
    
    from second_level_vm import run_all_contrasts
    
    first_level_dir = RESULTS_DIR / 'first_level'
    output_dir = RESULTS_DIR / 'second_level'
    
    results = run_all_contrasts(
        first_level_dir=first_level_dir,
        participants_path=PARTICIPANTS_PATH,
        output_dir=output_dir
    )
    
    return results


def run_roi_analysis():
    """Run ROI-based analysis."""
    print("\n" + "="*80)
    print("STEP 4: ROI-BASED ANALYSIS")
    print("="*80)
    
    from roi_vm import run_full_roi_analysis
    
    first_level_dir = RESULTS_DIR / 'first_level'
    output_dir = RESULTS_DIR / 'roi_analysis'
    
    results = run_full_roi_analysis(
        first_level_dir=first_level_dir,
        participants_path=PARTICIPANTS_PATH,
        output_dir=output_dir
    )
    
    return results


def run_correlation_analysis():
    """Run correlation analysis."""
    print("\n" + "="*80)
    print("STEP 5: CORRELATION ANALYSIS (PSYRATS)")
    print("="*80)
    
    from correlation_vm import run_correlation_analysis as corr_analysis
    
    roi_dir = RESULTS_DIR / 'roi_analysis'
    output_dir = RESULTS_DIR / 'correlations'
    
    results = corr_analysis(
        roi_dir=roi_dir,
        participants_path=PARTICIPANTS_PATH,
        output_dir=output_dir
    )
    
    return results


def run_effect_sizes():
    """Run effect size analysis."""
    print("\n" + "="*80)
    print("STEP 6: EFFECT SIZE ANALYSIS")
    print("="*80)
    
    from effect_size_vm import run_effect_size_analysis
    
    roi_dir = RESULTS_DIR / 'roi_analysis'
    output_dir = RESULTS_DIR / 'effect_sizes'
    
    results = run_effect_size_analysis(
        roi_dir=roi_dir,
        output_dir=output_dir
    )
    
    return results


def generate_summary_report():
    """Generate summary report."""
    print("\n" + "="*80)
    print("STEP 7: GENERATING SUMMARY REPORT")
    print("="*80)
    
    import pandas as pd
    
    report = []
    report.append("=" * 80)
    report.append("COMPLETE ANALYSIS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    
    # QC Summary
    report.append("\n\n## QUALITY CONTROL SUMMARY\n")
    qc_file = RESULTS_DIR / 'qc' / 'qc_summary.csv'
    if qc_file.exists():
        qc_df = pd.read_csv(qc_file)
        report.append(f"Subjects processed: {len(qc_df)}")
        if 'mean_fd' in qc_df.columns:
            report.append(f"Mean framewise displacement: {qc_df['mean_fd'].mean():.3f} mm")
    
    # First-level Summary
    report.append("\n\n## FIRST-LEVEL GLM SUMMARY\n")
    first_level_log = RESULTS_DIR / 'first_level' / 'first_level_processing.json'
    if first_level_log.exists():
        with open(first_level_log) as f:
            log = json.load(f)
        report.append(f"Subjects processed: {log['n_successful']}/{log['n_subjects']}")
        report.append(f"Contrasts computed: {len(log['contrasts'])}")
    
    # ROI Analysis Summary
    report.append("\n\n## ROI-BASED ANALYSIS SUMMARY\n")
    roi_summary = RESULTS_DIR / 'roi_analysis' / 'roi_analysis_summary.json'
    if roi_summary.exists():
        with open(roi_summary) as f:
            summary = json.load(f)
        report.append(f"ROIs analyzed: {summary['n_rois']}")
        report.append(f"Contrasts: {summary['n_contrasts']}")
    
    # Effect Size Summary
    report.append("\n\n## EFFECT SIZE SUMMARY\n")
    effect_file = RESULTS_DIR / 'effect_sizes' / 'effect_sizes_summary.csv'
    if effect_file.exists():
        effect_df = pd.read_csv(effect_file)
        large = effect_df[effect_df['interpretation'] == 'large']
        report.append(f"Large effects (|d| >= 0.8): {len(large)}")
    
    report.append("\n\n" + "=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    report_text = "\n".join(report)
    
    output_path = RESULTS_DIR / 'analysis_report.txt'
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\nReport saved to: {output_path}")


def main():
    """Main function to run complete analysis pipeline."""
    parser = argparse.ArgumentParser(description='Run fMRI analysis on GCP VM')
    parser.add_argument('--skip-qc', action='store_true', help='Skip QC analysis')
    parser.add_argument('--skip-first-level', action='store_true', help='Skip first-level GLM')
    parser.add_argument('--skip-second-level', action='store_true', help='Skip second-level')
    parser.add_argument('--skip-roi', action='store_true', help='Skip ROI analysis')
    parser.add_argument('--skip-correlations', action='store_true', help='Skip correlations')
    parser.add_argument('--skip-effect-sizes', action='store_true', help='Skip effect sizes')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("COMPLETE fMRI ANALYSIS PIPELINE (VM)")
    print("="*80)
    print(f"\nfMRIprep data: {FMRIPREP_DIR}")
    print(f"Results directory: {RESULTS_DIR}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
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
        
        generate_summary_report()
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Results saved to: {RESULTS_DIR}")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n\nERROR: Analysis failed with error:\n{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
