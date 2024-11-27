use std::array::from_fn;
use svg::Document;
use svg::node::element as ele;


pub fn export(pic_index: u32, path: &[u32; 10]) {

    const POINTS: [(u32, u32); 10] = [
        (0, 0),
        (50, 50),
        (100, 50),
        (150, 50),
        (50, 100),
        (100, 100),
        (150, 100),
        (50, 150),
        (100, 150),
        (150, 150),
    ];

    fn _circle(x: u32, y: u32) -> ele::Circle {
        ele::Circle::new()
            .set("cx", x)
            .set("cy", y)
            .set("r", 10)
            .set("fill", "none")
            .set("stroke", "black")
    }

    fn circle(index: u32) -> ele::Circle {
        let (x, y) = POINTS[index as usize];
        _circle(x, y)
    }

    fn _line(x1: u32, y1: u32, x2: u32, y2: u32) -> ele::Line {
        ele::Line::new()
            .set("x1", x1)
            .set("y1", y1)
            .set("x2", x2)
            .set("y2", y2)
            .set("stroke", "black")
    }

    fn line(index1: u32, index2: u32) -> ele::Line {
        let (x1, y1) = POINTS[index1 as usize];
        let (x2, y2) = POINTS[index2 as usize];
        _line(x1, y1, x2, y2)
    }

    let file_path = format!("output/{}.svg", pic_index);
    let mut document = Document::new()
        .set("viewBox", (0, 0, 200, 200));

    for i in 1..=9 {
        document = document.add(circle(i));
    }

    for i in 1..(path.len() - 1) {
        let (from, to) = (path[i], path[i + 1]);
        document = document.add(line(from, to));
    }

    svg::save(file_path, &document).unwrap();
}