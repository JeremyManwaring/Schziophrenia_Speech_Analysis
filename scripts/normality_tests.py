"""
Statistical tests for normality and variance homogeneity.

This script performs:
- Levene's test for homogeneity of variances across groups
- Shapiro-Wilk test for normality
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import warnings

warnings.filterwarnings('ignore')


def load_participants_data(dataset_root):
    """
    Load participants data and clean it.
    
    Parameters
    ----------
    dataset_root : str or Path
        Path to the BIDS dataset root directory
    
    Returns
    -------
    df : pd.DataFrame
        Cleaned DataFrame with participants information
    """
    participants_path = Path(dataset_root) / "participants.tsv"
    df = pd.read_csv(participants_path, sep="\t")
    
    # Replace 'n/a' with NaN for numeric columns
    numeric_cols = ['age', 'iq', 'psyrats']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def levenes_test(df, variable, group_col='group'):
    """
    Perform Levene's test for homogeneity of variances.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data
    variable : str
        Name of the continuous variable to test
    group_col : str
        Name of the grouping variable (default: 'group')
    
    Returns
    -------
    statistic : float
        Levene's test statistic
    p_value : float
        p-value of the test
    """
    # Get groups
    groups = df[group_col].unique()
    group_data = []
    group_names = []
    
    for group in groups:
        data = df[df[group_col] == group][variable].dropna()
        if len(data) > 0:
            group_data.append(data)
            group_names.append(group)
    
    if len(group_data) < 2:
        return None, None, "Not enough groups to perform test"
    
    # Perform Levene's test
    statistic, p_value = stats.levene(*group_data)
    
    return statistic, p_value, group_names


def shapiro_wilk_test(df, variable, group_col=None):
    """
    Perform Shapiro-Wilk test for normality.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data
    variable : str
        Name of the continuous variable to test
    group_col : str or None
        If provided, test normality within each group
    
    Returns
    -------
    results : dict
        Dictionary with test results
    """
    results = {}
    
    if group_col is None:
        # Test overall normality
        data = df[variable].dropna()
        if len(data) < 3:
            results['overall'] = {'statistic': None, 'p_value': None, 'n': len(data), 'note': 'Insufficient data'}
        elif len(data) > 5000:
            # Sample if too large (Shapiro-Wilk is limited to 5000 samples)
            data = data.sample(n=5000, random_state=42)
            statistic, p_value = stats.shapiro(data)
            results['overall'] = {'statistic': statistic, 'p_value': p_value, 'n': len(data), 'note': 'Sampled to 5000'}
        else:
            statistic, p_value = stats.shapiro(data)
            results['overall'] = {'statistic': statistic, 'p_value': p_value, 'n': len(data)}
    else:
        # Test within each group
        groups = df[group_col].unique()
        for group in groups:
            data = df[df[group_col] == group][variable].dropna()
            if len(data) < 3:
                results[group] = {'statistic': None, 'p_value': None, 'n': len(data), 'note': 'Insufficient data'}
            elif len(data) > 5000:
                data = data.sample(n=5000, random_state=42)
                statistic, p_value = stats.shapiro(data)
                results[group] = {'statistic': statistic, 'p_value': p_value, 'n': len(data), 'note': 'Sampled to 5000'}
            else:
                statistic, p_value = stats.shapiro(data)
                results[group] = {'statistic': statistic, 'p_value': p_value, 'n': len(data)}
    
    return results


def print_levene_results(variable, statistic, p_value, group_names):
    """Print Levene's test results in a formatted way."""
    print(f"\n{'='*70}")
    print(f"LEVENE'S TEST: {variable.upper()}")
    print(f"{'='*70}")
    print(f"Groups tested: {', '.join(group_names)}")
    print(f"\nTest statistic (W): {statistic:.4f}")
    print(f"p-value: {p_value:.6f}")
    
    if p_value is not None:
        alpha = 0.05
        if p_value < alpha:
            print(f"\nResult: p < {alpha} → REJECT H0")
            print("Interpretation: Variances are NOT equal across groups")
            print("               (heterogeneity of variances)")
        else:
            print(f"\nResult: p >= {alpha} → FAIL TO REJECT H0")
            print("Interpretation: Variances are equal across groups")
            print("               (homogeneity of variances)")
    print(f"{'='*70}")


