#!/bin/bash
# Interactive script to install git-annex on macOS

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          git-annex Installation for macOS               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if already installed
if command -v git-annex &> /dev/null; then
    echo "✓ git-annex is already installed!"
    git-annex version | head -1
    exit 0
fi

echo "git-annex is not installed."
echo ""
echo "Installation options:"
echo ""
echo "1. Install via Homebrew (Recommended - easiest)"
echo "2. Download binary manually"
echo "3. Exit and install manually"
echo ""
read -p "Choose option (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Installing Homebrew (if not installed)..."
        if ! command -v brew &> /dev/null; then
            echo "Homebrew not found. Installing..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            
            # Add Homebrew to PATH if needed
            if [ -f "/opt/homebrew/bin/brew" ]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            elif [ -f "/usr/local/bin/brew" ]; then
                eval "$(/usr/local/bin/brew shellenv)"
            fi
        fi
        
        echo ""
        echo "Installing git-annex..."
        brew install git-annex
        ;;
    2)
        echo ""
        echo "Opening git-annex download page..."
        open "https://downloads.kitenet.net/git-annex/OSX/"
        echo ""
        echo "Please:"
        echo "  1. Download the appropriate DMG file"
        echo "  2. Open it and copy git-annex to /usr/local/bin/"
        echo "  3. Run: chmod +x /usr/local/bin/git-annex"
        echo "  4. Run this script again to verify"
        exit 0
        ;;
    3)
        echo "Exiting. See INSTALL_GIT_ANNEX.md for instructions."
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "Verifying installation..."
if command -v git-annex &> /dev/null; then
    echo "✓ git-annex installed successfully!"
    git-annex version | head -1
    echo ""
    echo "Next step: Run ./retrieve_files.sh to get your data files"
else
    echo "⚠️  Installation may have failed. Check error messages above."
    echo "See INSTALL_GIT_ANNEX.md for troubleshooting."
fi
