#!/usr/bin/env bash
set -e
# Download the latest gh release binary directly — no sudo needed.
GH_VERSION=$(curl -s https://api.github.com/repos/cli/cli/releases/latest | grep '"tag_name"' | cut -d'"' -f4 | sed 's/^v//')
ARCH=linux_amd64
URL="https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_${ARCH}.tar.gz"
echo "Downloading gh ${GH_VERSION}..."
mkdir -p ~/bin
cd /tmp
curl -fsSL "$URL" -o gh.tar.gz
tar -xzf gh.tar.gz
cp "gh_${GH_VERSION}_${ARCH}/bin/gh" ~/bin/gh
chmod +x ~/bin/gh
rm -rf gh.tar.gz "gh_${GH_VERSION}_${ARCH}"
export PATH="$HOME/bin:$PATH"
gh --version
echo "Add 'export PATH=\"\$HOME/bin:\$PATH\"' to ~/.bashrc to make it permanent."