def print_shapiro_results(variable, results, group_col=None):
    """Print Shapiro-Wilk test results in a formatted way."""
    print(f"\n{'='*70}")
    print(f"SHAPIRO-WILK TEST: {variable.upper()}")
    print(f"{'='*70}")
    
    alpha = 0.05
    
    if group_col is None:
        # Overall results
        result = results.get('overall', {})
        n = result.get('n', 0)
        stat = result.get('statistic')
        p_val = result.get('p_value')
        note = result.get('note', '')
        
        print(f"\nOverall (N = {n})")
        if note:
            print(f"Note: {note}")
        if stat is not None:
            print(f"Test statistic (W): {stat:.4f}")
            print(f"p-value: {p_val:.6f}")
            if p_val < alpha:
                print(f"\nResult: p < {alpha} → REJECT H0")
                print("Interpretation: Data are NOT normally distributed")
            else:
                print(f"\nResult: p >= {alpha} → FAIL TO REJECT H0")
                print("Interpretation: Data are normally distributed")
        else:
            print("Cannot perform test: insufficient data")
    else:
        # Group-specific results
        for group, result in results.items():
            n = result.get('n', 0)
            stat = result.get('statistic')
            p_val = result.get('p_value')
            note = result.get('note', '')
            
            print(f"\n{group} (N = {n})")
            if note:
                print(f"Note: {note}")
            if stat is not None:
                print(f"  Test statistic (W): {stat:.4f}")
                print(f"  p-value: {p_val:.6f}")
                if p_val < alpha:
                    print(f"  Result: p < {alpha} → REJECT H0 (NOT normal)")
                else:
                    print(f"  Result: p >= {alpha} → FAIL TO REJECT H0 (normal)")
            else:
                print("  Cannot perform test: insufficient data")
    
    print(f"{'='*70}")


def main():
    """Main function to run all statistical tests."""
    # Set dataset root
    dataset_root = Path(__file__).parent.parent
    
    print("\n" + "="*70)
    print("STATISTICAL TESTS FOR NORMALITY AND VARIANCE HOMOGENEITY")
    print("="*70)
    print(f"\nDataset: {dataset_root.name}")
    
    # Load data
    print("\nLoading participants data...")
    df = load_participants_data(dataset_root)
    
    print(f"Total participants: {len(df)}")
    print(f"Groups: {df['group'].value_counts().to_dict()}")
    
    # Variables to test
    continuous_vars = ['age', 'iq', 'psyrats']
    
    # Perform Levene's test for each continuous variable
    print("\n" + "="*70)
    print("PART 1: LEVENE'S TEST (Homogeneity of Variances)")
    print("="*70)
    print("\nH0: Variances are equal across groups")
    print("H1: Variances are not equal across groups")
    
    levene_results = {}
    
    for var in continuous_vars:
        if var not in df.columns:
            continue
            
        # Check if variable has data
        n_valid = df[var].notna().sum()
        if n_valid < 6:  # Need at least 2 groups with some data
            print(f"\nSkipping {var}: insufficient data (N = {n_valid})")
            continue
        
        statistic, p_value, group_names = levenes_test(df, var, group_col='group')
        if statistic is not None:
            levene_results[var] = {
                'statistic': statistic,
                'p_value': p_value,
                'groups': group_names
            }
            print_levene_results(var, statistic, p_value, group_names)
        else:
            print(f"\nCannot perform Levene's test for {var}: {p_value}")
    
    # Perform Shapiro-Wilk test for each continuous variable
    print("\n" + "="*70)
    print("PART 2: SHAPIRO-WILK TEST (Normality)")
    print("="*70)
    print("\nH0: Data are normally distributed")
    print("H1: Data are not normally distributed")
    
    shapiro_results = {}
    
    for var in continuous_vars:
        if var not in df.columns:
            continue
        
        n_valid = df[var].notna().sum()
        if n_valid < 3:
            print(f"\nSkipping {var}: insufficient data (N = {n_valid})")
            continue
        
        # Test overall
        print(f"\n\nTesting {var}...")
        results = shapiro_wilk_test(df, var, group_col='group')
        shapiro_results[var] = results
        print_shapiro_results(var, results, group_col='group')
    
    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    print("\nLevene's Test Results (Homogeneity of Variances):")
    print("-" * 70)
    for var, result in levene_results.items():
        p_val = result['p_value']
        status = "Heterogeneous" if p_val < 0.05 else "Homogeneous"
        print(f"{var:12s}: p = {p_val:.6f} → {status}")
    
    print("\nShapiro-Wilk Test Results (Normality) - By Group:")
    print("-" * 70)
    for var, results in shapiro_results.items():
        print(f"\n{var}:")
        for group, result in results.items():
            p_val = result.get('p_value')
            n = result.get('n', 0)
            if p_val is not None:
                status = "Non-normal" if p_val < 0.05 else "Normal"
                print(f"  {group:8s}: p = {p_val:.6f} (N={n:2d}) → {status}")
    
    print("\n" + "="*70)
    print("Note: p < 0.05 indicates violation of assumption")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

