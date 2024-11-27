mod draw;


struct PatternGraph {
    matrix: [[bool; 10]; 10],
}

impl PatternGraph {
    fn new() -> Self {
        Self {
            matrix: [[false; 10]; 10],
        }
    }

    fn set(&mut self, u: u32, v: u32) {
        self.matrix[u as usize][v as usize] = true;
        self.matrix[v as usize][u as usize] = true;
    }

    fn get(&self, u: u32, v: u32) -> bool {
        self.matrix[u as usize][v as usize]
    }

    fn neighbors(&self, u: u32) -> impl Iterator<Item = u32> + '_ {
        self.matrix[u as usize]
            .iter()
            .enumerate()
            .skip(1)
            .take(9)
            .filter_map(|(i, &b)| if b { Some(i as u32) } else { None })
    }
}

struct Context {
    index: u32, // 结果计数
    results: Vec<[u32; 10]>,

    path: [u32; 10],
    visited: [bool; 10],
    last: u32,
    depth: u32,
}

/// 深度优先搜索
/// 从当前节点开始，遍历所有可能的路径
///
/// 初始调用时，depth = 0, last = 1, path = [], visited = [false; 10]
fn dfs(graph: &PatternGraph, ctx: &mut Context) -> u32 {
    ctx.path[ctx.depth as usize] = ctx.last;
    if ctx.depth == 9 {
        ctx.index += 1;
        println!("{}\t{:?}", ctx.index, &ctx.path[1..]);
        ctx.results.push(ctx.path);
        return 1;
    }
    ctx.depth += 1;
    let mut count = 0;
    for v in graph.neighbors(ctx.last) {
        if ctx.visited[v as usize] {
            continue;
        }
        ctx.visited[v as usize] = true;
        ctx.last = v;
        count += dfs(graph, ctx);
        ctx.visited[v as usize] = false;
    }
    ctx.depth -= 1;
    count
}

fn main() {
    let mut graph = PatternGraph::new();
    graph.set(0, 1);
    graph.set(1, 2);
    graph.set(1, 4);
    graph.set(1, 5);
    graph.set(1, 6);
    graph.set(1, 8);
    graph.set(2, 3);
    graph.set(2, 4);
    graph.set(2, 5);
    graph.set(2, 6);
    graph.set(2, 7);
    graph.set(2, 9);
    graph.set(3, 4);
    graph.set(3, 5);
    graph.set(3, 6);
    graph.set(3, 8);
    graph.set(4, 5);
    graph.set(4, 7);
    graph.set(4, 8);
    graph.set(4, 9);
    graph.set(5, 6);
    graph.set(5, 7);
    graph.set(5, 8);
    graph.set(5, 9);
    graph.set(6, 7);
    graph.set(6, 8);
    graph.set(6, 9);
    graph.set(7, 8);
    graph.set(8, 9);

    let mut ctx = Context {
        index: 0,
        results: Vec::new(),
        path: [0; 10],
        last: 0,
        depth: 0,
        visited: [false; 10],
    };

    let count = dfs(&graph, &mut ctx);
    println!("{} results in total.", count);

    for i in 0..ctx.results.len() {
        draw::export(i as u32, &ctx.results[i]);
    }
}