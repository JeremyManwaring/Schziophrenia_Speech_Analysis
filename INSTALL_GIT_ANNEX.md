# Installing git-annex on macOS

## Quick Install (Recommended)

### Option 1: Install Homebrew + git-annex

**Step 1: Install Homebrew** (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the prompts and enter your password when asked.

**Step 2: Install git-annex**
```bash
brew install git-annex
```

### Option 2: Direct Binary Download

1. Visit: https://downloads.kitenet.net/git-annex/OSX/
2. Download the appropriate DMG for your macOS version
   - For macOS 15.6 (Sequoia): Try the latest universal binary
   - For Apple Silicon (M1/M2/M3): Download arm64 version
   - For Intel: Download x86_64 version
3. Open the DMG file
4. Copy `git-annex` to `/usr/local/bin/` (or another directory in your PATH)
5. Make it executable: `chmod +x /usr/local/bin/git-annex`

### Option 3: MacPorts (if you have MacPorts)
```bash
sudo port install git-annex
```

## Verify Installation

After installation, verify it works:
```bash
git-annex version
```

You should see output like:
```
git-annex version: 10.20231202
```

## After Installation

Once git-annex is installed, retrieve your files:

```bash
cd /Users/adrianecheverria/DATASET/ds004302

# Retrieve files for first 3 subjects
python3 -m datalad get sub-01/func/sub-01_task-speech_bold.nii.gz
python3 -m datalad get sub-01/anat/sub-01_T1w.nii.gz
python3 -m datalad get sub-02/func/sub-02_task-speech_bold.nii.gz
python3 -m datalad get sub-02/anat/sub-02_T1w.nii.gz
python3 -m datalad get sub-03/func/sub-03_task-speech_bold.nii.gz
python3 -m datalad get sub-03/anat/sub-03_T1w.nii.gz
```

Or use the provided script:
```bash
./retrieve_files.sh 01 02 03
```

## Troubleshooting

### "git-annex: command not found"
- Ensure the binary is in your PATH
- Try: `export PATH="/usr/local/bin:$PATH"`
- Or add to your `~/.zshrc`: `echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc`

### "Need git-annex version >= 10.20230126"
- Download a newer version from https://downloads.kitenet.net/git-annex/OSX/

### Permission denied
- Use `sudo` when copying to system directories
- Or install to a user-writable directory like `~/bin` and add to PATH

## Next Steps

After installing git-annex and retrieving files, you can run:
```bash
cd matlab
./start_matlab.sh
# Then in MATLAB:
run_complete_analysis({'01', '02', '03'}, false)
```

