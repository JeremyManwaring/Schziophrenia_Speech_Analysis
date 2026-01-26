"""
Master Script: Run All Advanced AVH Analyses

Executes all advanced analyses for AVH- vs AVH+ comparison:
1. Cluster-corrected whole-brain analysis
2. Raincloud plot visualizations
3. MVPA classification
4. Connectivity analysis
5. Laterality analysis
"""

import sys
from pathlib import Path
import time

# Add the code directory to path
CODE_DIR = Path(__file__).parent
sys.path.insert(0, str(CODE_DIR))


def run_all_analyses():
    """Run all advanced analyses in sequence."""
    start_time = time.time()
    
    print("\n" + "="*80)
    print("ADVANCED AVH ANALYSIS SUITE")
    print("Comparing Schizophrenia Patients: AVH- vs AVH+")
    print("="*80)
    
    # 1. Cluster-corrected analysis
    print("\n" + "-"*80)
    print("STEP 1/5: Cluster-Corrected Whole-Brain Analysis")
    print("-"*80)
    try:
        from advanced_cluster_analysis import main as cluster_main
        cluster_main()
        print("✓ Cluster analysis complete")
    except Exception as e:
        print(f"✗ Cluster analysis failed: {e}")
    
    # 2. Raincloud plots
    print("\n" + "-"*80)
    print("STEP 2/5: Raincloud Plot Visualizations")
    print("-"*80)
    try:
        from raincloud_visualizations import main as raincloud_main
        raincloud_main()
        print("✓ Raincloud plots complete")
    except Exception as e:
        print(f"✗ Raincloud plots failed: {e}")
    
    # 3. MVPA Classification
    print("\n" + "-"*80)
    print("STEP 3/5: MVPA Classification")
    print("-"*80)
    try:
        from mvpa_classification import main as mvpa_main
        mvpa_main()
        print("✓ MVPA classification complete")
    except Exception as e:
        print(f"✗ MVPA classification failed: {e}")
    
    # 4. Connectivity analysis
    print("\n" + "-"*80)
    print("STEP 4/5: Functional Connectivity Analysis")
    print("-"*80)
    try:
        from connectivity_analysis import main as connectivity_main
        connectivity_main()
        print("✓ Connectivity analysis complete")
    except Exception as e:
        print(f"✗ Connectivity analysis failed: {e}")
    
    # 5. Laterality analysis
    print("\n" + "-"*80)
    print("STEP 5/5: Laterality Index Analysis")
    print("-"*80)
    try:
        from laterality_analysis import main as laterality_main
        laterality_main()
        print("✓ Laterality analysis complete")
    except Exception as e:
        print(f"✗ Laterality analysis failed: {e}")
    
    # Summary
    elapsed = time.time() - start_time
    
    print("\n" + "="*80)
    print("ALL ANALYSES COMPLETE")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print("="*80)
    
    # Print output locations
    BASE_DIR = Path(__file__).parent.parent.parent
    VIS_DIR = BASE_DIR / 'results' / 'visualizations'
    
    print("\nOutput Locations:")
    print(f"  01_cluster_corrected/  - Cluster-corrected brain maps")
    print(f"  02_raincloud_plots/    - ROI distribution visualizations")
    print(f"  03_mvpa_classification/- SVM classification results")
    print(f"  04_connectivity/       - Functional connectivity matrices")
    print(f"  05_laterality/         - Hemisphere dominance analysis")
    print(f"\nAll outputs in: {VIS_DIR}")


if __name__ == "__main__":
    run_all_analyses()
