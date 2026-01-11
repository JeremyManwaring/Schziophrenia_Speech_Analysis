"""
Example analysis script for ds004302 dataset.

This script demonstrates basic BIDS dataset exploration and data loading.
"""

import os
from pathlib import Path
import pandas as pd
import nibabel as nib
from bids import BIDSLayout


def load_bids_dataset(bids_root):
    """
    Load BIDS dataset layout.
    
    Parameters
    ----------
    bids_root : str or Path
        Path to the BIDS dataset root directory
    
    Returns
    -------
    layout : BIDSLayout
        PyBIDS layout object
    """
    layout = BIDSLayout(bids_root, validate=False)
    return layout


def get_participants_info(dataset_root):
    """
    Load participants information from TSV file.
    
    Parameters
    ----------
    dataset_root : str or Path
        Path to the BIDS dataset root directory
    
    Returns
    -------
    participants_df : pd.DataFrame
        DataFrame with participants information
    """
    participants_path = Path(dataset_root) / "participants.tsv"
    if participants_path.exists():
        return pd.read_csv(participants_path, sep="\t")
    else:
        print(f"Participants file not found at {participants_path}")
        return None


def load_bold_image(layout, subject_id, task="speech"):
    """
    Load BOLD functional image for a given subject and task.
    
    Parameters
    ----------
    layout : BIDSLayout
        PyBIDS layout object
    subject_id : str
        Subject identifier (e.g., "01")
    task : str
        Task name (default: "speech")
    
    Returns
    -------
    img : nibabel.Nifti1Image
        Loaded NIfTI image
    """
    subject = f"sub-{subject_id}"
    bold_files = layout.get(
        subject=subject_id,
        task=task,
        suffix="bold",
        extension=".nii.gz",
        return_type="filename"
    )
    
    if bold_files:
        return nib.load(bold_files[0])
    else:
        print(f"No BOLD file found for {subject}, task-{task}")
        return None


def main():
    """Main function demonstrating basic dataset exploration."""
    # Set dataset root
    dataset_root = Path(__file__).parent.parent
    
    print(f"Dataset root: {dataset_root}")
    
    # Load BIDS layout
    print("\nLoading BIDS layout...")
    layout = load_bids_dataset(dataset_root)
    
    # Get list of subjects
    subjects = layout.get_subjects()
    print(f"\nFound {len(subjects)} subjects: {subjects[:5]}...")
    
    # Load participants info
    print("\nLoading participants information...")
    participants_df = get_participants_info(dataset_root)
    if participants_df is not None:
        print(f"\nParticipants dataframe shape: {participants_df.shape}")
        print(f"\nColumns: {list(participants_df.columns)}")
    
    # Example: Load a BOLD image
    if subjects:
        print(f"\nExample: Loading BOLD image for {subjects[0]}...")
        bold_img = load_bold_image(layout, subjects[0])
        if bold_img is not None:
            print(f"Image shape: {bold_img.shape}")
            print(f"Image affine:\n{bold_img.affine}")


if __name__ == "__main__":
    main()

