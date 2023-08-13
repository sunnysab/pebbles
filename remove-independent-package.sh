#!/usr/bin/sh

# https://www.cnblogs.com/hugetong/p/7813073.html
pacman -Rs $(pacman -Qtdq)
