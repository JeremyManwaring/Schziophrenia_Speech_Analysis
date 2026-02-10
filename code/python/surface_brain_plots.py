"""
Surface brain plots using fsaverage (FreeSurfer) template.

Projects volume-based statistical maps onto the cortical surface
for accurate visualization that stays within the brain.
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from nilearn import datasets
from nilearn import surface
from nilearn.plotting import plot_surf_stat_map
import warnings

warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).parent.parent.parent
CLUSTER_DIR = BASE_DIR / 'results' / 'visualizations' / '01_cluster_corrected'
MVPA_DIR = BASE_DIR / 'results' / 'visualizations' / '03_mvpa_classification'
OUTPUT_DIR = BASE_DIR / 'results' / 'visualizations' / 'brain_maps_surface'


def get_fsaverage_mesh():
    """Fetch fsaverage5 mesh (faster than full fsaverage)."""
    fsaverage = datasets.fetch_surf_fsaverage(mesh='fsaverage5')
    return fsaverage


def project_vol_to_surf(vol_img, mesh, radius=2.0, n_samples=10):
    """Project volume map to left and right surfaces."""
    texture_left = surface.vol_to_surf(
        vol_img,
        mesh.pial_left,
        radius=radius,
        n_samples=n_samples,
    )
    texture_right = surface.vol_to_surf(
        vol_img,
        mesh.pial_right,
        radius=radius,
        n_samples=n_samples,
    )
    return texture_left, texture_right


def plot_surface_map(
    texture_left,
    texture_right,
    mesh,
    output_path,
    title='',
    threshold=None,
    cmap='RdBu_r',
    symmetric_cbar=True,
):
    """Create 2x2 figure: left lateral/medial, right lateral/medial."""
    fig = plt.figure(figsize=(14, 10))
    
    views = ['lateral', 'medial']
    hemis = ['left', 'right']
    textures = [texture_left, texture_right]
    mesh_surfs = [mesh.pial_left, mesh.pial_right]
    
    for row, (hemi, texture, surf) in enumerate(zip(hemis, textures, mesh_surfs)):
        for col, view in enumerate(views):
            ax = fig.add_subplot(2, 2, row * 2 + col + 1)
            try:
                plot_surf_stat_map(
                    surf,
                    texture,
                    hemi=hemi,
                    view=view,
                    colorbar=(col == 1),
                    threshold=threshold if threshold is not None else 'auto',
                    cmap=cmap,
                    symmetric_cbar=symmetric_cbar,
                    bg_map=mesh.sulc_left if hemi == 'left' else mesh.sulc_right,
                    axes=ax,
                )
                ax.set_title(f'{hemi.capitalize()} {view}', fontsize=11)
            except Exception as e:
                ax.text(0.5, 0.5, f'Error: {e}', ha='center', va='center', transform=ax.transAxes)
    
    if title:
        fig.suptitle(title, fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def create_cluster_surface_plots():
    """Generate surface plots for cluster-corrected contrast maps."""
    mesh = get_fsaverage_mesh()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    contrasts = ['sentences_vs_reversed', 'speech_vs_reversed', 'words_vs_sentences']
    
    for contrast_name in contrasts:
        z_path = CLUSTER_DIR / contrast_name / f'{contrast_name}_AVH-_vs_AVH+_zstat_uncorrected.nii.gz'
        if not z_path.exists():
            continue
        try:
            texture_left, texture_right = project_vol_to_surf(str(z_path), mesh)
            out_path = OUTPUT_DIR / f'{contrast_name}_surface.png'
            plot_surface_map(
                texture_left,
                texture_right,
                mesh,
                out_path,
                title=f'{contrast_name}: AVH- vs AVH+ (z-stat)',
                threshold=2.3,
            )
            print(f"  Saved {out_path}")
        except Exception as e:
            print(f"  Failed {contrast_name}: {e}")


def create_mvpa_surface_plots():
    """Generate surface plots for SVM weight maps."""
    mesh = get_fsaverage_mesh()
    
    contrasts = ['sentences_vs_reversed', 'speech_vs_reversed', 'words_vs_sentences', 'words_vs_reversed']
    
    for contrast_name in contrasts:
        w_path = MVPA_DIR / f'{contrast_name}_svm_weights.nii.gz'
        if not w_path.exists():
            continue
        try:
            texture_left, texture_right = project_vol_to_surf(str(w_path), mesh)
            out_path = OUTPUT_DIR / f'{contrast_name}_svm_weights_surface.png'
            plot_surface_map(
                texture_left,
                texture_right,
                mesh,
                out_path,
                title=f'{contrast_name}: SVM weights (AVH- vs AVH+)',
                threshold=None,
                symmetric_cbar=True,
            )
            print(f"  Saved {out_path}")
        except Exception as e:
            print(f"  Failed {contrast_name}: {e}")


def main():
    """Generate all surface brain plots."""
    print("\n" + "="*70)
    print("SURFACE BRAIN PLOTS (fsaverage5)")
    print("="*70)
    print("\nFetching fsaverage5 mesh...")
    
    print("\nCluster-corrected maps...")
    create_cluster_surface_plots()
    
    print("\nMVPA SVM weight maps...")
    create_mvpa_surface_plots()
    
    print(f"\nSurface plots saved to: {OUTPUT_DIR}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
