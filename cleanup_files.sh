#!/bin/bash
# VictoryChain File Reduction Script
# Removes redundant files and keeps only essential components

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[CLEANUP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Essential files to keep
ESSENTIAL_FILES=(
    "victorychain_core.py"
    "victorychain_launcher.sh" 
    "victorychain_config.toml"
    "launch_live_trading.py"
    ".env"
    ".env.template"
    "config.toml"
    "README.md"
)

# Create backup directory
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

print_status "Creating backup in $BACKUP_DIR..."

# Backup all files
cp -r . "$BACKUP_DIR/" 2>/dev/null || true

print_status "Identifying redundant files..."

# Count files before cleanup
TOTAL_PY_FILES=$(find . -name "*.py" -not -path "./$BACKUP_DIR/*" | wc -l)
TOTAL_SH_FILES=$(find . -name "*.sh" -not -path "./$BACKUP_DIR/*" | wc -l)

echo "Found $TOTAL_PY_FILES Python files and $TOTAL_SH_FILES shell scripts"

# Function to check if file is essential
is_essential() {
    local file="$1"
    for essential in "${ESSENTIAL_FILES[@]}"; do
        if [[ "$file" == "$essential" ]]; then
            return 0
        fi
    done
    return 1
}

# Remove redundant Python files
print_status "Removing redundant Python files..."
REMOVED_PY=0
for file in *.py; do
    if [[ -f "$file" ]] && ! is_essential "$file"; then
        print_warning "Removing $file"
        rm "$file"
        ((REMOVED_PY++))
    fi
done

# Remove redundant shell scripts
print_status "Removing redundant shell scripts..."
REMOVED_SH=0
for file in *.sh; do
    if [[ -f "$file" ]] && ! is_essential "$file"; then
        print_warning "Removing $file"
        rm "$file"
        ((REMOVED_SH++))
    fi
done

# Remove other redundant files
print_status "Removing redundant analysis files..."
rm -f *.json magicusdt_pattern_analysis_*.json claude_token_analysis_*.json 2>/dev/null || true
rm -f *.log trading_*.log 2>/dev/null || true
rm -f *.md COMPLETE_BINANCE_US_TOKENS_REPORT.md 2>/dev/null || true

# Keep only essential directories
print_status "Cleaning up directories..."
if [[ -d "deploy" ]]; then
    mv deploy/deploy.sh . 2>/dev/null || true
    rm -rf deploy
fi

# Create final summary
echo ""
echo "🎉 CLEANUP COMPLETE!"
echo "==================="
echo "Removed $REMOVED_PY Python files"
echo "Removed $REMOVED_SH shell scripts"
echo "Backup created in: $BACKUP_DIR"
echo ""
echo "Essential files remaining:"
for file in "${ESSENTIAL_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  ✅ $file"
    fi
done

# Make launcher executable
chmod +x victorychain_launcher.sh

echo ""
echo "🚀 Use ./victorychain_launcher.sh to run the system"
