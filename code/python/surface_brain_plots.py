"""
Surface brain plots using fsaverage (FreeSurfer) template.

Uses plot_img_on_surf to project volume statistical maps onto the cortical
surface for accurate visualization that stays within the brain.
"""

from pathlib import Path
from nilearn.plotting import plot_img_on_surf
import warnings

warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).parent.parent.parent
CLUSTER_DIR = BASE_DIR / 'results' / 'visualizations' / '01_cluster_corrected'
MVPA_DIR = BASE_DIR / 'results' / 'visualizations' / '03_mvpa_classification'
OUTPUT_DIR = BASE_DIR / 'results' / 'visualizations' / 'brain_maps_surface'


def _format_title(name):
    """Convert contrast name to publication-style title (underscores to spaces, title case)."""
    return name.replace('_', ' ').title()


def create_cluster_surface_plots():
    """Generate surface plots for cluster-corrected contrast maps."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    contrasts = ['sentences_vs_reversed', 'speech_vs_reversed', 'words_vs_sentences']

    for contrast_name in contrasts:
        z_path = CLUSTER_DIR / contrast_name / f'{contrast_name}_AVH-_vs_AVH+_zstat_uncorrected.nii.gz'
        if not z_path.exists():
            continue
        try:
            out_path = OUTPUT_DIR / f'{contrast_name}_surface.png'
            title = f"{_format_title(contrast_name)}: AVH- vs AVH+ (z-stat)"
            plot_img_on_surf(
                stat_map=str(z_path),
                surf_mesh='fsaverage5',
                threshold=2.3,
                cmap='cold_hot',
                views=['lateral', 'medial'],
                hemispheres=['left', 'right'],
                colorbar=True,
                symmetric_cbar=True,
                title=title,
                output_file=str(out_path),
            )
            print(f"  Saved {out_path}")
        except Exception as e:
            print(f"  Failed {contrast_name}: {e}")


def create_mvpa_surface_plots():
    """Generate surface plots for SVM weight maps."""
    contrasts = ['sentences_vs_reversed', 'speech_vs_reversed', 'words_vs_sentences', 'words_vs_reversed']

    for contrast_name in contrasts:
        w_path = MVPA_DIR / f'{contrast_name}_svm_weights.nii.gz'
        if not w_path.exists():
            continue
        try:
            out_path = OUTPUT_DIR / f'{contrast_name}_svm_weights_surface.png'
            title = f"{_format_title(contrast_name)}: SVM Weights (AVH- vs AVH+)"
            plot_img_on_surf(
                stat_map=str(w_path),
                surf_mesh='fsaverage5',
                threshold=None,
                cmap='cold_hot',
                views=['lateral', 'medial'],
                hemispheres=['left', 'right'],
                colorbar=True,
                symmetric_cbar=True,
                title=title,
                output_file=str(out_path),
            )
            print(f"  Saved {out_path}")
        except Exception as e:
            print(f"  Failed {contrast_name}: {e}")


def main():
    """Generate all surface brain plots."""
    print("\n" + "="*70)
    print("SURFACE BRAIN PLOTS (fsaverage5)")
    print("="*70)

    print("\nCluster-corrected maps...")
    create_cluster_surface_plots()

    print("\nMVPA SVM weight maps...")
    create_mvpa_surface_plots()

    print(f"\nSurface plots saved to: {OUTPUT_DIR}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
