#! /usr/bin/sh

rm -rf ~/.cache/yay/*
rm -rf ~/.cache/mozilla/*
rm -rf ~/.cache/pip/*
rm -rf ~/.cache/yarn/*
rm -rf ~/thumbnails/*
rm -rf ~/go/pkg/mod/cache/download/*
rm -rf ~/.cargo/registry/cache/*
rm -rf ~/.gradle/caches/*
rm -rf ~/.npm/_cacache/*
rm -rf ~/.debug/*
rm -rf ~/.rustup/{downloads,tmp}/*
rm -rf ~/.ghcup/{cache,tmp}/*
rm -rf ~/.cache/thumbnails/*

sudo pacman -Scc

# remove rust build crafts.
if [ -e ~/.cargo/bin/cargo-clean-recursive ]; then
    cargo clean-recursive ~/Code/;
else
    echo "please consider to install cargo-clean-recursive."
    fd -g -s "Cargo.toml" ~/Code -x sh -c "cd {//}; cargo clean";
fi
