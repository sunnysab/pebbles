# 生成图形密码排列

这个程序可以通过深度优先搜索，生成可能的图形密码排列。记左上角的顶点为 1, 条件为：

1. 九个点都用上，每个点仅出现一次
2. 支持斜方向滑动
3. 直线和斜线中不能跳过，比如 123，不能跳过 2，直接连接 1、3
4. 从左上开始
5. 不允许存在 213 这种路径

该问题有两种思路。一是，生成 1~9 的全排列，然后检查是否满足条件。二是，通过深度优先搜索，生成可能的路径。
考虑到效率，这里采用第二种方法。