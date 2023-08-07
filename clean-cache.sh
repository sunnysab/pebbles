#! /usr/bin/sh

rm -rf ~/.cache/yay/*
rm -rf ~/.cache/mozilla/*
rm -rf ~/.cache/pip/*
rm -rf ~/.cache/yarn/*
rm -rf ~/go/pkg/mod/cache/download/*
rm -rf ~/.cargo/registry/cache/*
rm -rf ~/.gradle/caches/*

sudo pacman -Scc
