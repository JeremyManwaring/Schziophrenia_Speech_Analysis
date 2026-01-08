"""
Welch's ANOVA Test

Welch's ANOVA is an alternative to the standard one-way ANOVA that does not
assume equal variances (homogeneity of variances). This makes it robust when
the assumption of equal variances is violated.

This script performs:
- Welch's ANOVA to test for differences in means across groups
- Games-Howell post-hoc tests (if ANOVA is significant)
- Descriptive statistics by group
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


def welch_anova(groups):
    """
    Perform Welch's ANOVA test.
    
    Welch's ANOVA tests the null hypothesis that all group means are equal,
    without assuming equal variances.
    
    Parameters
    ----------
    groups : list of arrays
        List of arrays, one for each group
    
    Returns
    -------
    statistic : float
        F-statistic from Welch's ANOVA
    p_value : float
        p-value of the test
    df_between : float
        Degrees of freedom between groups
    df_within : float
        Degrees of freedom within groups
    """
    # Filter out empty groups
    groups = [g[~np.isnan(g)] for g in groups if len(g[~np.isnan(g)]) > 0]
    
    if len(groups) < 2:
        return None, None, None, None, "Need at least 2 groups"
    
    # Calculate group statistics
    means = np.array([np.mean(g) for g in groups])
    vars_ = np.array([np.var(g, ddof=1) for g in groups])  # Sample variance
    ns = np.array([len(g) for g in groups])
    
    # Check for zero variance (all values are the same in a group)
    if np.any(vars_ == 0):
        return None, None, None, None, "Cannot perform Welch ANOVA: one or more groups have zero variance (all values identical)"
    
    # Calculate weights
    weights = ns / vars_
    
    # Calculate weighted mean
    x_bar_w = np.sum(weights * means) / np.sum(weights)
    
    # Calculate numerator (between-group variance)
    numerator = np.sum(weights * (means - x_bar_w)**2)
    
    # Calculate denominator components
    lambda_term = np.sum(((1 - weights / np.sum(weights))**2) / (ns - 1))
    denominator = 1 + (2 * (len(groups) - 2) * lambda_term / (len(groups)**2 - 1))
    
    # Welch's F-statistic
    F_welch = numerator / denominator
    
    # Degrees of freedom
    df_between = len(groups) - 1
    df_within = (len(groups)**2 - 1) / (3 * lambda_term)
    
    # p-value
    p_value = 1 - stats.f.cdf(F_welch, df_between, df_within)
    
    return F_welch, p_value, df_between, df_within, None


def games_howell_posthoc(groups, group_names):
    """
    Perform Games-Howell post-hoc test for pairwise comparisons.
    
    Games-Howell is appropriate when variances are unequal and sample sizes
    may differ. It's a pairwise t-test with adjusted degrees of freedom.
    
    Parameters
    ----------
    groups : list of arrays
        List of arrays, one for each group
    group_names : list of str
        Names of the groups
    
    Returns
    -------
    results : list of dict
        List of dictionaries with pairwise comparison results
    """
    results = []
    n_groups = len(groups)
    
    for i in range(n_groups):
        for j in range(i + 1, n_groups):
            group_i = groups[i][~np.isnan(groups[i])]
            group_j = groups[j][~np.isnan(groups[j])]
            
            if len(group_i) < 2 or len(group_j) < 2:
                continue
            
            mean_i = np.mean(group_i)
            mean_j = np.mean(group_j)
            var_i = np.var(group_i, ddof=1)
            var_j = np.var(group_j, ddof=1)
            n_i = len(group_i)
            n_j = len(group_j)
            
            # Standard error
            se = np.sqrt(var_i / n_i + var_j / n_j)
            
            # t-statistic
            t_stat = (mean_i - mean_j) / se
            
            # Degrees of freedom (Welch-Satterthwaite equation)
            df = (var_i / n_i + var_j / n_j)**2 / (
                (var_i / n_i)**2 / (n_i - 1) + (var_j / n_j)**2 / (n_j - 1)
            )
            
            # p-value (two-tailed)
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
            
            # Effect size (Cohen's d)
            pooled_std = np.sqrt((var_i + var_j) / 2)
            cohens_d = (mean_i - mean_j) / pooled_std if pooled_std > 0 else 0
            
            results.append({
                'group1': group_names[i],
                'group2': group_names[j],
                'mean1': mean_i,
                'mean2': mean_j,
                'mean_diff': mean_i - mean_j,
                't_stat': t_stat,
                'df': df,
                'p_value': p_value,
                'cohens_d': cohens_d
            })
    
    return results


def descriptive_stats(df, variable, group_col='group'):
    """
    Calculate descriptive statistics by group.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data
    variable : str
        Name of the variable
    group_col : str
        Name of the grouping variable
    
    Returns
    -------
    stats_df : pd.DataFrame
        DataFrame with descriptive statistics by group
    """
    stats_list = []
    
    for group in sorted(df[group_col].unique()):
        data = df[df[group_col] == group][variable].dropna()
        
        if len(data) > 0:
            stats_list.append({
                'Group': group,
                'N': len(data),
                'Mean': np.mean(data),
                'SD': np.std(data, ddof=1),
                'SE': stats.sem(data),
                'Median': np.median(data),
                'Min': np.min(data),
                'Max': np.max(data),
                '95% CI Lower': np.mean(data) - 1.96 * stats.sem(data),
                '95% CI Upper': np.mean(data) + 1.96 * stats.sem(data)
            })
    
    return pd.DataFrame(stats_list)


def print_anova_results(variable, F_stat, p_value, df_between, df_within, error_msg):
    """Print Welch ANOVA results in a formatted way."""
    print(f"\n{'='*70}")
    print(f"WELCH'S ANOVA: {variable.upper()}")
    print(f"{'='*70}")
    
    if error_msg:
        print(f"Error: {error_msg}")
        print(f"{'='*70}")
        return
    
    print(f"\nH0: All group means are equal")
    print(f"H1: At least one group mean differs")
    print(f"\nF-statistic: {F_stat:.4f}")
    print(f"Degrees of freedom (between): {df_between:.2f}")
    print(f"Degrees of freedom (within): {df_within:.2f}")
    print(f"p-value: {p_value:.6f}")
    
    alpha = 0.05
    if p_value < alpha:
        print(f"\nResult: p < {alpha} → REJECT H0")
        print("Interpretation: Significant difference between at least one pair of groups")
    else:
        print(f"\nResult: p >= {alpha} → FAIL TO REJECT H0")
        print("Interpretation: No significant difference between group means")
    
    print(f"{'='*70}")


def print_posthoc_results(posthoc_results):
    """Print post-hoc test results in a formatted table."""
    if not posthoc_results:
        return
    
    print(f"\n{'='*70}")
    print("GAMES-HOWELL POST-HOC TESTS")
    print(f"{'='*70}")
    cohens_d_label = "Cohen's d"
    print(f"\n{'Comparison':<20} {'Mean Diff':>12} {'t-stat':>10} {'df':>8} {'p-value':>12} {cohens_d_label:>12}")
    print("-" * 70)
    
    # Sort by p-value
    sorted_results = sorted(posthoc_results, key=lambda x: x['p_value'])
    
    for result in sorted_results:
        comparison = f"{result['group1']} vs {result['group2']}"
        mean_diff = result['mean_diff']
        t_stat = result['t_stat']
        df = result['df']
        p_val = result['p_value']
        cohens_d = result['cohens_d']
        
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
        
        print(f"{comparison:<20} {mean_diff:>12.2f} {t_stat:>10.3f} {df:>8.2f} {p_val:>12.6f} {cohens_d:>12.3f} {sig}")
    
    print("\nSignificance: *** p < 0.001, ** p < 0.01, * p < 0.05")
    print(f"{'='*70}")


def main():
    """Main function to run Welch's ANOVA tests."""
    # Set dataset root
    dataset_root = Path(__file__).parent.parent
    
    print("\n" + "="*70)
    print("WELCH'S ANOVA TEST")
    print("="*70)
    print(f"\nDataset: {dataset_root.name}")
    print("\nWelch's ANOVA tests for differences in means across groups")
    print("without assuming equal variances (robust to heteroscedasticity)")
    
    # Load data
    print("\nLoading participants data...")
    df = load_participants_data(dataset_root)
    
    print(f"Total participants: {len(df)}")
    print(f"Groups: {dict(df['group'].value_counts())}")
    
    # Variables to test
    continuous_vars = ['age', 'iq', 'psyrats']
    
    all_results = {}
    
    for var in continuous_vars:
        if var not in df.columns:
            continue
        
        n_valid = df[var].notna().sum()
        if n_valid < 6:
            print(f"\nSkipping {var}: insufficient data (N = {n_valid})")
            continue
        
        print(f"\n\n{'='*70}")
        print(f"ANALYZING: {var.upper()}")
        print(f"{'='*70}")
        
        # Get groups
        groups_dict = {}
        group_data = []
        group_names = []
        
        for group in sorted(df['group'].unique()):
            data = df[df['group'] == group][var].dropna().values
            if len(data) > 0:
                groups_dict[group] = data
                group_data.append(data)
                group_names.append(group)
        
        # Descriptive statistics
        print("\nDescriptive Statistics:")
        print("-" * 70)
        desc_stats = descriptive_stats(df, var, group_col='group')
        print(desc_stats.to_string(index=False))
        
        # Welch's ANOVA
        F_stat, p_value, df_between, df_within, error_msg = welch_anova(group_data)
        print_anova_results(var, F_stat, p_value, df_between, df_within, error_msg)
        
        # Store results
        all_results[var] = {
            'F_stat': F_stat,
            'p_value': p_value,
            'df_between': df_between,
            'df_within': df_within,
            'error': error_msg,
            'descriptive': desc_stats
        }
        
        # Post-hoc tests if ANOVA is significant
        if p_value is not None and p_value < 0.05:
            print("\nPerforming post-hoc Games-Howell tests...")
            posthoc_results = games_howell_posthoc(group_data, group_names)
            all_results[var]['posthoc'] = posthoc_results
            print_posthoc_results(posthoc_results)
    
    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    print("\nWelch's ANOVA Results:")
    print("-" * 70)
    print(f"{'Variable':<12} {'F-statistic':>12} {'df (bet/with)':>20} {'p-value':>12} {'Significant':>12}")
    print("-" * 70)
    
    for var, result in all_results.items():
        if result['error']:
            error_msg = result['error'][:40] + "..." if len(result['error']) > 40 else result['error']
            print(f"{var:<12} {'Error: ' + error_msg}")
            continue
        
        F_stat = result['F_stat']
        p_val = result['p_value']
        df_bet = result['df_between']
        df_with = result['df_within']
        sig = "Yes" if p_val < 0.05 else "No"
        
        df_str = f"{df_bet:.1f}/{df_with:.1f}"
        print(f"{var:<12} {F_stat:>12.4f} {df_str:>20} {p_val:>12.6f} {sig:>12}")
    
    print("\n" + "="*70)
    print("Note: Welch's ANOVA is robust to violations of equal variance assumption")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

